
"""Unit tests for the application data models."""

import pytest

from src.person_b.models import User, Deck, Category


def test_user_normalizes_email():
    """Emails should be stored in lowercase."""
    user = User("Alyssa", "ALYSSA@example.com", "sample_hash")
    assert user.email == "alyssa@example.com"


def test_user_rejects_empty_username():
    """A username cannot be blank."""
    with pytest.raises(ValueError):
        User(" ", "alyssa@example.com", "sample_hash")


def test_user_rejects_invalid_email():
    """An email must contain an @ symbol."""
    with pytest.raises(ValueError):
        User("Alyssa", "invalid-email", "sample_hash")


def test_user_adds_and_removes_deck():
    """Users can track their deck IDs without duplicates."""
    user = User("Alyssa", "alyssa@example.com", "sample_hash")

    user.add_deck("deck-1")
    user.add_deck("deck-1")

    assert user.deck_ids == ["deck-1"]

    user.remove_deck("deck-1")
    assert user.deck_ids == []


def test_deck_can_be_renamed():
    """A deck can be given a new title."""
    deck = Deck("Biology", "user-1")
    deck.rename("Chemistry")

    assert deck.title == "Chemistry"


def test_deck_rejects_empty_title():
    """A deck cannot have a blank title."""
    with pytest.raises(ValueError):
        Deck(" ", "user-1")


def test_deck_rejects_empty_owner():
    """A deck must have an owner."""
    with pytest.raises(ValueError):
        Deck("Biology", "")


def test_deck_adds_and_removes_cards():
    """A deck tracks card IDs without duplicates."""
    deck = Deck("Biology", "user-1")

    deck.add_card_id("card-1")
    deck.add_card_id("card-1")

    assert deck.card_ids == ["card-1"]

    deck.remove_card_id("card-1")
    assert deck.card_ids == []


def test_category_rejects_empty_name():
    """A category must have a name."""
    with pytest.raises(ValueError):
        Category("", "user-1")


def test_category_tracks_decks():
    """A category can add and remove deck IDs."""
    category = Category("Science", "user-1")

    category.add_deck("deck-1")
    assert category.deck_ids == ["deck-1"]

    category.remove_deck("deck-1")
    assert category.deck_ids == []
