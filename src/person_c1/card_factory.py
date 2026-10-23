
from src.person_c1.flashcard import Flashcard


class CardFactory:
    @staticmethod
    def create_card(question, answer, deck_id, difficult=False):
        return Flashcard(
            question=question,
            answer=answer,
            deck_id=deck_id,
            difficult=difficult,
        )
