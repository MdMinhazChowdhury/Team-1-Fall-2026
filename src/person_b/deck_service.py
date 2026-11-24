
"""Manage decks and categories using the shared SQLite database."""

import sqlite3

from src.person_b.deck_factory import DeckFactory
from src.person_b.models import Category, Deck
from src.person_b.nfr8_auth import NFR8Auth


class DeckService:
    """Manage database-backed decks and categories for individual users.

    Every operation receives current_user_id from the caller.
    Flask routes should get this ID from the user's Flask session.
    """

    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.database = auth_service.database

        # These are caches only. SQLite remains the source of truth.
        self._decks = {}
        self._categories = {}

    def _require_user(self, current_user_id):
        """Verify that the supplied user ID belongs to a registered user."""
        if not current_user_id:
            raise PermissionError("You must log in first.")

        user = self.auth_service.get_user_by_id(current_user_id)

        if user is None:
            raise PermissionError("You must log in first.")

        return user

    def _row_to_deck(self, row):
        """Convert a database row into a Deck object."""
        deck_id = row["deck_id"]
        deck = self._decks.get(deck_id)

        if deck is None:
            deck = Deck(
                title=row["title"],
                owner_id=row["owner_id"],
                description=row["description"],
                category_id=row["category_id"],
                deck_id=deck_id,
                created_at=row["created_at"]
            )
            self._decks[deck_id] = deck
        else:
            deck.title = row["title"]
            deck.owner_id = row["owner_id"]
            deck.description = row["description"]
            deck.category_id = row["category_id"]

        return deck

    def _row_to_category(self, row):
        """Convert a database row into a Category object."""
        category_id = row["category_id"]
        category = self._categories.get(category_id)

        if category is None:
            category = Category(
                name=row["name"],
                owner_id=row["owner_id"],
                description=row["description"],
                category_id=category_id
            )
            self._categories[category_id] = category
        else:
            category.name = row["name"]
            category.owner_id = row["owner_id"]
            category.description = row["description"]

        connection = self.database.get_connection()

        try:
            results = connection.execute(
                """
                SELECT deck_id
                FROM decks
                WHERE category_id = ?
                  AND owner_id = ?
                """,
                (category_id, category.owner_id)
            ).fetchall()

            category.deck_ids = [
                item["deck_id"] for item in results
            ]

        finally:
            connection.close()

        return category

    def _owned_deck(self, deck_id, current_user_id):
        """Return a deck only when the supplied user owns it."""
        user = self._require_user(current_user_id)

        connection = self.database.get_connection()

        try:
            row = connection.execute(
                """
                SELECT *
                FROM decks
                WHERE deck_id = ?
                  AND owner_id = ?
                """,
                (deck_id, user.user_id)
            ).fetchone()

        finally:
            connection.close()

        if row is None:
            raise PermissionError("Deck not found or access denied.")

        deck = self._row_to_deck(row)

        NFR8Auth.require_access(deck, user.user_id)

        return deck

    def create_deck(
        self,
        title,
        current_user_id,
        description="",
        category_id=None
    ):
        """Create and save a deck for the supplied user."""
        user = self._require_user(current_user_id)

        if category_id is not None:
            connection = self.database.get_connection()

            try:
                category = connection.execute(
                    """
                    SELECT category_id
                    FROM categories
                    WHERE category_id = ?
                      AND owner_id = ?
                    """,
                    (category_id, user.user_id)
                ).fetchone()

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
            connection.execute(
                """
                INSERT INTO decks (
                    deck_id,
                    title,
                    owner_id,
                    description,
                    category_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    deck.deck_id,
                    deck.title,
                    deck.owner_id,
                    deck.description,
                    deck.category_id,
                    deck.created_at
                )
            )
            connection.commit()

        finally:
            connection.close()

        self._decks[deck.deck_id] = deck
        user.add_deck(deck.deck_id)

        if category_id in self._categories:
            self._categories[category_id].add_deck(deck.deck_id)

        return deck

    def create_category(
        self,
        name,
        current_user_id,
        description=""
    ):
        """Create and save a category for the supplied user."""
        user = self._require_user(current_user_id)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Category name cannot be empty.")

        # Check duplicates for this user, ignoring capitalization.
        connection = self.database.get_connection()

        try:
            existing = connection.execute(
                """
                SELECT category_id
                FROM categories
                WHERE owner_id = ?
                  AND LOWER(name) = LOWER(?)
                """,
                (user.user_id, name.strip())
            ).fetchone()

            if existing is not None:
                raise ValueError("Category already exists.")

            category = Category(
                name=name,
                owner_id=user.user_id,
                description=description
            )

            connection.execute(
                """
                INSERT INTO categories (
                    category_id,
                    name,
                    owner_id,
                    description
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    category.category_id,
                    category.name,
                    category.owner_id,
                    category.description
                )
            )

            connection.commit()

        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise ValueError("Category already exists.") from error

        finally:
            connection.close()

        self._categories[category.category_id] = category

        return category

    def get_deck(self, deck_id, current_user_id):
        """Retrieve a deck owned by the supplied user."""
        return self._owned_deck(deck_id, current_user_id)

    def list_decks(self, current_user_id, category_id=None):
        """List the user's decks, optionally filtered by category."""
        user = self._require_user(current_user_id)

        connection = self.database.get_connection()

        try:
            if category_id is None:
                results = connection.execute(
                    """
                    SELECT *
                    FROM decks
                    WHERE owner_id = ?
                    ORDER BY created_at
                    """,
                    (user.user_id,)
                ).fetchall()
            else:
                # Verify that the category belongs to this user.
                category = connection.execute(
                    """
                    SELECT category_id
                    FROM categories
                    WHERE category_id = ?
                      AND owner_id = ?
                    """,
                    (category_id, user.user_id)
                ).fetchone()

                if category is None:
                    raise ValueError("Category not found or access denied.")

                results = connection.execute(
                    """
                    SELECT *
                    FROM decks
                    WHERE owner_id = ?
                      AND category_id = ?
                    ORDER BY created_at
                    """,
                    (user.user_id, category_id)
                ).fetchall()

        finally:
            connection.close()

        return [self._row_to_deck(row) for row in results]

    def list_categories(self, current_user_id):
        """List categories belonging to the supplied user."""
        user = self._require_user(current_user_id)

        connection = self.database.get_connection()

        try:
            results = connection.execute(
                """
                SELECT *
                FROM categories
                WHERE owner_id = ?
                ORDER BY name
                """,
                (user.user_id,)
            ).fetchall()

        finally:
            connection.close()

        return [
            self._row_to_category(row)
            for row in results
        ]

    def rename_deck(self, deck_id, new_title, current_user_id):
        """Rename a deck owned by the supplied user."""
        deck = self._owned_deck(deck_id, current_user_id)

        # Validate the new title before changing the database.
        if not isinstance(new_title, str) or not new_title.strip():
            raise ValueError("Deck title cannot be empty.")

        new_title = new_title.strip()

        connection = self.database.get_connection()

        try:
            cursor = connection.execute(
                """
                UPDATE decks
                SET title = ?
                WHERE deck_id = ?
                  AND owner_id = ?
                """,
                (new_title, deck_id, current_user_id)
            )
            connection.commit()

            if cursor.rowcount != 1:
                raise PermissionError("Deck not found or access denied.")

        finally:
            connection.close()

        deck.title = new_title

        return deck

    def assign_category(
        self,
        deck_id,
        category_id,
        current_user_id
    ):
        """Assign a category to a deck or remove its category."""
        user = self._require_user(current_user_id)
        deck = self._owned_deck(deck_id, user.user_id)

        new_category = None

        if category_id is not None:
            connection = self.database.get_connection()

            try:
                row = connection.execute(
                    """
                    SELECT *
                    FROM categories
                    WHERE category_id = ?
                      AND owner_id = ?
                    """,
                    (category_id, user.user_id)
                ).fetchone()

            finally:
                connection.close()

            if row is None:
                raise ValueError("Category not found or access denied.")

            new_category = self._row_to_category(row)

        old_category_id = deck.category_id

        connection = self.database.get_connection()

        try:
            cursor = connection.execute(
                """
                UPDATE decks
                SET category_id = ?
                WHERE deck_id = ?
                  AND owner_id = ?
                """,
                (category_id, deck_id, user.user_id)
            )
            connection.commit()

            if cursor.rowcount != 1:
                raise PermissionError("Deck not found or access denied.")

        finally:
            connection.close()

        old_category = self._categories.get(old_category_id)

        if old_category is not None:
            old_category.remove_deck(deck_id)

        deck.category_id = category_id

        if new_category is not None:
            new_category.add_deck(deck_id)

        return deck

    def delete_deck(self, deck_id, current_user_id):
        """Delete a deck owned by the supplied user."""
        user = self._require_user(current_user_id)
        deck = self._owned_deck(deck_id, user.user_id)

        connection = self.database.get_connection()

        try:
            cursor = connection.execute(
                """
                DELETE FROM decks
                WHERE deck_id = ?
                  AND owner_id = ?
                """,
                (deck_id, user.user_id)
            )
            connection.commit()

            if cursor.rowcount != 1:
                raise PermissionError("Deck not found or access denied.")

        finally:
            connection.close()

        category = self._categories.get(deck.category_id)

        if category is not None:
            category.remove_deck(deck_id)

        user.remove_deck(deck_id)
        self._decks.pop(deck_id, None)

        return True
