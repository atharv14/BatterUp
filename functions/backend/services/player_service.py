from typing import Dict
from services.firebase import db

async def get_player_data(player_id: str) -> Dict:
    """Get player data from Firestore"""
    try:
        doc_ref = db.collection('players').document(str(player_id))
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError(f"Player {player_id} not found")
        return doc.to_dict()
    except Exception as e:
        raise Exception(f"Error getting player data: {str(e)}")