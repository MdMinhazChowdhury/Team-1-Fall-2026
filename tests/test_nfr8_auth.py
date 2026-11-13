
"""Tests for NFR8 private deck authorization."""

import pytest

from src.person_b.models import User, Deck
from src.person_b.nfr8_auth import NFR8Auth


@pytest.fixture
def users():
    user1 = User(
        username="alyssa",
        email="alyssa@example.com",
        password_hash="test_hash_1"
    )

    user2 = User(
        username="otheruser",
        email="other@example.com",
        password_hash="test_hash_2"
    )

    return user1, user2


@pytest.fixture
def private_deck(users):
    user1, _ = users

    return Deck(
        title="Private Study Deck",
        owner_id=user1.user_id,
        description="A private flashcard deck."
    )


def test_owner_can_access_private_deck(users, private_deck):
    user1, _ = users
    assert NFR8Auth.can_access(private_deck, user1.user_id)


def test_other_user_cannot_access_private_deck(users, private_deck):
    _, user2 = users
    assert not NFR8Auth.can_access(private_deck, user2.user_id)


def test_unauthenticated_user_cannot_access_deck(private_deck):
    assert not NFR8Auth.can_access(private_deck, None)


def test_missing_deck_cannot_be_accessed(users):
    user1, _ = users
    assert not NFR8Auth.can_access(None, user1.user_id)


def test_owner_passes_access_check(users, private_deck):
    user1, _ = users
    assert NFR8Auth.require_access(private_deck, user1.user_id)


def test_other_user_is_denied_access(users, private_deck):
    _, user2 = users

    with pytest.raises(PermissionError):
        NFR8Auth.require_access(private_deck, user2.user_id)


def test_unauthenticated_user_is_denied_access(private_deck):
    with pytest.raises(PermissionError):
        NFR8Auth.require_access(private_deck, None)


def test_other_user_cannot_edit_deck(users, private_deck):
    _, user2 = users

    with pytest.raises(PermissionError):
        NFR8Auth.require_edit_access(private_deck, user2.user_id)


def test_other_user_cannot_delete_deck(users, private_deck):
    _, user2 = users

    with pytest.raises(PermissionError):
        NFR8Auth.require_delete_access(private_deck, user2.user_id)


def test_other_user_cannot_access_deck_cards(users, private_deck):
    _, user2 = users

    with pytest.raises(PermissionError):
        NFR8Auth.require_card_access(private_deck, user2.user_id)


def test_owner_can_edit_delete_and_access_cards(users, private_deck):
    user1, _ = users

    assert NFR8Auth.require_edit_access(private_deck, user1.user_id)
    assert NFR8Auth.require_delete_access(private_deck, user1.user_id)
    assert NFR8Auth.require_card_access(private_deck, user1.user_id)
