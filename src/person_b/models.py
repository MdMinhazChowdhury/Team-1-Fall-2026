
"""Data models for users, decks, and categories."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


def new_id():
    """Generate a unique ID."""
    return str(uuid4())


def current_time():
    """Return the current UTC time."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class User:
    """Represent a registered application user."""

    username: str
    email: str
    password_hash: str
    user_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=current_time)
    deck_ids: list = field(default_factory=list)

    def __post_init__(self):
        """Normalize and validate user information."""
        self.username = self.username.strip()
        self.email = self.email.strip().lower()

        if not self.username:
            raise ValueError("Username cannot be empty.")
        if "@" not in self.email:
            raise ValueError("A valid email address is required.")
        if not self.password_hash:
            raise ValueError("Password hash cannot be empty.")

    def add_deck(self, deck_id):
        """Add a deck ID without creating duplicates."""
        if deck_id not in self.deck_ids:
            self.deck_ids.append(deck_id)

    def remove_deck(self, deck_id):
        """Remove a deck ID if it exists."""
        if deck_id in self.deck_ids:
            self.deck_ids.remove(deck_id)


@dataclass
class Category:
    """Group related flashcard decks."""

    name: str
    owner_id: str
    description: str = ""
    category_id: str = field(default_factory=new_id)
    deck_ids: list = field(default_factory=list)

    def __post_init__(self):
        """Validate the category."""
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Category name cannot be empty.")
        if not self.owner_id:
            raise ValueError("Category must have an owner.")

    def add_deck(self, deck_id):
        """Add a deck to the category."""
        if deck_id not in self.deck_ids:
            self.deck_ids.append(deck_id)

    def remove_deck(self, deck_id):
        """Remove a deck from the category."""
        if deck_id in self.deck_ids:
            self.deck_ids.remove(deck_id)


@dataclass
class Deck:
    """Represent a collection of flashcards."""

    title: str
    owner_id: str
    description: str = ""
    category_id: Optional[str] = None
    deck_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=current_time)
    card_ids: list = field(default_factory=list)

    def __post_init__(self):
        """Validate required deck information."""
        self.title = self.title.strip()

        if not self.title:
            raise ValueError("Deck title cannot be empty.")
        if not self.owner_id:
            raise ValueError("Deck must have an owner.")

    def rename(self, new_title):
        """Rename the deck."""
        if not isinstance(new_title, str) or not new_title.strip():
            raise ValueError("Deck title cannot be empty.")

        self.title = new_title.strip()

    def add_card_id(self, card_id):
        """Add a flashcard ID without duplicates."""
        if card_id not in self.card_ids:
            self.card_ids.append(card_id)

    def remove_card_id(self, card_id):
        """Remove a flashcard ID if it exists."""
        if card_id in self.card_ids:
            self.card_ids.remove(card_id)
