from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import random
from models.schemas.game import BaseState, HitType, PlayResult, PlayState
from models.schemas.base import GameStatus, HittingStyle
from services.base_running import BaseRunningService
from services.history_service import HistoryService
from services.player_service import get_player_data

class GameService:
    """
    Service to update game change
    """
    @staticmethod
    def calculate_hits_and_score(outcome: str) -> Dict[str, int]:
        """
        Calculate hits and potential score based on hit type
        
        Rules:
        - Single: 1 hit
        - Double: 2 hits
        - Triple: 3 hits
        - Home Run: 4 hits = 1 score
        - 4 total hits = 1 score
        """
        hit_type_map = {
            "single": HitType.SINGLE,
            "double": HitType.DOUBLE,
            "triple": HitType.TRIPLE,
            "home_run": HitType.HOME_RUN,
            "out": HitType.OUT
        }
        
        result = {
            "hits": 0,
            "score_increment": 0,
            "hit_type": hit_type_map.get(outcome, HitType.OUT)
        }
        
        if outcome in ["single", "double", "triple", "home_run"]:
            result["hits"] = {
                "single": 1,
                "double": 2,
                "triple": 3,
                "home_run": 4
            }[outcome]
        
        # Score increment logic
        if outcome == "home_run":
            result["score_increment"] = 1
        
        return result
    
    @staticmethod
    async def update_game_state(game_state: dict, result: PlayResult) -> dict:
        """Update game state based on play result"""
        current_time = datetime.utcnow()

        # Update batting team's stats
        batting_team = game_state["team1"] if game_state["is_top_inning"] else game_state["team2"]
        
        if result.outcome != "out":
            # Accumulate hits
            batting_team["hits"] += result.hits
            
            # Score increment logic
            # Every 4 hits or home run
            if batting_team["hits"] >= 4:
                batting_team["score"] += 1
                batting_team["hits"] = batting_team["hits"] % 4
            
            # Direct score from home run or other increments
            batting_team["score"] += result.batting_team_runs

        # Outs and inning change logic
        if result.outcome == "out":
            game_state["outs"] += 1
            game_state["total_outs"] += 1

        # Inning change logic
        if game_state["outs"] >= 3:
            game_state["outs"] = 0
            game_state["is_top_inning"] = not game_state["is_top_inning"]
            game_state["bases"] = BaseState().dict()

            # Increment inning after every 6 outs (full inning)
            if game_state["total_outs"] % 6 == 0:
                game_state["inning"] += 1

        # Game completion logic
        if game_state["inning"] > 9:
            # Ensure a full 9 innings are played
            if not game_state["is_top_inning"]:
                # Compare scores after bottom of 9th
                if game_state["team1"]["score"] != game_state["team2"]["score"]:
                    game_state["status"] = GameStatus.COMPLETED
                    game_state["winner"] = (
                        game_state["team1"]["user_id"]
                        if game_state["team1"]["score"] > game_state["team2"]["score"]
                        else game_state["team2"]["user_id"]
                    )
                    # Record complete game history
                    await HistoryService.complete_game(game_state["game_id"], game_state)

        # Update bases if there was a hit
        if result.outcome != "out":
            game_state["bases"] = result.advancements[0].dict() if result.advancements else {}

        # Set up next action
        game_state["last_action"] = None
        game_state["action_deadline"] = (
            current_time + timedelta(seconds=30)).isoformat()

        # Update batting order
        batting_team["lineup"]["current_batter_index"] = (
            batting_team["lineup"]["current_batter_index"] + 1
        ) % len(batting_team["lineup"]["batting_order"])

        game_state["updated_at"] = current_time.isoformat()
        return game_state

    @staticmethod
    def handle_inning_change(game_state: Dict) -> Dict:
        """
        Handle transition between innings:
        - Reset outs
        - Switch batting teams
        - Update inning number
        - Clear bases
        - Reset play state
        """
        try:
            # Reset outs and bases
            game_state['outs'] = 0
            game_state['bases'] = {
                "first": None,
                "second": None,
                "third": None
            }

            # Reset play state
            game_state['play_state'] = PlayState().dict()

            # Switch batting teams
            game_state['is_top_inning'] = not game_state['is_top_inning']

            # If bottom inning ends, increment inning number
            if not game_state['is_top_inning']:
                game_state['inning'] += 1

            # Check if game should end (after 9 innings or more)
            if game_state['inning'] > 9:
                team1_score = game_state['team1']['score']
                team2_score = game_state['team2']['score']

                # Game ends if:
                # 1. Bottom of 9th or later, home team is ahead
                # 2. Bottom of 9th or later, game is not tied
                if (not game_state['is_top_inning'] and team1_score != team2_score):
                    game_state['status'] = GameStatus.COMPLETED
                    game_state['winner'] = (
                        game_state['team1']['user_id']
                        if team1_score > team2_score
                        else game_state['team2']['user_id']
                    )

            return game_state

        except Exception as e:
            raise Exception(f"Error in handle_inning_change: {str(e)}")

    @staticmethod
    async def process_at_bat(game_state: dict, batter_id: str, hit_style: HittingStyle) -> PlayResult:
        """Process a batting attempt and return the result using player abilities"""
        try:
            # Get current pitcher's data
            pitching_team = game_state["team2"] if game_state["is_top_inning"] else game_state["team1"]
            current_pitcher = pitching_team["lineup"]["available_pitchers"][pitching_team["lineup"]["current_pitcher_index"]]
            pitcher_data = await get_player_data(current_pitcher)

            # Get batter's data
            batter_data = await get_player_data(batter_id)

            # Get last pitch style
            last_action = game_state.get("play_state", {})
            pitch_style = last_action.get("last_pitch_style") if last_action else None

            if not pitch_style:
                raise ValueError("No pitch action found")

            # Calculate outcome probabilities based on abilities
            batter_contact = batter_data['batting_abilities']['contact'] / 100
            batter_power = batter_data['batting_abilities']['power'] / 100
            pitcher_effectiveness = pitcher_data['pitching_abilities']['effectiveness'] / 100
            pitcher_control = pitcher_data['pitching_abilities']['control'] / 100

            # Base probabilities adjusted by player stats
            hit_chance = batter_contact * (1 - pitcher_effectiveness)
            power_hit_chance = batter_power * (1 - pitcher_control)

            # Adjust based on pitch and hit styles
            if pitch_style == "Fastballs":
                if hit_style == HittingStyle.POWER:
                    power_hit_chance *= 1.2  # Power hitters better against fastballs
                hit_chance *= 0.9  # Harder to contact fastballs
            elif pitch_style == "Breaking_Balls":
                if hit_style == HittingStyle.DESIGNATED:
                    hit_chance *= 1.1  # Designated hitters better against breaking balls
                power_hit_chance *= 0.9  # Less power on breaking balls
            elif pitch_style == "Changeups":
                if hit_style == HittingStyle.SWITCH:
                    hit_chance *= 1.1  # Switch hitters adapt better to changeups

            # Determine outcome based on adjusted probabilities
            import random
            roll = random.random()
            print(roll)
            print(hit_chance)

            if roll < hit_chance:
                outcome = "out"
                description = "Out! Ball caught by fielder."
            else:
                # If it's a hit, determine type based on power
                power_roll = random.random()
                if power_roll < power_hit_chance * 0.2:
                    outcome = "home_run"
                    description = "Home run! Ball went over the fence!"
                elif power_roll < power_hit_chance * 0.4:
                    outcome = "triple"
                    description = "Triple! Ball hit deep into the outfield!"
                elif power_roll < power_hit_chance * 0.6:
                    outcome = "double"
                    description = "Double! Ball hit into the gap!"
                else:
                    outcome = "single"
                    description = "Single! Ball hit into the outfield!"

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


# class BaseRunnerService:
#     """
#     Service to handle base running

#     Returns:
#         Tuple: New bases with first, second and third as first param and runs scored as second param
#     """
#     @staticmethod
#     def advance_runners(
#         bases: Dict[str, Optional[str]],
#         hit_type: str,
#         batter_id: str
#     ) -> Tuple[Dict[str, Optional[str]], int]:
#         """
#         Advance runners based on hit type
#         Returns: (new_bases, runs_scored)
#         """
#         new_bases: Dict[str, Optional[str]] = {
#             "first": None,
#             "second": None,
#             "third": None
#         }
#         runs_scored = 0

#         if hit_type == "home_run":
#             # Score all runners and batter
#             runs_scored = 1  # Batter
#             for base in bases.values():
#                 if base is not None:
#                     runs_scored += 1
#             # All bases empty after home run
#             return new_bases, runs_scored

#         elif hit_type == "triple":
#             # Score all runners
#             for base in bases.values():
#                 if base is not None:
#                     runs_scored += 1
#             # Place batter on third
#             new_bases["third"] = batter_id

#         elif hit_type == "double":
#             # Score from second and third
#             if bases["third"]:
#                 runs_scored += 1
#             if bases["second"]:
#                 runs_scored += 1
#             if bases["first"]:
#                 new_bases["third"] = bases["first"]
#             # Place batter on second
#             new_bases["second"] = batter_id

#         elif hit_type == "single":
#             # Score from third
#             if bases["third"]:
#                 runs_scored += 1
#             # Advance from second to third
#             if bases["second"]:
#                 new_bases["third"] = bases["second"]
#             # Advance from first to second
#             if bases["first"]:
#                 new_bases["second"] = bases["first"]
#             # Place batter on first
#             new_bases["first"] = batter_id

#         return new_bases, runs_scored
