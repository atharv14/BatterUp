from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from models.schemas.game import (
    GameCreate, GameJoin, GameState, GameView,
    Action, GameHistory, PlayResult
)
from models.schemas.base import GameStatus, PitchingStyle, HittingStyle
from core.firebase_auth import get_current_user
from services.firebase import db
from datetime import datetime, timedelta
import uuid

router = APIRouter()


@router.post("/create", response_model=GameView)
async def create_game(
    game_data: GameCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new game session"""
    try:
        if current_user['uid'] != game_data.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can only create game for yourself"
            )

        game_id = str(uuid.uuid4())
        current_time = datetime.utcnow()

        # Initialize first batter and pitcher
        team1_state = {
            "user_id": game_data.user_id,
            "deck": game_data.deck.dict(),
            "current_pitcher": game_data.deck.pitchers[0],
            "current_batter": game_data.deck.hitters[0],
            "score": 0,
            "hits": 0,
            "errors": 0,
            "player_stats": {}
        }

        game_state = {
            "game_id": game_id,
            "status": GameStatus.WAITING,
            "inning": 1,
            "is_top_inning": True,
            "outs": 0,
            "bases": {},
            "team1": team1_state,
            "team2": None,
            "last_action": None,
            "action_deadline": None,
            "created_at": current_time,
            "updated_at": current_time
        }

        # Store in Firestore
        db.collection('games').document(game_id).set(game_state)

        return {
            "game_id": game_id,
            "state": GameState(**game_state),
            "history": []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating game: {str(e)}"
        )


@router.post("/{game_id}/join", response_model=GameView)
async def join_game(
    game_id: str,
    join_data: GameJoin,
    current_user: dict = Depends(get_current_user)
):
    """Join an existing game"""
    try:
        if current_user['uid'] != join_data.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can only join game for yourself"
            )

        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )

        game_state = game.to_dict()

        if game_state["status"] != GameStatus.WAITING:
            raise HTTPException(
                status_code=400,
                detail="Game is not available to join"
            )

        # Initialize second team
        team2_state = {
            "user_id": join_data.user_id,
            "deck": join_data.deck.dict(),
            "current_pitcher": join_data.deck.pitchers[0],
            "current_batter": join_data.deck.hitters[0],
            "score": 0,
            "hits": 0,
            "errors": 0,
            "player_stats": {}
        }

        # Update game state
        game_state["team2"] = team2_state
        game_state["status"] = GameStatus.IN_PROGRESS
        game_state["updated_at"] = datetime.utcnow()

        # Update in Firestore
        game_ref.update(game_state)

        return {
            "game_id": game_id,
            "state": GameState(**game_state),
            "history": []
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error joining game: {str(e)}"
        )


@router.post("/{game_id}/pitch")
async def make_pitch(
    game_id: str,
    pitch_style: PitchingStyle,
    current_user: dict = Depends(get_current_user)
):
    """Make a pitch"""
    try:
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )

        game_state = game.to_dict()

        # Validate game status
        if game_state["status"] != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400,
                detail="Game is not in progress"
            )

        # Validate it's pitcher's turn
        current_pitcher_id = game_state["team2"]["user_id"] if game_state[
            "is_top_inning"] else game_state["team1"]["user_id"]
        if current_user['uid'] != current_pitcher_id:
            raise HTTPException(
                status_code=400,
                detail="Not your turn to pitch"
            )

        # Create pitch action
        current_time = datetime.utcnow()
        action = {
            "player_id": current_user['uid'],
            "timestamp": current_time,
            "action_type": "pitch",
            "selected_style": pitch_style
        }

        # Update game state
        game_state["last_action"] = action
        game_state["action_deadline"] = current_time + timedelta(seconds=30)
        game_state["updated_at"] = current_time

        # Save state
        game_ref.update(game_state)

        return GameState(**game_state)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing pitch: {str(e)}"
        )


@router.post("/{game_id}/bat")
async def make_bat(
    game_id: str,
    hit_style: HittingStyle,
    current_user: dict = Depends(get_current_user)
):
    """Make a batting attempt"""
    try:
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )

        game_state = game.to_dict()

        # Validate game status and timing
        if game_state["status"] != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400,
                detail="Game is not in progress"
            )

        # Convert action_deadline to datetime if it's a string
        action_deadline = game_state["action_deadline"]
        if isinstance(action_deadline, str):
            action_deadline = datetime.fromisoformat(
                action_deadline.replace('Z', '+00:00'))

        if datetime.now(action_deadline.tzinfo) > action_deadline:
            raise HTTPException(
                status_code=400,
                detail="Action timeout! Took more than 5 seconds to make an action"
            )

        # Validate it's batter's turn
        current_batter_id = game_state["team1"]["user_id"] if game_state["is_top_inning"] else game_state["team2"]["user_id"]
        if current_user['uid'] != current_batter_id:
            raise HTTPException(
                status_code=400,
                detail="Not your turn to bat"
            )

        # Process the at-bat
        result = process_at_bat(
            game_state,
            hit_style
        )

        # Update game state
        game_state = update_game_state(game_state, result)
        game_state["updated_at"] = datetime.now().isoformat()

        # # Save state and history
        # batch = db.batch()

        # # Update game state
        # batch.update(game_ref, game_state)

        # # Add to history
        # history_ref = game_ref.collection('history').document()
        # history_entry = create_history_entry(game_state, result)
        # batch.set(history_ref, history_entry)

        # # Commit all updates
        # batch.commit()

        # Save state and history
        game_ref.update(game_state)

        return {
            "game_state": GameState(**game_state),
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing bat: {str(e)}"
        )


def process_at_bat(game_state: dict, hit_style: HittingStyle) -> PlayResult:
    """Process a batting attempt and return the result"""
    # Simple probability-based outcome
    import random

    outcomes = [
        ("home_run", "Home run! Ball went over the fence!", 1),
        ("triple", "Triple! Ball hit deep into the outfield!", 0),
        ("double", "Double! Ball hit into the gap!", 0),
        ("single", "Single! Ball hit into the outfield!", 0),
        ("out", "Out! Ball caught by fielder.", 0)
    ]

    weights = [0.1, 0.1, 0.2, 0.3, 0.3]  # Probabilities for each outcome
    outcome, description, error = random.choices(outcomes, weights=weights)[0]

    return PlayResult(
        outcome=outcome,
        description=description,
        batting_team_runs=1 if outcome == "home_run" else 0,
        fielding_team_errors=error
    )


def update_game_state(game_state: dict, result: PlayResult) -> dict:
    """Update game state based on play result"""
    current_time = datetime.utcnow()

    # Update score if there was a home run
    if result.batting_team_runs > 0:
        if game_state["is_top_inning"]:
            game_state["team1"]["score"] += result.batting_team_runs
        else:
            game_state["team2"]["score"] += result.batting_team_runs

    # Update outs if the result was an out
    if result.outcome == "out":
        game_state["outs"] += 1

        # Check if inning is over
        if game_state["outs"] >= 3:
            game_state["outs"] = 0
            game_state["is_top_inning"] = not game_state["is_top_inning"]
            if not game_state["is_top_inning"]:
                game_state["inning"] += 1

            # Set up next pitcher's turn
            game_state["last_action"] = None
            game_state["action_deadline"] = current_time + timedelta(seconds=5)
        else:
            # Set up next pitcher's turn for same inning
            game_state["last_action"] = None
            game_state["action_deadline"] = current_time + timedelta(seconds=5)
    else:
        # If it's a hit, set up next pitcher's turn
        game_state["last_action"] = None
        game_state["action_deadline"] = current_time + timedelta(seconds=5)

    # Check if game should end (9 innings completed)
    if game_state["inning"] > 9 and not game_state["is_top_inning"]:
        game_state["status"] = GameStatus.COMPLETED
        # Determine winner
        game_state["winner"] = (
            game_state["team1"]["user_id"]
            if game_state["team1"]["score"] > game_state["team2"]["score"]
            else game_state["team2"]["user_id"]
        )

    return game_state


@router.get("/{game_id}", response_model=GameView)
async def get_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current game state and history"""
    try:
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )

        game_state = game.to_dict()

        # Verify user is part of this game
        if (current_user['uid'] != game_state["team1"]["user_id"] and
                (not game_state["team2"] or current_user['uid'] != game_state["team2"]["user_id"])):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this game"
            )

        # Get game history
        history = []
        history_refs = game_ref.collection(
            'history').order_by('timestamp').stream()
        for hist in history_refs:
            history.append(hist.to_dict())

        return {
            "game_id": game_id,
            "state": GameState(**game_state),
            "history": history
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving game: {str(e)}"
        )


@router.post("/{game_id}/forfeit")
async def forfeit_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Forfeit the current game"""
    try:
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )

        game_state = game.to_dict()

        if game_state["status"] != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400,
                detail="Game is not in progress"
            )

        # Verify user is part of this game
        if current_user['uid'] not in [game_state["team1"]["user_id"], game_state["team2"]["user_id"]]:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to forfeit this game"
            )

        # Update game state
        game_state["status"] = GameStatus.COMPLETED
        game_state["updated_at"] = datetime.utcnow()
        game_state["winner"] = game_state["team2"]["user_id"] if current_user[
            'uid'] == game_state["team1"]["user_id"] else game_state["team1"]["user_id"]

        # Save state
        game_ref.update(game_state)

        return GameState(**game_state)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error forfeiting game: {str(e)}"
        )
