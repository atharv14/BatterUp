from typing import List, Dict, Optional
from datetime import datetime
from models.schemas.player import Deck, Position, DeckRequirements, DeckValidationError
from services.firebase import db

class DeckService:
    def __init__(self):
        self.decks_ref = db.collection('decks')
        self.players_ref = db.collection('players')

    async def validate_deck_composition(self, cards: Dict[Position, List[str]]) -> bool:
        """Validate deck meets composition requirements"""
        try:
            # Check card counts
            for position, required_count in DeckRequirements.REQUIRED_CARDS.items():
                if len(cards.get(position, [])) != required_count:
                    raise DeckValidationError(
                        f"Invalid number of {position} cards. Required: {required_count}"
                    )

            # Validate each card exists and has correct position
            for position, card_ids in cards.items():
                for card_id in card_ids:
                    card_doc = self.players_ref.document(str(card_id)).get()
                    if not card_doc.exists:
                        raise DeckValidationError(f"Card {card_id} not found")
                    
                    card_data = card_doc.to_dict()
                    if card_data['role_info']['primary_role'] != position:
                        raise DeckValidationError(
                            f"Card {card_id} is not a {position}"
                        )

            return True
        except Exception as e:
            raise DeckValidationError(str(e))

    async def create_deck(self, user_id: str, cards: Dict[Position, List[str]]) -> Deck:
        """Create new deck for user"""
        # Validate deck composition
        await self.validate_deck_composition(cards)
        
        current_time = datetime.utcnow().isoformat()
        deck_dict = {
            "user_id": user_id,
            "cards": cards,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # Create deck document
        deck_ref = self.decks_ref.document()
        deck_ref.set(deck_dict)
        
        # Update user's current deck
        db.collection('users').document(user_id).update({
            "current_deck_id": deck_ref.id
        })
        
        return Deck(**deck_dict)

    async def get_deck(self, deck_id: str) -> Optional[Deck]:
        """Get deck by ID"""
        doc = self.decks_ref.document(deck_id).get()
        return Deck(**doc.to_dict()) if doc.exists else None

deck_service = DeckService()