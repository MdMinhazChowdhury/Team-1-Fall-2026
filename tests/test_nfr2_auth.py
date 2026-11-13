
"""Tests for NFR2 authentication requirements."""

import pytest

from src.person_b.nfr2_auth import NFR2Auth


@pytest.fixture
def auth():
    """Create a fresh authentication service."""
    return NFR2Auth()


def test_register_user_successfully(auth):
    user = auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    assert user.username == "alyssa"
    assert user.email == "alyssa@example.com"
    assert auth.user_count == 1


def test_password_is_hashed(auth):
    user = auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    assert user.password_hash != "password123"
    assert auth._verify_password(
        "password123",
        user.password_hash
    )


def test_password_must_be_at_least_eight_characters(auth):
    with pytest.raises(ValueError):
        auth.register(
            "alyssa",
            "alyssa@example.com",
            "short"
        )


def test_eight_character_password_is_accepted(auth):
    user = auth.register(
        "alyssa",
        "alyssa@example.com",
        "12345678"
    )

    assert user.username == "alyssa"


def test_login_with_username(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    user = auth.login("alyssa", "password123")

    assert user is not None
    assert user.username == "alyssa"


def test_login_with_email(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    user = auth.login("alyssa@example.com", "password123")

    assert user is not None
    assert user.email == "alyssa@example.com"


def test_wrong_password_is_rejected(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    assert auth.login("alyssa", "wrongpassword") is None


def test_unknown_username_is_rejected(auth):
    assert auth.login("unknown", "password123") is None


def test_duplicate_username_is_rejected(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    with pytest.raises(ValueError):
        auth.register(
            "alyssa",
            "another@example.com",
            "password456"
        )


def test_duplicate_email_is_rejected(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    with pytest.raises(ValueError):
        auth.register(
            "anotheruser",
            "alyssa@example.com",
            "password456"
        )


def test_logout(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    auth.login("alyssa", "password123")

    assert auth.get_current_user() is not None

    auth.logout()

    assert auth.get_current_user() is None


def test_login_is_case_insensitive(auth):
    auth.register(
        "Alyssa",
        "Alyssa@example.com",
        "password123"
    )

    user = auth.login("ALYSSA", "password123")

    assert user is not None
    assert user.username == "Alyssa"


def test_failed_login_does_not_create_session(auth):
    auth.register(
        "alyssa",
        "alyssa@example.com",
        "password123"
    )

    assert auth.login("alyssa", "wrongpassword") is None
    assert auth.get_current_user() is None
