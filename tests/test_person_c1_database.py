
import pytest

from src.database import Database
from src.person_b.models import Deck
from src.person_c1.card_service import CardService


class DatabaseDeckService:
    def __init__(self, database, deck):
        self.database = database
        self.deck = deck

    def get_deck(self, deck_id):
        if deck_id != self.deck.deck_id:
            raise PermissionError("Deck not found.")
        return self.deck


@pytest.fixture
def setup_database(tmp_path):
    database = Database(tmp_path / "test_flashcards.db")
    database.initialize_database()

    connection = database.get_connection()
    try:
        connection.execute(
            """
            INSERT INTO users
            (user_id, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "user1",
                "testuser",
                "test@example.com",
                "test_hash",
                "2026-11-12",
            ),
        )

        deck = Deck(
            title="Computer Science",
            owner_id="user1",
        )

        connection.execute(
            """
            INSERT INTO decks
            (deck_id, title, owner_id, description,
             category_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                deck.deck_id,
                deck.title,
                deck.owner_id,
                deck.description,
                deck.category_id,
                deck.created_at,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return database, deck


def test_card_saved_to_database(setup_database):
    database, deck = setup_database
    service = CardService(DatabaseDeckService(database, deck))

    card = service.add_card(deck.deck_id, "What is Python?", "A language")

    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM flashcards WHERE card_id = ?",
            (card.card_id,),
        ).fetchone()
    finally:
        connection.close()

    assert row is not None
    assert row["question"] == "What is Python?"


def test_card_persists_after_new_service(setup_database):
    database, deck = setup_database
    first = CardService(DatabaseDeckService(database, deck))
    card = first.add_card(deck.deck_id, "Question", "Answer")

    new_deck = Deck(
        title=deck.title,
        owner_id=deck.owner_id,
        deck_id=deck.deck_id,
    )
    second = CardService(DatabaseDeckService(database, new_deck))

    saved = second.get_card(card.card_id)

    assert saved is not None
    assert saved.question == "Question"
    assert len(second.get_cards(deck.deck_id)) == 1


def test_card_edit_persists(setup_database):
    database, deck = setup_database
    service = CardService(DatabaseDeckService(database, deck))
    card = service.add_card(deck.deck_id, "Old", "Answer")

    assert service.edit_card(card.card_id, "New", "Updated")

    second = CardService(DatabaseDeckService(database, deck))
    saved = second.get_card(card.card_id)

    assert saved.question == "New"
    assert saved.answer == "Updated"


def test_card_delete_persists(setup_database):
    database, deck = setup_database
    service = CardService(DatabaseDeckService(database, deck))
    card = service.add_card(deck.deck_id, "Question", "Answer")

    assert service.delete_card(card.card_id)

    second = CardService(DatabaseDeckService(database, deck))
    assert second.get_card(card.card_id) is None
    assert second.get_cards(deck.deck_id) == []


def test_difficult_setting_persists(setup_database):
    database, deck = setup_database
    service = CardService(DatabaseDeckService(database, deck))
    card = service.add_card(deck.deck_id, "Question", "Answer")

    assert service.mark_difficult(card.card_id)

    second = CardService(DatabaseDeckService(database, deck))
    saved = second.get_card(card.card_id)

    assert saved.difficult is True


def test_deleting_deck_cascades_to_cards(setup_database):
    database, deck = setup_database
    service = CardService(DatabaseDeckService(database, deck))
    card = service.add_card(deck.deck_id, "Question", "Answer")

    connection = database.get_connection()
    try:
        connection.execute(
            "DELETE FROM decks WHERE deck_id = ?",
            (deck.deck_id,),
        )
        connection.commit()

        row = connection.execute(
            "SELECT * FROM flashcards WHERE card_id = ?",
            (card.card_id,),
        ).fetchone()
    finally:
        connection.close()

    assert row is None
