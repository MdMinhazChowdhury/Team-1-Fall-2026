
from time import perf_counter
from types import SimpleNamespace
import pytest

from src.person_c1.flashcard import Flashcard
from src.person_c1.search_service import SearchService


def make_cards(n=1000):
    return [
        Flashcard(
            question=f"Question {i} Python",
            answer=f"Answer {i}",
            deck_id="deck1"
        )
        for i in range(n)
    ]


def test_search_case_insensitive_regression():
    cards = make_cards(20)

    results = SearchService.search_cards(cards, "pYtHoN")

    assert len(results) == 20


def test_search_no_matches_regression():
    cards = make_cards(20)

    results = SearchService.search_cards(
        cards, "unlikely-nonexistent-keyword"
    )

    assert results == []


def test_difficult_card_filter_regression():
    cards = make_cards(10)

    cards[0].mark_difficult()
    cards[3].mark_difficult()

    results = SearchService.get_difficult_cards(cards)

    assert len(results) == 2
    assert cards[0] in results
    assert cards[3] in results


def test_search_performance_measurement():
    cards = make_cards(1000)

    started = perf_counter()

    for _ in range(100):
        results = SearchService.search_cards(cards, "Python")
        assert len(results) == 1000

    elapsed = perf_counter() - started

    print(
        f"\nC1 search performance: "
        f"100 searches over 1,000 cards in "
        f"{elapsed:.6f} seconds; "
        f"{elapsed / 100 * 1000:.3f} ms/search"
    )

    assert elapsed >= 0


def test_difficult_filter_performance_measurement():
    cards = make_cards(1000)

    for card in cards[::5]:
        card.mark_difficult()

    started = perf_counter()

    for _ in range(100):
        results = SearchService.get_difficult_cards(cards)
        assert len(results) == 200

    elapsed = perf_counter() - started

    print(
        f"\nC1 difficult-filter performance: "
        f"100 filters over 1,000 cards in "
        f"{elapsed:.6f} seconds; "
        f"{elapsed / 100 * 1000:.3f} ms/filter"
    )

    assert elapsed >= 0


def test_load_200_flashcards_performance():
    started = perf_counter()

    cards = make_cards(200)

    elapsed = perf_counter() - started

    assert len(cards) == 200

    print(
        f"\nNFR1 - Create 200 flashcards: "
        f"{elapsed:.6f} seconds"
    )

    assert elapsed <= 3.0


def test_search_200_flashcards_performance():
    cards = make_cards(200)

    started = perf_counter()

    results = SearchService.search_cards(cards, "Python")

    elapsed = perf_counter() - started

    assert len(results) == 200

    print(
        f"\nNFR5 - Search 200 flashcards: "
        f"{elapsed:.6f} seconds"
    )

    assert elapsed <= 2.0


def test_edit_200_flashcards_performance():
    cards = make_cards(200)

    started = perf_counter()

    for i, card in enumerate(cards):
        card.edit(
            question=f"Updated Question {i}",
            answer=f"Updated Answer {i}"
        )

    elapsed = perf_counter() - started

    assert len(cards) == 200
    assert cards[0].question == "Updated Question 0"
    assert cards[199].answer == "Updated Answer 199"

    print(
        f"\nNFR9 - Edit 200 flashcards: "
        f"{elapsed:.6f} seconds"
    )

    assert elapsed <= 2.0


def test_nfr4_search_flashcard_text():
    cards = make_cards(200)

    results = SearchService.search_cards(cards, "Python")

    assert len(results) == 200

    print("\nNFR4 - Flashcard text search PASSED")


def test_nfr4_search_deck_names():
    decks = [
        SimpleNamespace(title="Computer Science"),
        SimpleNamespace(title="Mathematics"),
        SimpleNamespace(title="Biology")
    ]

    results = SearchService.search_decks(decks, "science")

    assert len(results) == 1
    assert results[0].title == "Computer Science"

    print("\nNFR4 - Deck title search PASSED")


def test_nfr4_search_modes_independent():
    cards = make_cards(200)

    decks = [
        SimpleNamespace(title="History"),
        SimpleNamespace(title="Python Programming")
    ]

    card_results = SearchService.search_cards(
        cards, "Python"
    )

    deck_results = SearchService.search_decks(
        decks, "Python"
    )

    assert len(card_results) == 200
    assert len(deck_results) == 1

    print("\nNFR4 - Both search modes PASSED")
