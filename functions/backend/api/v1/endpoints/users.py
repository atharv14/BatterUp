from fastapi import APIRouter, Depends, HTTPException
from models.schemas.user import UserCreate, UserUpdate, UserInDB, Deck
from core.firebase_auth import get_current_user
from services.firebase import db
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/create", response_model=UserInDB)
async def create_user(user_data: UserCreate):
    try:
        # Check if user already exists
        user_ref = db.collection('users').document(user_data.firebase_uid)
        if user_ref.get().exists:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )

        current_time = datetime.utcnow()
        user_dict = {
            **user_data.dict(),
            'created_at': current_time,
            'updated_at': current_time,
            'deck': None
        }

        # Create user document
        user_ref.set(user_dict)
        return UserInDB(**user_dict)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/deck", response_model=UserInDB)
async def update_deck(
    deck: Deck,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_ref.get()

        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Validate all player IDs exist
        all_player_ids = (
            deck.catchers + deck.pitchers + 
            deck.infielders + deck.outfielders + 
            deck.hitters
        )

        # Batch get all players
        player_refs = [db.collection('players').document(pid) 
                      for pid in all_player_ids]
        player_snapshots = db.get_all(player_refs)

        # Verify all players exist and match their positions
        for player_snap in player_snapshots:
            if not player_snap.exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_snap.id} not found"
                )

            player_data = player_snap.to_dict()
            position = player_data['basic_info']['primary_position']
            player_id = str(player_data['player_id'])

            # Position verification
            if player_id in deck.catchers and position != "Catcher":
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_id} is not a Catcher"
                )
            elif player_id in deck.pitchers and position != "Pitcher":
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_id} is not a Pitcher"
                )
            elif player_id in deck.infielders and position != "Infielder":
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_id} is not an Infielder"
                )
            elif player_id in deck.outfielders and position != "Outfielder":
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {player_id} is not an Outfielder"
                )
            # For hitters, allowed any position as they can be utility players

        # Update deck
        user_ref.update({
            'deck': deck.dict(),
            'updated_at': datetime.utcnow()
        })

        # Get updated user data
        updated_user = user_ref.get().to_dict()
        
        # Ensure all required fields are present
        if not all(field in updated_user for field in ['email', 'username', 'role', 'firebase_uid', 'created_at', 'updated_at', 'deck']):
            raise HTTPException(
                status_code=500,
                detail="Updated user data is incomplete"
            )
        
        return UserInDB(**updated_user)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating deck: {str(e)}"
        )
