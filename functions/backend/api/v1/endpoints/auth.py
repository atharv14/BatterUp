# api/v1/endpoints/auth.py
from fastapi import APIRouter, HTTPException, Depends
from models.schemas.user import UserCreate, UserResponse, UserUpdate
from core.firebase_auth import get_current_user
from services.firebase import db
from datetime import datetime

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)  # This ensures valid Firebase token
):
    """
    Create user record in Firestore after Firebase Authentication
    """
    try:
        # Verify Firebase UID matches token
        if current_user['uid'] != user_data.firebase_uid:
            raise HTTPException(
                status_code=403,
                detail="Firebase UID mismatch"
            )

        # Check if user already exists
        user_ref = db.collection('users').document(user_data.firebase_uid)
        if user_ref.get().exists:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )

        user_dict = {
            "firebase_uid": user_data.firebase_uid,
            "email": user_data.email,
            "username": user_data.username,
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "deck": None,
            "stats": {
                "games_played": 0,
                "wins": 0,
                "losses": 0
            }
        }

        # Create user document in Firestore
        user_ref.set(user_dict)

        return UserResponse(**user_dict)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile from Firestore
    """
    try:
        user_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_ref.get()

        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        return UserResponse(**user_doc.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user profile: {str(e)}"
        )

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user's profile in Firestore
    """
    try:
        user_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_ref.get()

        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )

        update_dict = {
            "updated_at": datetime.utcnow().isoformat(),
            **update_data.dict(exclude_unset=True, exclude_none=True)
        }

        user_ref.update(update_dict)
        
        # Get updated document
        updated_doc = user_ref.get()
        return UserResponse(**updated_doc.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user profile: {str(e)}"
        )