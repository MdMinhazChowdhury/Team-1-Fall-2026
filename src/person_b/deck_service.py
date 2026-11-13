
"""Manage decks and categories using the shared SQLite database."""

import sqlite3

from src.person_b.deck_factory import DeckFactory
from src.person_b.models import Category
from src.person_b.nfr8_auth import NFR8Auth


class DeckService:
    """Provide database-backed operations for a user's decks."""

    def __init__(self, auth_service):
        """Share the database used by the authentication service."""
        self.auth_service = auth_service
        self.database = auth_service.database

        self._decks = {}
        self._categories = {}

    def _require_user(self):
        """Require a logged-in user."""
        user = self.auth_service.get_current_user()

        if user is None:
            raise PermissionError("You must log in first.")

        return user

    def _row_to_deck(self, row):
        """Convert a database row into a Deck object."""
        from src.person_b.models import Deck

        deck = self._decks.get(row["deck_id"])

        if deck is None:
            deck = Deck(
                title=row["title"],
                owner_id=row["owner_id"],
                description=row["description"],
                category_id=row["category_id"],
                deck_id=row["deck_id"],
                created_at=row["created_at"]
            )

            self._decks[deck.deck_id] = deck

        return deck

    def _row_to_category(self, row):
        """Convert a database row into a Category object."""
        category = self._categories.get(row["category_id"])

        if category is None:
            category = Category(
                name=row["name"],
                owner_id=row["owner_id"],
                description=row["description"],
                category_id=row["category_id"]
            )

            self._categories[category.category_id] = category

        # Refresh the category's deck IDs from the database.
        connection = self.database.get_connection()

        try:
            results = connection.execute("""
                SELECT deck_id
                FROM decks
                WHERE category_id = ?
            """, (category.category_id,)).fetchall()

            category.deck_ids = [item["deck_id"] for item in results]

        finally:
            connection.close()

        return category

    def _owned_deck(self, deck_id):
        """Return a deck only if the current user owns it."""
        user = self._require_user()

        connection = self.database.get_connection()

        try:
            row = connection.execute("""
                SELECT *
                FROM decks
                WHERE deck_id = ?
            """, (deck_id,)).fetchone()

        finally:
            connection.close()

        if row is None:
            raise PermissionError("Deck not found or access denied.")

        deck = self._row_to_deck(row)

        # Apply NFR8 ownership authorization.
        NFR8Auth.require_access(deck, user.user_id)

        return deck

    def create_deck(self, title, description="", category_id=None):
        """Create and save a deck for the current user."""
        user = self._require_user()

        if category_id is not None:
            connection = self.database.get_connection()

            try:
                category = connection.execute("""
                    SELECT category_id
                    FROM categories
                    WHERE category_id = ?
                      AND owner_id = ?
                """, (category_id, user.user_id)).fetchone()

            finally:
                connection.close()

            if category is None:
                raise ValueError("Category not found or access denied.")

        deck = DeckFactory.create_deck(
            title=title,
            owner_id=user.user_id,
            description=description,
            category_id=category_id
        )

        connection = self.database.get_connection()

        try:
            connection.execute("""
                INSERT INTO decks (
                    deck_id,
                    title,
                    owner_id,
                    description,
                    category_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                deck.deck_id,
                deck.title,
                deck.owner_id,
                deck.description,
                deck.category_id,
                deck.created_at
            ))

            connection.commit()

        finally:
            connection.close()

        self._decks[deck.deck_id] = deck
        user.add_deck(deck.deck_id)

        if category_id in self._categories:
            self._categories[category_id].add_deck(deck.deck_id)

        return deck

    def create_category(self, name, description=""):
        """Create and save a category for the current user."""
        user = self._require_user()

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Category name cannot be empty.")

        category = Category(
            name=name,
            owner_id=user.user_id,
            description=description
        )

        connection = self.database.get_connection()

        try:
            connection.execute("""
                INSERT INTO categories (
                    category_id,
                    name,
                    owner_id,
                    description
                )
                VALUES (?, ?, ?, ?)
            """, (
                category.category_id,
                category.name,
                category.owner_id,
                category.description
            ))

            connection.commit()

        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise ValueError("Category already exists.") from error

        finally:
            connection.close()

        self._categories[category.category_id] = category

        return category

    def get_deck(self, deck_id):
        """Retrieve a deck owned by the current user."""
        return self._owned_deck(deck_id)

    def list_decks(self, category_id=None):
        """List the user's decks, optionally filtered by category."""
        user = self._require_user()

        connection = self.database.get_connection()

        try:
            if category_id is None:
                results = connection.execute("""
                    SELECT *
                    FROM decks
                    WHERE owner_id = ?
                    ORDER BY created_at
                """, (user.user_id,)).fetchall()

            else:
                results = connection.execute("""
                    SELECT *
                    FROM decks
                    WHERE owner_id = ?
                      AND category_id = ?
                    ORDER BY created_at
                """, (user.user_id, category_id)).fetchall()

        finally:
            connection.close()

        return [self._row_to_deck(row) for row in results]

    def list_categories(self):
        """List categories belonging to the current user."""
        user = self._require_user()

        connection = self.database.get_connection()

        try:
            results = connection.execute("""
                SELECT *
                FROM categories
                WHERE owner_id = ?
                ORDER BY name
            """, (user.user_id,)).fetchall()

        finally:
            connection.close()

        return [self._row_to_category(row) for row in results]

    def rename_deck(self, deck_id, new_title):
        """Rename a deck owned by the current user."""
        deck = self._owned_deck(deck_id)

        # Validate the title using the existing model.
        deck.rename(new_title)

        connection = self.database.get_connection()

        try:
            connection.execute("""
                UPDATE decks
                SET title = ?
                WHERE deck_id = ?
                  AND owner_id = ?
            """, (deck.title, deck_id, deck.owner_id))

            connection.commit()

        finally:
            connection.close()

        return deck

    def assign_category(self, deck_id, category_id):
        """Assign a category to a deck or remove its category."""
        deck = self._owned_deck(deck_id)
        user = self._require_user()

        new_category = None

        if category_id is not None:
            connection = self.database.get_connection()

            try:
                row = connection.execute("""
                    SELECT *
                    FROM categories
                    WHERE category_id = ?
                      AND owner_id = ?
                """, (category_id, user.user_id)).fetchone()

            finally:
                connection.close()

            if row is None:
                raise ValueError("Category not found or access denied.")

            new_category = self._row_to_category(row)

        old_category_id = deck.category_id

        connection = self.database.get_connection()

        try:
            connection.execute("""
                UPDATE decks
                SET category_id = ?
                WHERE deck_id = ?
                  AND owner_id = ?
            """, (category_id, deck_id, user.user_id))

            connection.commit()

        finally:
            connection.close()

        # Update the existing objects to keep them synchronized.
        old_category = self._categories.get(old_category_id)

        if old_category is not None:
            old_category.remove_deck(deck_id)

        deck.category_id = category_id

        if new_category is not None:
            new_category.add_deck(deck_id)

        return deck

    def delete_deck(self, deck_id):
        """Delete a deck owned by the current user."""
        deck = self._owned_deck(deck_id)
        user = self._require_user()

        connection = self.database.get_connection()

        try:
            connection.execute("""
                DELETE FROM decks
                WHERE deck_id = ?
                  AND owner_id = ?
            """, (deck_id, user.user_id))

            connection.commit()

        finally:
            connection.close()

        category = self._categories.get(deck.category_id)

        if category is not None:
            category.remove_deck(deck_id)

        user.remove_deck(deck_id)
        del self._decks[deck_id]

        return True
