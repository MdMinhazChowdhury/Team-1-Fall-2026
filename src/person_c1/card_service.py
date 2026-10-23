
from src.person_c1.card_factory import CardFactory


class CardService:
    def __init__(self, deck_service):
        self.deck_service = deck_service
        self.cards = {}

    def add_card(self, deck_id, question, answer):
        deck = self.deck_service.get_deck(deck_id)
        card = CardFactory.create_card(question, answer, deck.deck_id)

        self.cards[card.card_id] = card
        deck.add_card_id(card.card_id)
        return card

    def get_card(self, card_id):
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
        return True

    def delete_card(self, card_id):
        card = self.get_card(card_id)
        if card is None:
            return False

        deck = self.deck_service.get_deck(card.deck_id)
        deck.remove_card_id(card_id)
        del self.cards[card_id]
        return True

    def mark_difficult(self, card_id, value=True):
        card = self.get_card(card_id)
        if card is None:
            return False

        card.mark_difficult(value)
        return True

    def get_cards(self, deck_id):
        deck = self.deck_service.get_deck(deck_id)
        return [
            self.cards[card_id]
            for card_id in deck.card_ids
            if card_id in self.cards
        ]
