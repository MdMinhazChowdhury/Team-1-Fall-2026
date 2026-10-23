
"""Manage decks and categories for logged-in users."""

from src.person_b.deck_factory import DeckFactory
from src.person_b.models import Category


class DeckService:
    """Provide operations for managing a user's decks."""

    def __init__(self, auth_service):
        # Reuse authentication to identify the current user.
        self.auth_service = auth_service

        # Temporary in-memory storage for the initial version.
        self._decks = {}
        self._categories = {}

    def _require_user(self):
        """Require a logged-in user."""
        user = self.auth_service.get_current_user()

        if user is None:
            raise PermissionError("You must log in first.")

        return user

    def _owned_deck(self, deck_id):
        """Return a deck only if the current user owns it."""
        user = self._require_user()
        deck = self._decks.get(deck_id)

        if deck is None or deck.owner_id != user.user_id:
            raise PermissionError("Deck not found or access denied.")

        return deck

    def create_deck(self, title, description="", category_id=None):
        """Create a deck for the current user."""
        user = self._require_user()

        if category_id is not None:
            category = self._categories.get(category_id)

            if category is None or category.owner_id != user.user_id:
                raise ValueError("Category not found or access denied.")

        deck = DeckFactory.create_deck(
            title=title,
            owner_id=user.user_id,
            description=description,
            category_id=category_id,
        )

        self._decks[deck.deck_id] = deck
        user.add_deck(deck.deck_id)

        if category_id is not None:
            self._categories[category_id].add_deck(deck.deck_id)

        return deck

    def create_category(self, name, description=""):
        """Create a category for the current user."""
        user = self._require_user()

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Category name cannot be empty.")

        category_key = name.strip().casefold()

        for category in self._categories.values():
            if (
                category.owner_id == user.user_id
                and category.name.casefold() == category_key
            ):
                raise ValueError("Category already exists.")

        category = Category(
            name=name,
            owner_id=user.user_id,
            description=description,
        )

        self._categories[category.category_id] = category
        return category

    def get_deck(self, deck_id):
        """Retrieve a deck owned by the current user."""
        return self._owned_deck(deck_id)

    def list_decks(self, category_id=None):
        """List the user's decks, optionally filtering by category."""
        user = self._require_user()

        return [
            deck
            for deck in self._decks.values()
            if deck.owner_id == user.user_id
            and (
                category_id is None
                or deck.category_id == category_id
            )
        ]

    def list_categories(self):
        """List categories belonging to the current user."""
        user = self._require_user()

        return [
            category
            for category in self._categories.values()
            if category.owner_id == user.user_id
        ]

    def rename_deck(self, deck_id, new_title):
        """Rename a deck owned by the current user."""
        deck = self._owned_deck(deck_id)
        deck.rename(new_title)
        return deck

    def assign_category(self, deck_id, category_id):
        """Assign a category, or remove the current category."""
        deck = self._owned_deck(deck_id)
        user = self._require_user()
        new_category = None

        if category_id is not None:
            new_category = self._categories.get(category_id)

            if (
                new_category is None
                or new_category.owner_id != user.user_id
            ):
                raise ValueError("Category not found or access denied.")

        # Remove the deck from its previous category.
        old_category = self._categories.get(deck.category_id)

        if old_category is not None:
            old_category.remove_deck(deck.deck_id)

        deck.category_id = category_id

        if new_category is not None:
            new_category.add_deck(deck.deck_id)

        return deck

    def delete_deck(self, deck_id):
        """Delete a deck and remove associated references."""
        deck = self._owned_deck(deck_id)
        user = self._require_user()

        category = self._categories.get(deck.category_id)

        if category is not None:
            category.remove_deck(deck.deck_id)

        user.remove_deck(deck.deck_id)
        del self._decks[deck_id]

        return True
