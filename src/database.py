
"""Shared SQLite database for the Flashcard Study Application."""

import sqlite3
from pathlib import Path


# Store the database in the main project directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "flashcards.db"


class Database:
    """Manage the shared application database."""

    def __init__(self, database_path=DEFAULT_DATABASE_PATH):
        self.database_path = str(database_path)

    def get_connection(self):
        """Open a database connection with foreign keys enabled."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_database(self):
        """Create the initial shared database tables."""

        connection = self.get_connection()

        try:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    category_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL COLLATE NOCASE,
                    owner_id TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',

                    FOREIGN KEY (owner_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    UNIQUE (owner_id, name)
                );

                CREATE TABLE IF NOT EXISTS decks (
                    deck_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    category_id TEXT,
                    created_at TEXT NOT NULL,

                    FOREIGN KEY (owner_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (category_id)
                        REFERENCES categories(category_id)
                        ON DELETE SET NULL
                );


                CREATE TABLE IF NOT EXISTS flashcards (
                    card_id TEXT PRIMARY KEY,
                     deck_id TEXT NOT NULL,
                     question TEXT NOT NULL,
                     answer TEXT NOT NULL,
                     difficult INTEGER NOT NULL DEFAULT 0
                     CHECK (difficult IN (0, 1)),

                    FOREIGN KEY (deck_id)
                     REFERENCES decks(deck_id)
                      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_flashcards_deck
ON flashcards(deck_id);


                CREATE INDEX IF NOT EXISTS idx_decks_owner
                ON decks(owner_id);

                CREATE INDEX IF NOT EXISTS idx_categories_owner
                ON categories(owner_id);
            """)

            connection.commit()

        finally:
            connection.close()
