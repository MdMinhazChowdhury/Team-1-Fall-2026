
"""Unit tests for deck and category management."""

import pytest

from src.person_b.auth_service import AuthService
from src.person_b.deck_service import DeckService
from src.person_b.deck_factory import DeckFactory


@pytest.fixture
def setup_services():
    """Create two users and a deck service for testing."""
    auth = AuthService()

    auth.register("Alyssa", "alyssa@example.com", "Password123")
    auth.register("Jordan", "jordan@example.com", "Password456")

    service = DeckService(auth)
    return auth, service


def test_create_deck(setup_services):
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    deck = service.create_deck("Biology")

    assert deck.title == "Biology"
    assert deck.owner_id == auth.get_current_user().user_id


def test_login_required(setup_services):
    """A user must log in before creating a deck."""
    auth, service = setup_services

    with pytest.raises(PermissionError):
        service.create_deck("Biology")


def test_create_category(setup_services):
    """A logged-in user can create a category."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    category = service.create_category("Science")

    assert category.name == "Science"


def test_duplicate_category_rejected(setup_services):
    """Duplicate category names are not allowed."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    service.create_category("Science")

    with pytest.raises(ValueError):
        service.create_category("SCIENCE")


def test_filter_decks_by_category(setup_services):
    """A category filter returns only matching decks."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    science = service.create_category("Science")
    history = service.create_category("History")

    biology = service.create_deck(
        "Biology", category_id=science.category_id
    )
    service.create_deck(
        "World History", category_id=history.category_id
    )

    assert service.list_decks(science.category_id) == [biology]


def test_rename_deck(setup_services):
    """The owner can rename a deck."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    deck = service.create_deck("Biology")
    service.rename_deck(deck.deck_id, "Chemistry")

    assert deck.title == "Chemistry"


def test_assign_and_remove_category(setup_services):
    """A deck can be assigned to and removed from a category."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    category = service.create_category("Science")
    deck = service.create_deck("Biology")

    service.assign_category(deck.deck_id, category.category_id)

    assert deck.category_id == category.category_id
    assert deck.deck_id in category.deck_ids

    service.assign_category(deck.deck_id, None)

    assert deck.category_id is None
    assert deck.deck_id not in category.deck_ids


def test_delete_deck(setup_services):
    """Deleting a deck removes it from the user's collection."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    deck = service.create_deck("Biology")

    assert service.delete_deck(deck.deck_id) is True
    assert service.list_decks() == []


def test_other_user_cannot_access_deck(setup_services):
    """A user cannot access another user's deck."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")
    deck = service.create_deck("Private Biology")

    auth.login("Jordan", "Password456")

    with pytest.raises(PermissionError):
        service.get_deck(deck.deck_id)


def test_other_user_cannot_assign_category(setup_services):
    """A user cannot assign another user's category or access another user's deck."""
    auth, service = setup_services

    auth.login("Alyssa", "Password123")
    deck = service.create_deck("Biology")

    auth.login("Jordan", "Password456")
    category = service.create_category("Jordan Science")

    with pytest.raises(PermissionError):
        service.assign_category(deck.deck_id, category.category_id)



def test_factory_creates_deck(setup_services):
    """The deck factory creates a deck for the specified owner."""
    auth, service = setup_services
    auth.login("Alyssa", "Password123")

    deck = DeckFactory.create_deck(
        "Chemistry",
        auth.get_current_user().user_id,
    )

    assert deck.title == "Chemistry"
    assert deck.owner_id == auth.get_current_user().user_id
