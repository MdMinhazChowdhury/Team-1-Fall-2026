
"""Manage user registration and authentication."""

import hashlib
import hmac
import os

from src.person_b.models import User


class AuthService:
    """Register users and manage login sessions."""

    def __init__(self):
        self._users = {}
        self._usernames = {}
        self._emails = {}
        self._current_user_id = None

    @staticmethod
    def _normalize(value):
        return value.strip().casefold()

    @staticmethod
    def _hash_password(password, salt=None):
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
        try:
            salt_hex, expected_hash = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
        except (ValueError, TypeError):
            return False

        actual_hash = cls._hash_password(password, salt)
        return hmac.compare_digest(
            actual_hash.split("$", 1)[1],
            expected_hash
        )

    def register(self, username, email, password):
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Username is required.")

        if not isinstance(email, str) or "@" not in email:
            raise ValueError("A valid email is required.")

        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        username = username.strip()
        email = email.strip()

        username_key = self._normalize(username)
        email_key = self._normalize(email)

        if username_key in self._usernames:
            raise ValueError("Username already exists.")

        if email_key in self._emails:
            raise ValueError("Email already exists.")

        user = User(
            username=username,
            email=email,
            password_hash=self._hash_password(password)
        )

        self._users[user.user_id] = user
        self._usernames[username_key] = user.user_id
        self._emails[email_key] = user.user_id

        return user

    def login(self, username_or_email, password):
        if not isinstance(username_or_email, str):
            return None

        key = self._normalize(username_or_email)

        user_id = self._usernames.get(key)
        if user_id is None:
            user_id = self._emails.get(key)

        if user_id is None:
            return None

        user = self._users[user_id]

        if not self._verify_password(password, user.password_hash):
            return None

        self._current_user_id = user.user_id
        return user

    def logout(self):
        self._current_user_id = None

    def get_current_user(self):
        if self._current_user_id is None:
            return None

        return self._users.get(self._current_user_id)

    def get_user_by_id(self, user_id):
        return self._users.get(user_id)

    @property
    def user_count(self):
        return len(self._users)
