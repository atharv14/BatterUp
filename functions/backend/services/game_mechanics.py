from typing import Dict, Tuple
import random
from models.schemas.game import PitchingStyle, HittingStyle

class GameMechanics:
    @staticmethod
    def calculate_hit_probability(pitcher_data: Dict, batter_data: Dict, 
                                pitch_style: PitchingStyle, hit_style: HittingStyle) -> Tuple[str, float]:
        # Base probabilities
        outcomes = {
            "strike": 0.3,
            "ball": 0.3,
            "hit": {
                "single": 0.2,
                "double": 0.1,
                "triple": 0.05,
                "home_run": 0.05
            }
        }

        # Pitcher influence
        pitcher_effectiveness = (
            pitcher_data["pitching_abilities"]["control"] * 0.4 +
            pitcher_data["pitching_abilities"]["velocity"] * 0.3 +
            pitcher_data["pitching_abilities"]["effectiveness"] * 0.3
        ) / 100

        # Batter influence
        batter_effectiveness = (
            batter_data["batting_abilities"]["contact"] * 0.4 +
            batter_data["batting_abilities"]["power"] * 0.3 +
            batter_data["batting_abilities"]["discipline"] * 0.3
        ) / 100

        # Style matchup adjustments
        style_multiplier = GameMechanics._calculate_style_matchup(
            pitch_style, hit_style)

        # Final probability calculation
        hit_chance = (
            batter_effectiveness * 0.6 +
            (1 - pitcher_effectiveness) * 0.4
        ) * style_multiplier

        # Determine outcome
        random_value = random.random()
        if random_value < hit_chance:
            hit_type = GameMechanics._determine_hit_type(
                batter_data["batting_abilities"]["power"])
            return hit_type, hit_chance
        elif random_value < hit_chance + outcomes["strike"]:
            return "strike", hit_chance
        else:
            return "ball", hit_chance

    @staticmethod
    def _calculate_style_matchup(pitch_style: PitchingStyle, 
                               hit_style: HittingStyle) -> float:
        matchup_table = {
            (PitchingStyle.FASTBALLS, HittingStyle.POWER): 1.2,
            (PitchingStyle.BREAKING_BALLS, HittingStyle.POWER): 0.8,
            (PitchingStyle.CHANGEUPS, HittingStyle.POWER): 1.0,
            # Add other style matchups
        }
        return matchup_table.get((pitch_style, hit_style), 1.0)

    @staticmethod
    def _determine_hit_type(power: float) -> str:
        power_factor = power / 100
        random_value = random.random()

        if random_value < power_factor * 0.1:
            return "home_run"
        elif random_value < power_factor * 0.2:
            return "triple"
        elif random_value < power_factor * 0.4:
            return "double"
        else:
            return "single"

game_mechanics = GameMechanics()
