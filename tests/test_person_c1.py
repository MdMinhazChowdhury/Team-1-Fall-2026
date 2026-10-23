
import pytest

from src.models import Deck
from src.person_c1.flashcard import Flashcard
from src.person_c1.card_factory import CardFactory
from src.person_c1.card_service import CardService
from src.person_c1.search_service import SearchService


class FakeDeckService:
    def __init__(self):
        self.deck = Deck(
            title="Computer Science",
            owner_id="user1"
        )

    def get_deck(self, deck_id):
        if deck_id != self.deck.deck_id:
            raise PermissionError("Deck not found.")
        return self.deck


@pytest.fixture
def setup_service():
    deck_service = FakeDeckService()
    card_service = CardService(deck_service)
    return card_service, deck_service.deck


def test_create_flashcard():
    card = Flashcard("What is Python?", "A language", "deck1")
    assert card.question == "What is Python?"
    assert card.answer == "A language"
    assert card.deck_id == "deck1"


def test_edit_flashcard():
    card = Flashcard("Old", "Answer", "deck1")
    card.edit("New Question", "New Answer")
    assert card.question == "New Question"
    assert card.answer == "New Answer"


def test_mark_difficult():
    card = Flashcard("Question", "Answer", "deck1")
    card.mark_difficult()
    assert card.difficult is True


def test_invalid_flashcard():
    with pytest.raises(ValueError):
        Flashcard("", "Answer", "deck1")


def test_card_factory():
    card = CardFactory.create_card("Question", "Answer", "deck1")
    assert isinstance(card, Flashcard)
    assert card.card_id


def test_unique_card_ids():
    first = CardFactory.create_card("Q1", "A1", "deck1")
    second = CardFactory.create_card("Q2", "A2", "deck1")
    assert first.card_id != second.card_id


def test_add_card(setup_service):
    service, deck = setup_service
    card = service.add_card(deck.deck_id, "Question", "Answer")
    assert card.card_id in deck.card_ids
    assert service.get_card(card.card_id) == card


def test_edit_card(setup_service):
    service, deck = setup_service
    card = service.add_card(deck.deck_id, "Old", "Answer")
    assert service.edit_card(card.card_id, "New", "Updated")
    assert card.question == "New"


def test_delete_card(setup_service):
    service, deck = setup_service
    card = service.add_card(deck.deck_id, "Question", "Answer")
    assert service.delete_card(card.card_id)
    assert card.card_id not in deck.card_ids
    assert service.get_card(card.card_id) is None


def test_mark_card_difficult(setup_service):
    service, deck = setup_service
    card = service.add_card(deck.deck_id, "Question", "Answer")
    assert service.mark_difficult(card.card_id)
    assert card.difficult is True


def test_list_deck_cards(setup_service):
    service, deck = setup_service
    service.add_card(deck.deck_id, "Q1", "A1")
    service.add_card(deck.deck_id, "Q2", "A2")
    assert len(service.get_cards(deck.deck_id)) == 2


def test_search_cards():
    cards = [
        Flashcard("What is Python?", "Language", "deck1"),
        Flashcard("What is Java?", "Programming", "deck1")
    ]
    results = SearchService.search_cards(cards, "python")
    assert len(results) == 1
    assert results[0].question == "What is Python?"


def test_search_decks():
    decks = [Deck(title="Biology", owner_id="user1")]
    results = SearchService.search_decks(decks, "BIOLOGY")
    assert len(results) == 1


def test_get_difficult_cards():
    cards = [
        Flashcard("Q1", "A1", "deck1", difficult=True),
        Flashcard("Q2", "A2", "deck1")
    ]
    assert len(SearchService.get_difficult_cards(cards)) == 1
