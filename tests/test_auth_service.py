
"""Unit tests for account registration and authentication."""

import pytest

from src.person_b.auth_service import AuthService


@pytest.fixture
def auth():
    """Create a fresh service for each test."""
    return AuthService()


def test_register_user(auth):
    """A valid registration creates a user."""
    user = auth.register(
        "Alyssa", "alyssa@example.com", "Password123"
    )

    assert user.username == "Alyssa"
    assert user.email == "alyssa@example.com"
    assert auth.user_count == 1


def test_password_is_hashed(auth):
    """The plain-text password must not be stored."""
    user = auth.register(
        "Alyssa", "alyssa@example.com", "Password123"
    )

    assert user.password_hash != "Password123"
    assert "$" in user.password_hash


def test_login_with_username(auth):
    """A user can log in using their username."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    user = auth.login("Alyssa", "Password123")

    assert user is not None
    assert auth.get_current_user() is user


def test_login_with_email(auth):
    """A user can log in using their email."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    user = auth.login("ALYSSA@example.com", "Password123")

    assert user is not None


def test_short_password_is_rejected(auth):
    """Passwords must have at least eight characters."""
    with pytest.raises(ValueError):
        auth.register("Alyssa", "alyssa@example.com", "short")


def test_invalid_email_is_rejected(auth):
    """Registration rejects an invalid email."""
    with pytest.raises(ValueError):
        auth.register("Alyssa", "invalid-email", "Password123")


def test_duplicate_username_is_rejected(auth):
    """Usernames cannot be registered twice."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    with pytest.raises(ValueError):
        auth.register("Alyssa", "other@example.com", "Password456")


def test_duplicate_email_is_rejected(auth):
    """Emails cannot be registered twice."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    with pytest.raises(ValueError):
        auth.register("OtherUser", "ALYSSA@example.com", "Password456")


def test_wrong_password_fails(auth):
    """An incorrect password does not log the user in."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    assert auth.login("Alyssa", "WrongPassword") is None
    assert auth.get_current_user() is None


def test_logout(auth):
    """Logout clears the current user."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")
    auth.login("Alyssa", "Password123")

    auth.logout()

    assert auth.get_current_user() is None


def test_username_is_case_insensitive(auth):
    """Username capitalization does not affect login."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    assert auth.login("ALYSSA", "Password123") is not None
