from fastapi import APIRouter, HTTPException, status
from models.schemas.game import (
    GameCreate, GameState, PlayerSelection,
    GameStatus, PlayerRole, PitchingStyle
)
from services.firebase import db
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/create", response_model=GameState)
async def create_game(game_data: GameCreate):
    """Create a new game session"""
    try:
        # Validate player selections
        await validate_player_selection(game_data.player1_id, game_data.player1_selection)

        game_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()

        game_state = {
            "game_id": game_id,
            "status": GameStatus.WAITING if not game_data.player2_id else GameStatus.IN_PROGRESS,
            "player1": game_data.player1_selection.dict(),
            "player2": None,
            "current_state": {
                "inning": 1,
                "top_inning": True,
                "outs": 0,
                "score": {"player1": 0, "player2": 0},
                "bases": {"first": None, "second": None, "third": None}
            },
            "created_at": current_time,
            "updated_at": current_time
        }

        # Store in Firestore
        doc_ref = db.collection('games').document(game_id)
        doc_ref.set(game_state)

        return game_state

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating game: {str(e)}"
        )

@router.post("/{game_id}/join", response_model=GameState)
async def join_game(
    game_id: str,
    player_selection: PlayerSelection
):
    """Join an existing game"""
    try:
        # Get game state
        doc_ref = db.collection('games').document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )

        game_state = doc.to_dict()

        if game_state["status"] != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not available to join"
            )

        # Validate player selection
        await validate_player_selection(player_selection.player_id, player_selection)

        # Update game state
        game_state["player2"] = player_selection.dict()
        game_state["status"] = GameStatus.IN_PROGRESS
        game_state["updated_at"] = datetime.utcnow().isoformat()

        # Update in Firestore
        doc_ref.update(game_state)

        return game_state

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining game: {str(e)}"
        )

async def validate_player_selection(player_id: str, selection: PlayerSelection):
    """Validate player role selection"""
    try:
        # Get player data
        doc_ref = db.collection('players').document(str(player_id))
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found"
            )

        player_data = doc.to_dict()
        role_info = player_data.get('role_info', {})

        # Validate role selection
        if selection.role == PlayerRole.PITCHER:
            if role_info.get('primary_role') != 'Pitcher':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected player cannot be used as a pitcher"
                )

            # Validate pitching styles
            valid_styles = role_info.get('pitching_styles', [])
            selected_styles = selection.role_specific_info.get('pitching_styles', [])

            if not all(style in valid_styles for style in selected_styles):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pitching style selection"
                )

        # Add similar validation for other roles

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating player selection: {str(e)}"
        )
