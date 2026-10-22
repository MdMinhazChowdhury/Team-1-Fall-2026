
"""Factory for creating flashcard decks."""

from src.person_b.models import Deck


class DeckFactory:
    """Create Deck objects consistently."""

    @staticmethod
    def create_deck(title, owner_id, description="", category_id=None):
        """Create and return a validated deck."""
        return Deck(
            title=title,
            owner_id=owner_id,
            description=description,
            category_id=category_id,
        )
