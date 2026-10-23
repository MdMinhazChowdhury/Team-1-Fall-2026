
from dataclasses import dataclass, field
from src.models import new_id


@dataclass
class Flashcard:
    question: str
    answer: str
    deck_id: str
    difficult: bool = False
    card_id: str = field(default_factory=new_id)

    def __post_init__(self):
        self.edit(self.question, self.answer)

        if not self.deck_id:
            raise ValueError("Deck ID cannot be empty.")

    def edit(self, question, answer):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer cannot be empty.")

        self.question = question.strip()
        self.answer = answer.strip()

    def mark_difficult(self, value=True):
        self.difficult = bool(value)
