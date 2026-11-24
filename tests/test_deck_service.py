"""Unit tests for deck and category management."""

import pytest

from src.database import Database
from src.person_b.auth_service import AuthService
from src.person_b.deck_service import DeckService
from src.person_b.deck_factory import DeckFactory


@pytest.fixture
def setup_services(tmp_path):
    """Create two users and a deck service for testing."""
    database = Database(tmp_path / "test_decks.db")
    auth = AuthService(database)

    alyssa = auth.register(
        "Alyssa",
        "alyssa@example.com",
        "Password123"
    )
    jordan = auth.register(
        "Jordan",
        "jordan@example.com",
        "Password456"
    )

    service = DeckService(auth)

    return auth, service, alyssa, jordan


def test_create_deck(setup_services):
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )

    assert deck.title == "Biology"
    assert deck.owner_id == alyssa.user_id


def test_login_required(setup_services):
    """A missing user ID must not be allowed to create a deck."""
    auth, service, alyssa, jordan = setup_services

    with pytest.raises(PermissionError):
        service.create_deck("Biology", current_user_id=None)


def test_create_category(setup_services):
    auth, service, alyssa, jordan = setup_services

    category = service.create_category(
        "Science",
        current_user_id=alyssa.user_id
    )

    assert category.name == "Science"
    assert category.owner_id == alyssa.user_id


def test_duplicate_category_rejected(setup_services):
    auth, service, alyssa, jordan = setup_services

    service.create_category("Science", current_user_id=alyssa.user_id)

    with pytest.raises(ValueError):
        service.create_category(
            "SCIENCE",
            current_user_id=alyssa.user_id
        )


def test_filter_decks_by_category(setup_services):
    auth, service, alyssa, jordan = setup_services

    science = service.create_category(
        "Science",
        current_user_id=alyssa.user_id
    )
    history = service.create_category(
        "History",
        current_user_id=alyssa.user_id
    )

    biology = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id,
        category_id=science.category_id
    )
    service.create_deck(
        "World History",
        current_user_id=alyssa.user_id,
        category_id=history.category_id
    )

    assert service.list_decks(
        current_user_id=alyssa.user_id,
        category_id=science.category_id
    ) == [biology]


def test_rename_deck(setup_services):
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )
    service.rename_deck(
        deck.deck_id,
        "Chemistry",
        current_user_id=alyssa.user_id
    )

    assert deck.title == "Chemistry"


def test_assign_and_remove_category(setup_services):
    auth, service, alyssa, jordan = setup_services

    category = service.create_category(
        "Science",
        current_user_id=alyssa.user_id
    )
    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )

    service.assign_category(
        deck.deck_id,
        category.category_id,
        current_user_id=alyssa.user_id
    )

    assert deck.category_id == category.category_id
    assert deck.deck_id in category.deck_ids

    service.assign_category(
        deck.deck_id,
        None,
        current_user_id=alyssa.user_id
    )

    assert deck.category_id is None
    assert deck.deck_id not in category.deck_ids


def test_delete_deck(setup_services):
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )

    assert service.delete_deck(
        deck.deck_id,
        current_user_id=alyssa.user_id
    ) is True

    assert service.list_decks(current_user_id=alyssa.user_id) == []


def test_other_user_cannot_access_deck(setup_services):
    """A user cannot access another user's deck."""
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Private Biology",
        current_user_id=alyssa.user_id
    )

    with pytest.raises(PermissionError):
        service.get_deck(
            deck.deck_id,
            current_user_id=jordan.user_id
        )


def test_other_user_cannot_rename_or_delete_deck(setup_services):
    """A different user cannot change or delete a private deck."""
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Private Biology",
        current_user_id=alyssa.user_id
    )

    with pytest.raises(PermissionError):
        service.rename_deck(
            deck.deck_id,
            "Changed",
            current_user_id=jordan.user_id
        )

    with pytest.raises(PermissionError):
        service.delete_deck(
            deck.deck_id,
            current_user_id=jordan.user_id
        )


def test_other_user_cannot_assign_category(setup_services):
    """A user cannot assign their category to another user's deck."""
    auth, service, alyssa, jordan = setup_services

    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )

    category = service.create_category(
        "Jordan Science",
        current_user_id=jordan.user_id
    )

    with pytest.raises(PermissionError):
        service.assign_category(
            deck.deck_id,
            category.category_id,
            current_user_id=jordan.user_id
        )


def test_factory_creates_deck(setup_services):
    """The factory creates a deck for the supplied owner."""
    auth, service, alyssa, jordan = setup_services

    deck = DeckFactory.create_deck(
        "Chemistry",
        alyssa.user_id
    )

    assert deck.title == "Chemistry"
    assert deck.owner_id == alyssa.user_id


def test_deck_persists_after_creating_new_deck_service(setup_services):
    """A deck remains available after creating a new DeckService."""
    auth, service, alyssa, jordan = setup_services

    original_deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id
    )

    new_service = DeckService(auth)

    saved_deck = new_service.get_deck(
        original_deck.deck_id,
        current_user_id=alyssa.user_id
    )

    assert saved_deck is not None
    assert saved_deck.title == "Biology"
    assert saved_deck.owner_id == original_deck.owner_id


def test_category_and_deck_assignment_persist(setup_services):
    """Categories and deck assignments remain in SQLite."""
    auth, service, alyssa, jordan = setup_services

    category = service.create_category(
        "Science",
        current_user_id=alyssa.user_id
    )

    deck = service.create_deck(
        "Biology",
        current_user_id=alyssa.user_id,
        category_id=category.category_id
    )

    new_service = DeckService(auth)

    saved_categories = new_service.list_categories(
        current_user_id=alyssa.user_id
    )
    saved_decks = new_service.list_decks(
        current_user_id=alyssa.user_id
    )

    assert len(saved_categories) == 1
    assert saved_categories[0].name == "Science"

    assert len(saved_decks) == 1
    assert saved_decks[0].title == "Biology"
    assert saved_decks[0].category_id == category.category_id

    assert deck.deck_id in saved_categories[0].deck_ids


def test_users_only_see_their_own_decks(setup_services):
    """Each user receives only their own decks."""
    auth, service, alyssa, jordan = setup_services

    alyssa_deck = service.create_deck(
        "Alyssa's Deck",
        current_user_id=alyssa.user_id
    )
    jordan_deck = service.create_deck(
        "Jordan's Deck",
        current_user_id=jordan.user_id
    )

    alyssa_decks = service.list_decks(current_user_id=alyssa.user_id)
    jordan_decks = service.list_decks(current_user_id=jordan.user_id)

    assert [deck.deck_id for deck in alyssa_decks] == [alyssa_deck.deck_id]
    assert [deck.deck_id for deck in jordan_decks] == [jordan_deck.deck_id]