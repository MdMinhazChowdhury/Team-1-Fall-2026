
class SearchService:
    @staticmethod
    def search_cards(cards, keyword):
        if not isinstance(keyword, str) or not keyword.strip():
            return []

        keyword = keyword.strip().casefold()

        return [
            card for card in cards
            if keyword in card.question.casefold()
            or keyword in card.answer.casefold()
        ]

    @staticmethod
    def search_decks(decks, keyword):
        if not isinstance(keyword, str) or not keyword.strip():
            return []

        keyword = keyword.strip().casefold()

        return [
            deck for deck in decks
            if keyword in deck.title.casefold()
        ]

    @staticmethod
    def get_difficult_cards(cards):
        return [
            card for card in cards
            if card.difficult
        ]
