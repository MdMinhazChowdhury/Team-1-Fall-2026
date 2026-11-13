
"""Manage user registration and authentication using SQLite."""

import hashlib
import hmac
import os
import sqlite3

from src.database import Database
from src.person_b.models import User


class AuthService:
    """Register users and manage login sessions using a database."""

    def __init__(self, database=None):
        """Use the shared database or an explicitly supplied database."""
        self.database = database if database is not None else Database()
        self.database.initialize_database()

        self._users = {}
        self._current_user_id = None

    @staticmethod
    def _normalize(value):
        return value.strip().casefold()

    @staticmethod
    def _hash_password(password, salt=None):
        """Create a salted PBKDF2 password hash."""
        if salt is None:
            salt = os.urandom(16)

        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            240000
        )

        return salt.hex() + "$" + hashed.hex()

    @classmethod
    def _verify_password(cls, password, stored_hash):
        """Check a password against its stored hash."""
        if not isinstance(password, str):
            return False

        try:
            salt_hex, expected_hash = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
        except (ValueError, TypeError, AttributeError):
            return False

        actual_hash = cls._hash_password(password, salt)

        return hmac.compare_digest(
            actual_hash.split("$", 1)[1],
            expected_hash
        )

    @staticmethod
    def _row_to_user(row):
        """Convert a database row into a User object."""
        return User(
            user_id=row["user_id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"]
        )

    def register(self, username, email, password):
        """Register a new user and save the account in SQLite."""
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Username is required.")

        if not isinstance(email, str) or "@" not in email:
            raise ValueError("A valid email is required.")

        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        username = username.strip()
        email = email.strip()

        password_hash = self._hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )

        connection = self.database.get_connection()

        try:
            connection.execute("""
                INSERT INTO users (
                    user_id,
                    username,
                    email,
                    password_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.username,
                user.email,
                user.password_hash,
                user.created_at
            ))

            connection.commit()

        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise ValueError(
                "Username or email already exists."
            ) from error

        finally:
            connection.close()

        self._users[user.user_id] = user

        return user

    def login(self, username_or_email, password):
        """Log in using either a username or email address."""
        if not isinstance(username_or_email, str):
            return None

        if not isinstance(password, str):
            return None

        key = self._normalize(username_or_email)

        connection = self.database.get_connection()

        try:
            row = connection.execute("""
                SELECT *
                FROM users
                WHERE username = ? COLLATE NOCASE
                   OR email = ? COLLATE NOCASE
            """, (key, key)).fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        if not self._verify_password(password, row["password_hash"]):
            return None

        user_id = row["user_id"]

        # Reuse an existing object when available.
        user = self._users.get(user_id)

        if user is None:
            user = self._row_to_user(row)
            self._users[user_id] = user

        self._current_user_id = user.user_id

        return user

    def logout(self):
        """Clear the current login session."""
        self._current_user_id = None

    def get_current_user(self):
        """Return the currently logged-in user."""
        if self._current_user_id is None:
            return None

        return self.get_user_by_id(self._current_user_id)

    def get_user_by_id(self, user_id):
        """Retrieve a user from the cache or database."""
        if user_id in self._users:
            return self._users[user_id]

        connection = self.database.get_connection()

        try:
            row = connection.execute("""
                SELECT *
                FROM users
                WHERE user_id = ?
            """, (user_id,)).fetchone()

        finally:
            connection.close()

        if row is None:
            return None

        user = self._row_to_user(row)
        self._users[user.user_id] = user

        return user

    @property
    def user_count(self):
        """Return the total number of registered users."""
        connection = self.database.get_connection()

        try:
            result = connection.execute("""
                SELECT COUNT(*) AS total
                FROM users
            """).fetchone()

            return result["total"]

        finally:
            connection.close()
