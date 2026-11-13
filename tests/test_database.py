
"""Tests for the shared SQLite database."""

import sqlite3

from src.database import Database


def test_database_is_created(tmp_path):
    database_path = tmp_path / "test_flashcards.db"
    database = Database(database_path)

    database.initialize_database()

    assert database_path.exists()


def test_required_tables_are_created(tmp_path):
    database = Database(tmp_path / "test_flashcards.db")
    database.initialize_database()

    connection = database.get_connection()

    try:
        results = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """).fetchall()

        table_names = [row["name"] for row in results]

        assert "users" in table_names
        assert "categories" in table_names
        assert "decks" in table_names

    finally:
        connection.close()


def test_database_enforces_unique_usernames(tmp_path):
    database = Database(tmp_path / "test_flashcards.db")
    database.initialize_database()

    connection = database.get_connection()

    try:
        connection.execute("""
            INSERT INTO users
            (user_id, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("user1", "alyssa", "alyssa@example.com",
              "test_hash", "2026-11-10"))

        connection.commit()

        try:
            connection.execute("""
                INSERT INTO users
                (user_id, username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("user2", "ALYSSA", "other@example.com",
                  "test_hash", "2026-11-10"))

            assert False, "Duplicate username should not be allowed."

        except sqlite3.IntegrityError:
            pass

    finally:
        connection.close()


def test_database_enforces_user_ownership_reference(tmp_path):
    database = Database(tmp_path / "test_flashcards.db")
    database.initialize_database()

    connection = database.get_connection()

    try:
        try:
            connection.execute("""
                INSERT INTO decks
                (deck_id, title, owner_id, description,
                 category_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("deck1", "Study Deck", "missing_user",
                  "", None, "2026-11-10"))

            connection.commit()

            assert False, "Deck must reference an existing user."

        except sqlite3.IntegrityError:
            pass

    finally:
        connection.close()
