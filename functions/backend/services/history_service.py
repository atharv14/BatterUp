from typing import Dict, List
from models.schemas.history import GameHistory, InningHistory, PlayerGameStats
from models.schemas.game import GameState, PlayResult
from datetime import datetime
from services.firebase import db


class HistoryService:
    @staticmethod
    async def record_play(
        game_id: str,
        game_state: Dict,
        play_result: PlayResult
    ):
        """Record a single play in game history"""
        try:
            history_ref = (
                db.collection('games')
                .document(game_id)
                .collection('history')
                .document()
            )

            play_data = {
                "timestamp": datetime.utcnow(),
                "inning": game_state["inning"],
                "is_top_inning": game_state["is_top_inning"],
                "batting_team": game_state["team1"]["user_id"] if game_state["is_top_inning"]
                else game_state["team2"]["user_id"],
                "pitching_team": game_state["team2"]["user_id"] if game_state["is_top_inning"]
                else game_state["team1"]["user_id"],
                "play_result": play_result.dict(),
                "game_state_after": game_state
            }

            history_ref.set(play_data)
        except Exception as e:
            print(f"Error recording single game play: {e}")
            raise

    @staticmethod
    async def complete_game(game_id: str, final_game_state: Dict):
        """Record completed game history"""
        try:
            # Get all plays from game history
            plays = (
                db.collection('games')
                .document(game_id)
                .collection('history')
                .order_by('timestamp')
                .stream()
            )

            # Compile inning-by-inning history
            innings: Dict[int, InningHistory] = {}
            player_stats: Dict[str, PlayerGameStats] = {}

            for play in plays:
                play_data = play.to_dict()
                inning_num = play_data["inning"]

                if inning_num not in innings:
                    innings[inning_num] = InningHistory(
                        inning_number=inning_num,
                        is_top_inning=play_data["is_top_inning"],
                        batting_team_id=play_data["batting_team"],
                        pitching_team_id=play_data["pitching_team"],
                        runs_scored=0,
                        hits=0,
                        errors=0,
                        plays=[]
                    )

                # Update inning statistics
                play_result = play_data["play_result"]
                current_inning = innings[inning_num]
                current_inning.plays.append(play_data)
                current_inning.runs_scored += play_result["runs_scored"]
                current_inning.hits += 1 if play_result["outcome"] != "out" else 0

                # Update player statistics
                # You would add detailed player stat updates here

            # Create final game history
            game_history = GameHistory(
                game_id=game_id,
                start_time=final_game_state["created_at"],
                end_time=datetime.utcnow(),
                team1_id=final_game_state["team1"]["user_id"],
                team2_id=final_game_state["team2"]["user_id"],
                final_score={
                    final_game_state["team1"]["user_id"]: final_game_state["team1"]["score"],
                    final_game_state["team2"]["user_id"]: final_game_state["team2"]["score"]
                },
                winner_id=final_game_state.get("winner"),
                status=final_game_state["status"],
                innings=list(innings.values()),
                player_stats=player_stats
            )

            # Save complete game history
            await db.collection('game_history').document(game_id).set(
                game_history.dict()
            )

        except Exception as e:
            print(f"Error recording game history: {e}")
            raise
