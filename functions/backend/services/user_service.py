from datetime import datetime
from typing import Optional, Dict
from firebase_admin import firestore
from models.schemas.user import UserCreate, UserInDB
from services.firebase import db

class UserService:
    def __init__(self):
        self.users_ref = db.collection('users')

    async def get_user(self, firebase_uid: str) -> Optional[Dict]:
        """Get user by Firebase UID"""
        doc = self.users_ref.document(firebase_uid).get()
        return doc.to_dict() if doc.exists else None

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create new user in Firestore"""
        current_time = datetime.utcnow().isoformat()
        user_dict = {
            "firebase_uid": user_data.firebase_uid,
            "email": user_data.email,
            "username": user_data.username,
            "current_deck_id": None,
            "created_at": current_time,
            "updated_at": current_time,
            "stats": {
                "games_played": 0,
                "games_won": 0,
                "games_lost": 0
            }
        }
        
        # Create user document
        self.users_ref.document(user_data.firebase_uid).set(user_dict)
        return UserInDB(**user_dict)

    async def update_user_stats(self, firebase_uid: str, game_result: str):
        """Update user statistics after game"""
        user_ref = self.users_ref.document(firebase_uid)
        
        user_ref.update({
            "stats.games_played": firestore.Increment(1),
            f"stats.games_{game_result}": firestore.Increment(1),
            "updated_at": datetime.utcnow().isoformat()
        })

user_service = UserService()