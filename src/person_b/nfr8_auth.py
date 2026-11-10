
"""NFR8: Prevent unauthorized access to private flashcard decks."""


class NFR8Auth:
    """Control access to private decks based on ownership."""

    @staticmethod
    def can_access(deck, user_id):
        """Check whether the user owns the requested deck."""
        if deck is None or user_id is None:
            return False

        return deck.owner_id == user_id

    @classmethod
    def require_access(cls, deck, user_id):
        """Require ownership before allowing deck access."""
        if not cls.can_access(deck, user_id):
            raise PermissionError(
                "Unauthorized: You cannot access this private deck."
            )

        return True

    @classmethod
    def require_edit_access(cls, deck, user_id):
        return cls.require_access(deck, user_id)

    @classmethod
    def require_delete_access(cls, deck, user_id):
        return cls.require_access(deck, user_id)

    @classmethod
    def require_card_access(cls, deck, user_id):
        return cls.require_access(deck, user_id)
