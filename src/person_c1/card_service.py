
from src.person_c1.card_factory import CardFactory
from src.person_c1.flashcard import Flashcard


class CardService:
    def __init__(self, deck_service):
        self.deck_service = deck_service
        self.database = getattr(deck_service, "database", None)
        self.cards = {}

    def add_card(self, deck_id, question, answer):
        deck = self.deck_service.get_deck(deck_id)
        card = CardFactory.create_card(
            question, answer, deck.deck_id
        )

        if self.database is not None:
            connection = self.database.get_connection()
            try:
                connection.execute(
                    """
                    INSERT INTO flashcards
                    (card_id, deck_id, question, answer, difficult)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        card.card_id,
                        card.deck_id,
                        card.question,
                        card.answer,
                        int(card.difficult),
                    ),
                )
                connection.commit()
            finally:
                connection.close()

        self.cards[card.card_id] = card
        deck.add_card_id(card.card_id)
        return card

    def get_card(self, card_id):
        if self.database is not None:
            connection = self.database.get_connection()
            try:
                row = connection.execute(
                    "SELECT * FROM flashcards WHERE card_id = ?",
                    (card_id,),
                ).fetchone()
            finally:
                connection.close()

            if row is None:
                return None

            self.deck_service.get_deck(row["deck_id"])

            return Flashcard(
                question=row["question"],
                answer=row["answer"],
                deck_id=row["deck_id"],
                difficult=bool(row["difficult"]),
                card_id=row["card_id"],
            )

        card = self.cards.get(card_id)
        if card is None:
            return None

        self.deck_service.get_deck(card.deck_id)
        return card

    def edit_card(self, card_id, question, answer):
        card = self.get_card(card_id)
        if card is None:
            return False

        card.edit(question, answer)

        if self.database is not None:
            connection = self.database.get_connection()
            try:
                connection.execute(
                    """
                    UPDATE flashcards
                    SET question = ?, answer = ?
                    WHERE card_id = ?
                    """,
                    (card.question, card.answer, card_id),
                )
                connection.commit()
            finally:
                connection.close()

        self.cards[card_id] = card
        return True

    def delete_card(self, card_id):
        card = self.get_card(card_id)
        if card is None:
            return False

        deck = self.deck_service.get_deck(card.deck_id)

        if self.database is not None:
            connection = self.database.get_connection()
            try:
                connection.execute(
                    "DELETE FROM flashcards WHERE card_id = ?",
                    (card_id,),
                )
                connection.commit()
            finally:
                connection.close()

        deck.remove_card_id(card_id)
        self.cards.pop(card_id, None)
        return True

    def mark_difficult(self, card_id, value=True):
        card = self.get_card(card_id)
        if card is None:
            return False

        card.mark_difficult(value)

        if self.database is not None:
            connection = self.database.get_connection()
            try:
                connection.execute(
                    """
                    UPDATE flashcards
                    SET difficult = ?
                    WHERE card_id = ?
                    """,
                    (int(card.difficult), card_id),
                )
                connection.commit()
            finally:
                connection.close()

        self.cards[card_id] = card
        return True

    def get_cards(self, deck_id):
        deck = self.deck_service.get_deck(deck_id)

        if self.database is not None:
            connection = self.database.get_connection()
            try:
                rows = connection.execute(
                    """
                    SELECT * FROM flashcards
                    WHERE deck_id = ?
                    """,
                    (deck_id,),
                ).fetchall()
            finally:
                connection.close()

            cards = [
                Flashcard(
                    question=row["question"],
                    answer=row["answer"],
                    deck_id=row["deck_id"],
                    difficult=bool(row["difficult"]),
                    card_id=row["card_id"],
                )
                for row in rows
            ]

            for card in cards:
                deck.add_card_id(card.card_id)

            return cards

        return [
            self.cards[card_id]
            for card_id in deck.card_ids
            if card_id in self.cards
        ]
