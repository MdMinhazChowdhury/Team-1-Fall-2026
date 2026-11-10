
"""Performance tests for Person B backend operations."""

import time

from src.database import Database
from src.person_b.auth_service import AuthService
from src.person_b.deck_service import DeckService


def test_backend_operation_performance(tmp_path):
    """Measure registration, login, deck creation, and retrieval times."""

    database = Database(tmp_path / "performance_test.db")
    auth = AuthService(database)
    service = DeckService(auth)

    # 1. Measure user registration.
    start = time.perf_counter()

    user = auth.register(
        "Alyssa",
        "alyssa@example.com",
        "Password123"
    )

    registration_time = time.perf_counter() - start

    # 2. Measure user login.
    start = time.perf_counter()

    logged_in_user = auth.login(
        "Alyssa",
        "Password123"
    )

    login_time = time.perf_counter() - start

    assert logged_in_user is not None
    assert logged_in_user.user_id == user.user_id

    # 3. Measure deck creation.
    start = time.perf_counter()

    deck = service.create_deck("Biology")

    deck_creation_time = time.perf_counter() - start

    # 4. Measure deck retrieval.
    start = time.perf_counter()

    retrieved_deck = service.get_deck(deck.deck_id)

    deck_retrieval_time = time.perf_counter() - start

    assert retrieved_deck is not None
    assert retrieved_deck.deck_id == deck.deck_id

    # Display actual measurements in milliseconds.
    print("\n--- Person B Performance Test Results ---")
    print(f"User registration: {registration_time * 1000:.2f} ms")
    print(f"User login: {login_time * 1000:.2f} ms")
    print(f"Deck creation: {deck_creation_time * 1000:.2f} ms")
    print(f"Deck retrieval: {deck_retrieval_time * 1000:.2f} ms")

    # Broad performance limits, not official NFR targets.
    assert registration_time < 2.0
    assert login_time < 2.0
    assert deck_creation_time < 1.0
    assert deck_retrieval_time < 1.0
