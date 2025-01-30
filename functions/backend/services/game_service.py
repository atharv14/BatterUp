from fastapi import HTTPException
from typing import Dict, Tuple
import random
from datetime import datetime, timedelta
from models.schemas.game import BaseState, GameState, Action, GameHistory
from models.schemas.base import PitchingStyle, HittingStyle

class GameService:
    ACTION_TIMEOUT = 5  # seconds

    @staticmethod
    def calculate_outcome(
        pitcher_data: Dict,
        batter_data: Dict,
        pitch_style: PitchingStyle,
        hit_style: HittingStyle
    ) -> Tuple[str, str]:
        """Calculate the outcome of a pitch-hit interaction"""
        
        # Base probabilities
        contact_prob = batter_data['batting_abilities']['contact'] / 100
        power_prob = batter_data['batting_abilities']['power'] / 100
        pitcher_effectiveness = pitcher_data['pitching_abilities']['effectiveness'] / 100

        # Adjust based on styles
        if pitch_style == PitchingStyle.FASTBALLS:
            if hit_style == HittingStyle.POWER:
                power_prob *= 1.2  # Power hitters better against fastballs
            contact_prob *= 0.9  # Harder to contact fastballs
            
        elif pitch_style == PitchingStyle.BREAKING_BALLS:
            if hit_style == HittingStyle.DESIGNATED:
                contact_prob *= 1.1  # Designated hitters better against breaking balls
            power_prob *= 0.9  # Less power on breaking balls
            
        elif pitch_style == PitchingStyle.CHANGEUPS:
            if hit_style == HittingStyle.SWITCH:
                contact_prob *= 1.1  # Switch hitters adapt better to changeups

        # Final calculations
        contact_roll = random.random()
        power_roll = random.random()
        
        if contact_roll > contact_prob:
            return "out", "Strike out!"
            
        if power_roll < power_prob * (1 - pitcher_effectiveness):
            if power_roll < power_prob * 0.2:
                return "home_run", "Home run!"
            elif power_roll < power_prob * 0.4:
                return "triple", "Triple!"
            elif power_roll < power_prob * 0.6:
                return "double", "Double!"
            else:
                return "single", "Single!"
        
        return "out", "Fly out!"

    @staticmethod
    def update_game_state(
        current_state: GameState,
        outcome: str,
        description: str
    ) -> GameState:
        """Update game state based on play outcome"""
        
        # Update bases and score based on outcome
        if outcome == "home_run":
            # Score all runners and batter
            runs = 1  # Batter
            if current_state.bases.third:
                runs += 1
            if current_state.bases.second:
                runs += 1
            if current_state.bases.first:
                runs += 1
                
            # Clear bases
            current_state.bases = BaseState()
            
            # Add runs
            if current_state.is_top_inning:
                current_state.team1.score += runs
            else:
                current_state.team2.score += runs
                
        elif outcome == "triple":
            # Score all runners
            runs = 0
            if current_state.bases.third:
                runs += 1
            if current_state.bases.second:
                runs += 1
            if current_state.bases.first:
                runs += 1
                
            # Place batter on third
            current_state.bases.third = current_state.team1.current_batter if current_state.is_top_inning else current_state.team2.current_batter
            current_state.bases.second = None
            current_state.bases.first = None
            
            # Add runs
            if current_state.is_top_inning:
                current_state.team1.score += runs
            else:
                current_state.team2.score += runs
                
        # Add similar logic for double and single
        
        elif outcome == "out":
            current_state.outs += 1
            if current_state.outs >= 3:
                # Switch sides
                current_state.is_top_inning = not current_state.is_top_inning
                current_state.outs = 0
                current_state.bases = BaseState()
                if not current_state.is_top_inning:
                    current_state.inning += 1

        return current_state