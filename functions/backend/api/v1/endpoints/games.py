from fastapi import APIRouter, HTTPException, Depends, status
from models.schemas.game import (
    BaseState, GameCreate, GameEvent, GameJoin, GameState, GameView, PlayAction,
    PlayResult, TeamLineup, TeamState
)
from models.schemas.base import GameStatus, PitchingStyle, HittingStyle
from core.firebase_auth import get_current_user
from models.schemas.user import Deck
from services.base_running import BaseRunningService
from services.firebase import db
from datetime import datetime, timedelta
import uuid

from services.history_service import HistoryService
from services.lineup_manager import LineupManager

router = APIRouter()


@router.post("/create", response_model=GameView)
async def create_game(
    game_data: GameCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new game session"""
    try:
        # Validate user
        if current_user['uid'] != game_data.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can only create game for yourself"
            )

        # Validate deck composition
        validate_deck_composition(game_data.deck)

        game_id = str(uuid.uuid4())
        current_time = datetime.utcnow()

        # Initialize team lineup
        team1_lineup = LineupManager.initialize_lineup(game_data.deck.dict())

        # Initialize bases
        initial_bases = BaseState().dict()

        # Initialize first team state
        team1_state = TeamState(
            user_id=game_data.user_id,
            deck=game_data.deck,
            lineup=team1_lineup,
            score=0,
            hits=0,
            errors=0,
            player_stats={}
        ).dict()

        # Create initial game state
        game_state = {
            "game_id": game_id,
            "status": GameStatus.WAITING,
            "inning": 1,
            "is_top_inning": True,
            "outs": 0,
            "bases": initial_bases,
            "team1": team1_state,
            "team2": None,
            "last_action": None,
            "action_deadline": None,
            "created_at": current_time,
            "updated_at": current_time
        }

        # Store in Firestore
        db.collection('games').document(game_id).set(game_state)

        # Initialize game history collection
        history_ref = db.collection('games').document(
            game_id).collection('history')
        history_ref.document().set({
            "event": "game_created",
            "timestamp": current_time,
            "player_id": game_data.user_id,
            "event_data": {
                "creator_id": game_data.user_id
            }
        })

        return GameView(
            game_id=game_id,
            state=GameState(**game_state),
            history=[]
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
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
        # Validate user
        if current_user['uid'] != join_data.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can only join game for yourself"
            )

        # Validate deck composition
        validate_deck_composition(join_data.deck)

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

        if game_state["team1"]["user_id"] == join_data.user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot join your own game"
            )

        # Initialize team lineup for second team
        team2_lineup = LineupManager.initialize_lineup(join_data.deck.dict())

        # Initialize second team state
        team2_state = TeamState(
            user_id=join_data.user_id,
            deck=join_data.deck,
            lineup=team2_lineup,
            score=0,
            hits=0,
            errors=0,
            player_stats={}
        ).dict()

        # Update game state
        current_time = datetime.utcnow()
        update_data = {
            "team2": team2_state,
            "status": GameStatus.IN_PROGRESS,
            "updated_at": current_time,
            "last_action": None,
            "action_deadline": current_time + timedelta(seconds=5)
        }

        # Update in Firestore
        game_ref.update(update_data)

        # Update game state for response
        game_state.update(update_data)

        # Record join event in history
        history_ref = game_ref.collection('history')
        history_ref.document().set({
            "event": "player_joined",
            "timestamp": current_time,
            "player_id": join_data.user_id,
            "event_data": {
                "joiner_id": join_data.user_id
            }
        })

        return GameView(
            game_id=game_id,
            state=GameState(**game_state),
            history=[]
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error joining game: {str(e)}"
        )


def validate_deck_composition(deck: Deck):
    """Validate deck follows required composition rules"""
    if len(deck.catchers) != 1:
        raise ValueError("Deck must contain exactly 1 catcher")
    if len(deck.pitchers) != 5:
        raise ValueError("Deck must contain exactly 5 pitchers")
    if len(deck.infielders) != 4:
        raise ValueError("Deck must contain exactly 4 infielders")
    if len(deck.outfielders) != 3:
        raise ValueError("Deck must contain exactly 3 outfielders")
    if len(deck.hitters) != 4:
        raise ValueError("Deck must contain exactly 4 hitters")

    # Check for duplicates across all positions
    all_players = (
        deck.catchers + deck.pitchers +
        deck.infielders + deck.outfielders +
        deck.hitters
    )
    if len(set(all_players)) != len(all_players):
        raise ValueError("Deck contains duplicate players")


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


@router.post("/{game_id}/change-pitcher")
async def change_pitcher(
    game_id: str,
    new_pitcher_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Change current pitcher"""
    try:
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.to_dict()

        # Determine which team is pitching
        pitching_team_key = "team2" if game_state["is_top_inning"] else "team1"
        pitching_team = game_state[pitching_team_key]

        if current_user['uid'] != pitching_team["user_id"]:
            raise HTTPException(
                status_code=403, detail="Not your team's turn to pitch")

        # Convert dictionary to TeamState for lineup management
        pitching_team_lineup = TeamLineup(**pitching_team["lineup"])

        # Validate and perform pitcher change
        success, message = LineupManager.change_pitcher(
            pitching_team_lineup, new_pitcher_id)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Update game state with new lineup
        pitching_team["lineup"] = pitching_team_lineup.dict()
        game_state[pitching_team_key] = pitching_team

        game_state["updated_at"] = datetime.utcnow().isoformat()

        # Update in Firestore
        game_ref.update(game_state)

        return {
            "message": "Pitcher changed successfully",
            "new_pitcher_id": new_pitcher_id
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error changing pitcher: {str(e)}"
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
        batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
        if current_user['uid'] != batting_team["user_id"]:
            raise HTTPException(
                status_code=400,
                detail="Not your turn to bat"
            )

        # Get current batter from lineup
        current_batter = batting_team["lineup"]["batting_order"][batting_team["lineup"]
                                                                 ["current_batter_index"]]

        # Process the at-bat
        result = process_at_bat(game_state, current_batter, hit_style)

        # Update game state
        updated_state = await update_game_state(game_state, result)

        # Update in Firestore
        game_ref.update(updated_state)

        return {
            "game_state": updated_state,
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing bat: {str(e)}"
        )


def process_at_bat(game_state: dict, batter_id: str, hit_style: HittingStyle) -> PlayResult:
    """Process a batting attempt and return the result"""
    try:
        # Get current pitcher's data
        pitching_team = game_state["team2"] if game_state["is_top_inning"] else game_state["team1"]
        current_pitcher = pitching_team["lineup"]["available_pitchers"][pitching_team["lineup"]
                                                                        ["current_pitcher_index"]]

        # Get last pitch style
        last_action = game_state.get("last_action", {})
        pitch_style = last_action.get(
            "selected_style") if last_action else None

        if not pitch_style:
            raise ValueError("No pitch action found")

        # Calculate outcome probabilities based on abilities
        import random

        # # Get current batter ID
        # current_batter_id = (
        #     game_state["team1"]["current_batter"]
        #     if game_state["is_top_inning"]
        #     else game_state["team2"]["current_batter"]
        # )

        outcomes = [
            ("home_run", "Home run! Ball went over the fence!", 1),
            ("triple", "Triple! Ball hit deep into the outfield!", 0),
            ("double", "Double! Ball hit into the gap!", 0),
            ("single", "Single! Ball hit into the outfield!", 0),
            ("out", "Out! Ball caught by fielder.", 0)
        ]

        weights = [0.1, 0.1, 0.2, 0.3, 0.3]  # Probabilities for each outcome
        outcome, description, error = random.choices(
            outcomes, weights=weights)[0]

        # Process base running if it's a hit
        if outcome != "out":
            current_bases = BaseState(**game_state.get("bases", {}))
            new_bases, advancements, runs_scored = BaseRunningService.advance_runners(
                current_bases,
                batter_id,
                outcome
            )

            return PlayResult(
                outcome=outcome,
                description=description,
                advancements=advancements,
                runs_scored=runs_scored,
                batting_team_runs=runs_scored
            )

        return PlayResult(
            outcome=outcome,
            description=description,
            advancements=[],
            runs_scored=0,
            batting_team_runs=0
        )

    except Exception as e:
        raise Exception(f"Error in process_at_bat: {str(e)}")


TOTAL_OUTS = 0


async def update_game_state(game_state: dict, result: PlayResult) -> dict:
    """Update game state based on play result"""
    global TOTAL_OUTS
    current_time = datetime.utcnow()

    # Update batting team's stats
    batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
    if result.outcome != "out":
        batting_team["hits"] += 1

    # Get current pitching team
    pitching_team = game_state["team2"] if game_state["is_top_inning"] else game_state["team1"]

    # Update outs and inning state
    if result.outcome == "out":
        game_state["outs"] += 1

        if game_state["outs"] >= 3:
            # Half-inning is over
            # game_state["total_outs"] += game_state["outs"]
            TOTAL_OUTS += game_state["outs"]
            game_state["outs"] = 0
            game_state["is_top_inning"] = not game_state["is_top_inning"]
            game_state["bases"] = BaseState().dict()

            # Increment inning after every 6 outs (full inning)
            # if game_state["total_outs"] % 6 == 0:
            if TOTAL_OUTS % 6 == 0:
                game_state["inning"] += 1

            # Update pitching team for next half-inning
            pitching_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]

    # Update batting order
    batting_team["lineup"]["current_batter_index"] = (
        batting_team["lineup"]["current_batter_index"] + 1
    ) % len(batting_team["lineup"]["batting_order"])

    # Set up next action
    game_state["last_action"] = None
    game_state["action_deadline"] = (
        current_time + timedelta(seconds=5)).isoformat()

    # Update bases if there was a hit
    if result.outcome != "out":
        game_state["bases"] = result.advancements[0].dict(
        ) if result.advancements else {}

    # Check if game should end
    if game_state["inning"] > 9 and not game_state["is_top_inning"]:
        if game_state["team1"]["score"] != game_state["team2"]["score"]:
            game_state["status"] = GameStatus.COMPLETED
            game_state["winner"] = (
                game_state["team1"]["user_id"]
                if game_state["team1"]["score"] > game_state["team2"]["score"]
                else game_state["team2"]["user_id"]
            )
            # Record complete game history
            await HistoryService.complete_game(game_state["game_id"], game_state)

    game_state["updated_at"] = current_time.isoformat()
    return game_state


@router.get("/{game_id}", response_model=GameView)
async def get_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current game state and history"""
    try:
        # Get game document
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
        history_refs = (
            game_ref.collection('history')
            .order_by('timestamp')
            .stream()
        )

        for hist in history_refs:
            play_data = hist.to_dict()

            # Determine if this is a game event or play action
            if 'event' in play_data:
                # This is a game event
                history.append({
                    "entry_type": "event",
                    "data": GameEvent(
                        event_type=play_data['event'],
                        timestamp=play_data['timestamp'],
                        player_id=play_data.get('player_id'),
                        event_data=play_data
                    )
                })
            elif 'play_result' in play_data:
                # This is a play action
                history.append({
                    "entry_type": "play",
                    "data": PlayAction(
                        inning=play_data['inning'],
                        is_top_inning=play_data['is_top_inning'],
                        batting_team=play_data['batting_team'],
                        pitching_team=play_data['pitching_team'],
                        action={
                            "type": play_data.get('action_type'),
                            "player_id": play_data.get('player_id'),
                            "style": play_data.get('selected_style')
                        },
                        result=play_data['play_result'],
                        timestamp=play_data['timestamp'],
                        play_data=play_data
                    )
                })

        # Compile current game view
        game_view = {
            "game_id": game_id,
            "state": GameState(**game_state),
            "history": history
        }

        return game_view

    except HTTPException as he:
        raise he
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


@router.get("/{game_id}/history")
async def get_game_history(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get complete history of a game"""
    try:
        # Get game history
        history_ref = db.collection('game_history').document(game_id)
        history = history_ref.get()
        winner = db.collection('games').document(game_id)

        if not history.exists:
            # Try getting in-progress game history
            plays = (
                db.collection('games')
                .document(game_id)
                .collection('history')
                .order_by('timestamp')
                .stream()
            )

            return {
                "game_id": game_id,
                "status": GameStatus.COMPLETED,
                "plays": [play.to_dict() for play in plays],
                # "winner": winner["winner"]
            }

        return history.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving game history: {str(e)}"
        )
    
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_KEY"])

@router.get("/{game_id}/commentary")
async def get_game_commentary(
    game_id: str,
    game_action: str,
):
    """Get complete history of a game and new commentary on the latest action"""
    try:
        # Get game history
        history_ref = db.collection('game_commentary').document(game_id)
        history = history_ref.get()

        previous_commentaries = []
        if history.exists:
            previous_commentaries = history.to_dict().get("commentaries", [])
        else:
            # Try getting in-progress game history
            plays = (
                db.collection('games')
                .document(game_id)
                .collection('history')
                .order_by('timestamp')
                .stream()
            )
            previous_commentaries = [play.to_dict() for play in plays]

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Previous commentaries: {previous_commentaries}. New action: {game_action}"
        response = model.generate_content(prompt)
        new_commentary = response.text

        updated_commentaries = previous_commentaries + [new_commentary]
        history_ref.set({"commentaries": updated_commentaries}, merge=True)

        return {
            "game_id": game_id,
            "status": GameStatus.COMPLETED if history.exists else GameStatus.IN_PROGRESS,
            "commentaries": updated_commentaries
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving game history: {str(e)}"
        )