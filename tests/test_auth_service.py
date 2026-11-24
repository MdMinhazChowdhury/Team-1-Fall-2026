"""Unit tests for account registration and authentication."""

import pytest

from src.database import Database
from src.person_b.auth_service import AuthService


@pytest.fixture
def auth(tmp_path):
    """Create a fresh database and service for each test."""
    database = Database(tmp_path / "test_auth.db")
    return AuthService(database)


def test_register_user(auth):
    """A valid registration creates a user."""
    user = auth.register(
        "Alyssa",
        "alyssa@example.com",
        "Password123"
    )

    assert user.username == "Alyssa"
    assert user.email == "alyssa@example.com"
    assert auth.user_count == 1


def test_password_is_hashed(auth):
    """The plain-text password must not be stored."""
    user = auth.register(
        "Alyssa",
        "alyssa@example.com",
        "Password123"
    )

    assert user.password_hash != "Password123"
    assert "$" in user.password_hash


def test_login_with_username(auth):
    """A user can log in using their username."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    user = auth.login("Alyssa", "Password123")

    assert user is not None
    assert user.username == "Alyssa"


def test_login_with_email(auth):
    """A user can log in using their email."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    user = auth.login("ALYSSA@example.com", "Password123")

    assert user is not None
    assert user.username == "Alyssa"


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
    """An incorrect password does not authenticate the user."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    assert auth.login("Alyssa", "WrongPassword") is None


def test_unknown_username_fails(auth):
    """An unknown username or email does not authenticate."""
    assert auth.login("unknown", "Password123") is None


def test_username_is_case_insensitive(auth):
    """Username capitalization does not affect login."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")

    assert auth.login("ALYSSA", "Password123") is not None


def test_login_does_not_store_current_user_on_service(auth):
    """The shared service does not store one current user's identity."""
    auth.register("Alyssa", "alyssa@example.com", "Password123")
    auth.register("Jordan", "jordan@example.com", "Password456")

    alyssa = auth.login("Alyssa", "Password123")
    jordan = auth.login("Jordan", "Password456")

    assert alyssa is not None
    assert jordan is not None

    # Both logins return their own user; neither sets shared login state.
    assert alyssa.user_id != jordan.user_id
    assert not hasattr(auth, "_current_user_id")
    assert not hasattr(auth, "get_current_user")


def test_user_persists_after_creating_new_auth_service(tmp_path):
    """A registered user remains available to a new service."""
    database_path = tmp_path / "persistent_auth.db"

    first_auth = AuthService(Database(database_path))
    original_user = first_auth.register(
        "Alyssa",
        "alyssa@example.com",
        "Password123"
    )

    second_auth = AuthService(Database(database_path))
    logged_in_user = second_auth.login(
        "Alyssa",
        "Password123"
    )

    assert logged_in_user is not None
    assert logged_in_user.user_id == original_user.user_id


def test_user_count_persists_after_new_auth_service(tmp_path):
    """The database retains registered users between services."""
    database_path = tmp_path / "persistent_count.db"

    first_auth = AuthService(Database(database_path))
    first_auth.register("Alyssa", "alyssa@example.com", "Password123")
    first_auth.register("Jordan", "jordan@example.com", "Password456")

    second_auth = AuthService(Database(database_path))

    assert second_auth.user_count == 2