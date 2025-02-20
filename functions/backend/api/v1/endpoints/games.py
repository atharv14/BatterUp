from typing import List
from datetime import datetime, timedelta
import uuid
from firebase_admin import firestore
# from google.cloud.firestore_v1.base_query import FieldFilter, BaseQueryOption, Direction
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
import google.generativeai as genai
from google.cloud.firestore import FieldFilter
from models.schemas.game import (
    AtBatState, BaseState, CommentaryResponse, GameCreate, GameEvent, GameJoin, GameState, GameView, PitchOutcome, PlayAction,
    PlayResult, PlayState, TeamLineup, TeamState, HitType
)
from models.schemas.user import Deck
from models.schemas.base import GameStatus, PitchingStyle, HittingStyle
from services.audio_storage_service import AudioStorageService
from services.text_to_speech_service import audio_commentary_service
from services.game_service import GameService
from services.at_bat_service import AtBatService
from services.commentary_service import commentary_service
from services.base_running import BaseRunningService
from services.firebase import db
from services.history_service import HistoryService
from services.lineup_manager import LineupManager
from core.firebase_auth import get_current_user
from core.config import settings
from services.player_service import get_player_data

genai.configure(api_key=settings.GEMINI_KEY)

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
            "total_outs": 0,
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

        history_ref = db.collection('games').document(
            game_id).collection('commentary_history')
        history_ref.document().set({
            "full_commentary": [],
            "full_audio_url": [],
            "created_at": current_time
        })

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
        current_pitching_team_id = game_state["team2"] if game_state[
            "is_top_inning"] else game_state["team1"]
        if current_user['uid'] != current_pitching_team_id["user_id"]:
            raise HTTPException(
                status_code=400,
                detail="Not your turn to pitch"
            )

        # Get current pitching from lineup
        current_pitcher = current_pitching_team_id["lineup"]["available_pitchers"][
            current_pitching_team_id["lineup"]["current_pitcher_index"]]

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
        game_state["action_deadline"] = current_time + timedelta(seconds=100)
        game_state["updated_at"] = current_time

        # Fetch play history
        history_query = (
            game_ref.collection('history')
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .stream()
        )
        play_history = [hist.to_dict() for hist in history_query]

        # Fetch pitcher details
        pitcher_name = await commentary_service.fetch_player_name(current_pitcher)

        # Generate commentary
        game_context = {
            "inning": game_state["inning"],
            "is_top_inning": game_state["is_top_inning"],
            "score": {
                "team1": game_state["team1"]["score"],
                "team2": game_state["team2"]["score"]
            },
            "outs": game_state["outs"],
            "player_name": pitcher_name
        }
        action_details = {
            "pitch_style": pitch_style
        }

        commentary = await commentary_service.generate_ai_commentary(
            "pitch",
            action_details,
            game_context,
            play_history
        )

        # Save state
        game_ref.update(game_state)

        # Generate audio commentary
        audio_commentary = audio_commentary_service.generate_audio_commentary(
            commentary)

        # Upload audio to storage
        audio_url = await AudioStorageService.upload_audio_commentary(
            game_id,
            audio_commentary
        )

        # Record pitch action in game history
        history_ref = game_ref.collection('history').document()
        history_ref.set({
            "action_type": "pitch",
            "timestamp": current_time.isoformat(),
            "player_id": current_user['uid'],
            "pitch_style": pitch_style,
            "inning": game_state["inning"],
            "is_top_inning": game_state["is_top_inning"],
            "commentary": commentary,
            "audio_url": audio_url
        })

        # Fetch existing commentary history
        commentary_history_ref = game_ref.collection('commentary_history').document('main')
        commentary_history = commentary_history_ref.get()
        
        if not commentary_history.exists:
            full_commentary = []
        else:
            full_commentary = commentary_history.to_dict().get('full_commentary', [])

        # Append new commentary
        full_commentary.append({
            "timestamp": current_time.isoformat(),
            "commentary": commentary,
            "audio_url": audio_url,
            "action_type": "pitch",
            "details": action_details
        })

        # Truncate commentary history if needed
        if len(full_commentary) > 50:
            full_commentary = full_commentary[-50:]

        # Update commentary history
        commentary_history_ref.set({
            "full_commentary": full_commentary,
        })

        return {
            "game_state": GameState(**game_state),
            "commentary": commentary,
            "audio_url": audio_url,
            "full_commentary": full_commentary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing pitch: {str(e)}"
        )

# @router.post("/{game_id}/pitch")
# async def make_pitch(
#     game_id: str,
#     pitch_style: PitchingStyle,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Make a pitch with enhanced count system"""
#     try:
#         game_ref = db.collection('games').document(game_id)
#         game = game_ref.get()

#         if not game.exists:
#             raise HTTPException(status_code=404, detail="Game not found")

#         game_state = game.to_dict()

#         # Verify game status and user's turn
#         if game_state["status"] != GameStatus.IN_PROGRESS:
#             raise HTTPException(status_code=400, detail="Game is not in progress")

#         pitching_team = game_state["team2"] if game_state["is_top_inning"] else game_state["team1"]
#         if current_user['uid'] != pitching_team["user_id"]:
#             raise HTTPException(status_code=400, detail="Not your turn to pitch")

#         # Get current pitcher's abilities
#         current_pitcher = pitching_team["lineup"]["available_pitchers"][
#             pitching_team["lineup"]["current_pitcher_index"]
#         ]
#         pitcher_data = await get_player_data(current_pitcher)

#         # Get or create current at-bat state
#         if not game_state.get('play_state'):
#             game_state['play_state'] = PlayState().dict()

#         if not game_state['play_state'].get('current_at_bat'):
#             batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
#             current_batter = batting_team["lineup"]["batting_order"][
#                 batting_team["lineup"]["current_batter_index"]
#             ]
#             game_state['play_state']['current_at_bat'] = AtBatState(
#                 batter_id=current_batter,
#                 pitcher_id=current_pitcher
#             ).dict()

#         # Resolve pitch
#         pitch_outcome = AtBatService.resolve_pitch(
#             pitch_style,
#             pitcher_data['pitching_abilities']
#         )

#         # Update count and check resolution
#         at_bat = AtBatState(**game_state['play_state']['current_at_bat'])
#         at_bat, is_resolved, result = AtBatService.update_count(at_bat, pitch_outcome)

#         if is_resolved:
#             if result == "walk":
#                 game_state = AtBatService.handle_walk(
#                     game_state,
#                     at_bat.batter_id
#                 )
#                 game_state['outs'] += 1
#             elif result == "strikeout":
#                 game_state['outs'] += 1

#             # Reset at-bat state
#             game_state['play_state']['current_at_bat'] = None

#             # Check if half-inning is over
#             if game_state['outs'] >= 3:
#                 game_state = GameService.handle_inning_change(game_state)
#         else:
#             # Update at-bat state for next pitch/bat
#             game_state['play_state']['current_at_bat'] = at_bat.dict()
#             game_state['play_state']['last_pitch_style'] = pitch_style
#             game_state['play_state']['last_pitch_outcome'] = pitch_outcome

#         # Update game state
#         game_state["updated_at"] = datetime.utcnow().isoformat()
#         game_ref.update(game_state)

#         return {
#             "game_state": game_state,
#             "pitch_outcome": pitch_outcome,
#             "at_bat_state": at_bat.dict() if not is_resolved else None,
#             "resolution": result if is_resolved else None
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing pitch: {str(e)}"
#         )


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

        # Fetch batter details
        batter_name = await commentary_service.fetch_player_name(current_batter)

        # Process the at-bat
        result = process_at_bat(game_state, current_batter, hit_style)

        # Update game state
        updated_state = await GameService.update_game_state(game_state, result)

        # Fetch play history
        history_query = (
            game_ref.collection('history')
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .stream()
        )
        play_history = [hist.to_dict() for hist in history_query]

        # Generate commentary
        game_context = {
            "inning": updated_state["inning"],
            "is_top_inning": updated_state["is_top_inning"],
            "score": {
                "team1": updated_state["team1"]["score"],
                "team2": updated_state["team2"]["score"]
            },
            "outs": updated_state["outs"],
            "player_name": batter_name,
        }

        commentary = await commentary_service.generate_ai_commentary(
            "bat",
            result.dict(),
            game_context,
            play_history
        )

        # Update in Firestore
        game_ref.update(updated_state)

        # Generate audio commentary
        audio_commentary = audio_commentary_service.generate_audio_commentary(
            commentary)

        # Upload audio to storage
        audio_url = await AudioStorageService.upload_audio_commentary(
            game_id,
            audio_commentary
        )

        # Record bat action in game history
        current_time = datetime.utcnow()
        history_ref = game_ref.collection('history').document()
        history_ref.set({
            "action_type": "bat",
            "timestamp": current_time.isoformat(),
            "player_id": current_user['uid'],
            "hit_style": hit_style,
            "inning": updated_state["inning"],
            "is_top_inning": updated_state["is_top_inning"],
            "play_result": result.dict(),
            "commentary": commentary
        })

        # Fetch existing commentary history
        commentary_history_ref = game_ref.collection(
            'commentary_history').document('main')
        commentary_history = commentary_history_ref.get()

        if not commentary_history.exists:
            # Initialize if not exists
            full_commentary = []
        else:
            full_commentary = commentary_history.to_dict().get('full_commentary', [])

        # Append new commentary
        full_commentary.append({
            "timestamp": current_time.isoformat(),
            "commentary": commentary,
            "audio_url": audio_url,
            "action_type": "bat",
            "details": result.dict()
        })

        # Truncate commentary history if needed
        if len(full_commentary) > 50:
            full_commentary = full_commentary[-50:]

        # Update commentary history
        commentary_history_ref.set({
            "full_commentary": full_commentary,
        })

        return {
            "game_state": updated_state,
            "result": result,
            "commentary": commentary,
            "audio_url": audio_url,
            "full_commentary": full_commentary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing bat: {str(e)}"
        )


# @router.post("/{game_id}/bat")
# async def make_bat(
#     game_id: str,
#     hit_style: HittingStyle,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Handle batting with enhanced stat-based outcomes"""
#     try:
#         game_ref = db.collection('games').document(game_id)
#         game = game_ref.get()

#         if not game.exists:
#             raise HTTPException(status_code=404, detail="Game not found")

#         game_state = game.to_dict()

#         # Validate game status
#         if game_state["status"] != GameStatus.IN_PROGRESS:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Game is not in progress"
#             )

#         # Verify it's batter's turn and right user
#         batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
#         if current_user['uid'] != batting_team["user_id"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Not your turn to bat"
#             )

#         # Get current batter
#         current_batter = batting_team["lineup"]["batting_order"][
#             batting_team["lineup"]["current_batter_index"]
#         ]

#         # Process the at-bat
#         result = await GameService.process_at_bat(game_state, current_batter, hit_style)

#         # Handle outcome
#         if result.outcome != "out":
#             # Update bases and score
#             batting_team['score'] += result.batting_team_runs
#             batting_team['hits'] += 1

#             # Update bases from advancements
#             game_state['bases'] = {
#                 base: runner.player_id if runner else None
#                 for base, runner in zip(['first', 'second', 'third'], result.advancements)
#             } if result.advancements else {}
#         else:
#             # Handle out
#             game_state['outs'] += 1

#         # Check for inning change
#         if game_state['outs'] >= 3:
#             game_state = GameService.handle_inning_change(game_state)
#         else:
#             # Advance to next batter
#             batting_team["lineup"]["current_batter_index"] = (
#                 batting_team["lineup"]["current_batter_index"] + 1
#             ) % len(batting_team["lineup"]["batting_order"])

#         # Reset last action
#         game_state["last_action"] = None

#         # Update timestamp
#         game_state["updated_at"] = datetime.utcnow().isoformat()

#         # Update game state in database
#         game_ref.update(game_state)

#         # Prepare response
#         next_batter = None
#         if game_state["status"] != GameStatus.COMPLETED:
#             next_batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
#             next_batter = next_batting_team["lineup"]["batting_order"][
#                 next_batting_team["lineup"]["current_batter_index"]
#             ]

#         return {
#             "game_state": game_state,
#             "play_result": {
#                 "outcome": result.outcome,
#                 "description": result.description,
#                 "runs_scored": result.runs_scored,
#                 "advancements": result.advancements
#             },
#             "next_batter": next_batter
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error processing bat: {str(e)}"
#         )

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

        outcomes = [
            (HitType.HOME_RUN, "Home run! Ball went over the fence!", 1),
            (HitType.TRIPLE, "Triple! Ball hit deep into the outfield!", 0),
            (HitType.DOUBLE, "Double! Ball hit into the gap!", 0),
            (HitType.SINGLE, "Single! Ball hit into the outfield!", 0),
            (HitType.OUT, "Out! Ball caught by fielder.", 0)
        ]

        weights = [0.1, 0.1, 0.2, 0.3, 0.3]  # Probabilities for each outcome
        outcome, description, error = random.choices(
            outcomes, weights=weights)[0]

        # Hit and score calculation
        hit_result = GameService.calculate_hits_and_score(outcome)

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
                batting_team_runs=hit_result['score_increment'],
                hits=hit_result['hits']
            )

        return PlayResult(
            outcome=outcome,
            description=description,
            advancements=[],
            runs_scored=0,
            batting_team_runs=0,
            hits=0,
            hit_type=HitType.OUT
        )

    except Exception as e:
        raise Exception(f"Error in process_at_bat: {str(e)}")


async def update_game_state(game_state: dict, result: PlayResult) -> dict:
    """Update game state based on play result"""
    # global TOTAL_OUTS
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
            game_state["total_outs"] += game_state["outs"]
            # TOTAL_OUTS += game_state["outs"]
            game_state["outs"] = 0
            game_state["is_top_inning"] = not game_state["is_top_inning"]
            game_state["bases"] = BaseState().dict()

            # Increment inning after every 6 outs (full inning)
            if game_state["total_outs"] % 6 == 0:
                # if TOTAL_OUTS % 6 == 0:
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
        current_time + timedelta(seconds=30)).isoformat()

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
                (not game_state.get("team2") or current_user['uid'] != game_state["team2"]["user_id"])):
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
                # Sanitize event type to match allowed values
                event_type = play_data.get('event', '')
                if event_type not in ['game_created', 'player_joined', 'forfeit']:
                    event_type = 'forfeit'  # Default to forfeit if not matching
                    # This is a game event
                    history.append({
                        "entry_type": "event",
                        "data": GameEvent(
                            event_type=play_data.get('event', ''),
                            timestamp=play_data.get('timestamp', ''),
                            player_id=play_data.get('player_id', ''),
                            event_data=play_data
                        )
                    })
            elif 'play_result' in play_data or 'action_type' in play_data:
                # This is a play action
                # Determine batting and pitching teams based on game state
                is_top_inning = game_state.get('is_top_inning', True)
                batting_team = "team1" if is_top_inning else "team2"
                pitching_team = "team2" if is_top_inning else "team1"

                history.append({
                    "entry_type": "play",
                    "data": PlayAction(
                        inning=play_data.get(
                            'inning', game_state.get('inning', 1)),
                        is_top_inning=is_top_inning,
                        batting_team=batting_team,
                        pitching_team=pitching_team,
                        action={
                            "type": play_data.get('action_type', ''),
                            "player_id": play_data.get('player_id', ''),
                            "style": play_data.get('pitch_style') or play_data.get('hit_style', '')
                        },
                        result=play_data.get('play_result', {}),
                        timestamp=play_data.get('timestamp', ''),
                        play_data=play_data
                    )
                })

        # Get commentary history if it exists
        commentary_history = []
        try:
            commentary_ref = game_ref.collection(
                'commentary_history').document('main')
            commentary_doc = commentary_ref.get()
            if commentary_doc.exists:
                commentary_data = commentary_doc.to_dict()
                full_commentary = commentary_data.get('full_commentary', [])

                # Convert to format with audio URLs
                commentary_history = {
                    'text_commentaries': [entry.get('commentary') for entry in full_commentary],
                    'audio_urls': [entry.get('audio_url') for entry in full_commentary]
                }

        except Exception:
            # If commentary history doesn't exist or can't be retrieved, ignore
            pass

        # Compile current game view
        game_view = {
            "game_id": game_id,
            "state": GameState(**game_state),
            "history": history,
            "commentary_history": commentary_history
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
            raise HTTPException(status_code=404, detail="Game not found")

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

        # Record which team forfeited
        forfeiting_team = "team1" if current_user['uid'] == game_state["team1"]["user_id"] else "team2"
        winning_team = "team2" if forfeiting_team == "team1" else "team1"

        current_time = datetime.utcnow()

        # Record forfeit in history
        history_ref = game_ref.collection('history').document()
        history_ref.set({
            "event": "forfeit",
            "timestamp": current_time.isoformat(),
            "forfeiting_team": forfeiting_team,
            "forfeiting_user_id": current_user['uid']
        })

        # Update game state
        game_state.update({
            "status": GameStatus.COMPLETED,
            "winner": game_state[winning_team]["user_id"],
            "forfeit_info": {
                "forfeiting_team": forfeiting_team,
                "forfeiting_user_id": current_user['uid'],
                "timestamp": current_time.isoformat()
            },
            "updated_at": current_time.isoformat()
        })

        # Save state
        game_ref.update(game_state)

        # Optional: Clean up audio commentaries for this game
        try:
            await AudioStorageService.cleanup_old_audio_files(game_id)
        except Exception as cleanup_error:
            print(f"Error cleaning up audio files: {cleanup_error}")

        return game_state

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


@router.get("/{game_id}/commentary", response_model=CommentaryResponse)
async def get_game_commentary(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get game commentary based on game history"""
    try:
        # Verify game exists and user is authorized
        game_ref = db.collection('games').document(game_id)
        game = game_ref.get()

        if not game.exists:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.to_dict()

        # Verify user authorization
        if (current_user['uid'] != game_state["team1"]["user_id"] and
                (not game_state["team2"] or current_user['uid'] != game_state["team2"]["user_id"])):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Fetch commentary history
        commentary_history_ref = game_ref.collection(
            'commentary_history').document('main')
        commentary_history = commentary_history_ref.get()

        if not commentary_history.exists:
            return CommentaryResponse(
                game_id=game_id,
                status=game_state["status"],
                commentaries=[],
                audio_commentaries=[],
                latest_commentary="No commentary available.",
                latest_audio_commentary=None,
                play_data=None
            )

        full_commentary = commentary_history.to_dict().get('full_commentary', [])

        # Extract non-None audio URLs
        audio_urls = [
            entry.get('audio_url') or '' 
            for entry in full_commentary
        ]

        return CommentaryResponse(
            game_id=game_id,
            status=game_state["status"],
            commentaries=[entry['commentary'] for entry in full_commentary],
            audio_commentaries=audio_urls,
            latest_commentary=full_commentary[-1].get('commentary', '') if full_commentary else "No commentary available.",
            latest_audio_commentary=full_commentary[-1].get('audio_url') or None if full_commentary else None,
            play_data=full_commentary[-1] if full_commentary else None
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating commentary: {str(e)}"
        )
