from typing import Tuple, Dict, Optional
import random
from models.schemas.game import AtBatState, PitchOutcome, PlayState
from models.schemas.base import PitchingStyle, HittingStyle

class AtBatService:
    """Service to handle pitch-by-pitch gameplay"""
    
    @staticmethod
    def resolve_pitch(
        pitch_style: PitchingStyle,
        pitcher_abilities: Dict
    ) -> PitchOutcome:
        """
        Resolve if pitch is ball, strike, or in play based on pitcher's control
        """
        # Base probabilities
        control = pitcher_abilities.get('control', 50) / 100
        
        # Adjust probabilities based on pitch style
        if pitch_style == PitchingStyle.FASTBALLS:
            strike_prob = control * 0.7  # Fastballs easier to control
        elif pitch_style == PitchingStyle.BREAKING_BALLS:
            strike_prob = control * 0.5  # Breaking balls harder to control
        else:  # Changeups
            strike_prob = control * 0.6
            
        # Roll for outcome
        roll = random.random()
        
        if roll < strike_prob:
            return PitchOutcome.STRIKE
        elif roll < strike_prob + 0.3:  # 30% chance for ball
            return PitchOutcome.BALL
        else:
            return PitchOutcome.IN_PLAY

    @staticmethod
    def check_count_resolution(at_bat: AtBatState) -> Tuple[bool, Optional[str]]:
        """
        Check if at-bat is resolved by count (walk or strikeout)
        Returns: (is_resolved, result)
        """
        if at_bat.balls >= 4:
            return True, "walk"
        if at_bat.strikes >= 3:
            return True, "strikeout"
        return False, None

    @staticmethod
    def update_count(
        at_bat: AtBatState,
        pitch_outcome: PitchOutcome
    ) -> Tuple[AtBatState, bool, Optional[str]]:
        """
        Update ball/strike count and check for resolution
        Returns: (updated_at_bat, is_resolved, result)
        """
        if pitch_outcome == PitchOutcome.BALL:
            at_bat.balls += 1
        elif pitch_outcome == PitchOutcome.STRIKE:
            at_bat.strikes += 1
            
        is_resolved, result = AtBatService.check_count_resolution(at_bat)
        if is_resolved:
            at_bat.is_complete = True
            at_bat.result = result
            
        return at_bat, is_resolved, result

    @staticmethod
    def handle_walk(
        game_state: Dict,
        batter_id: str
    ) -> Dict:
        """
        Handle base runner advancement on walk
        """
        bases = game_state['bases'].copy()
        
        # Check if bases are loaded
        if bases['first'] and bases['second'] and bases['third']:
            # Score runner from third
            game_state['team1' if game_state['is_top_inning'] else 'team2']['score'] += 1
            
        # Advance runners if forced
        if bases['second'] and bases['first']:
            bases['third'] = bases['second']
        if bases['first']:
            bases['second'] = bases['first']
            
        # Put batter on first
        bases['first'] = batter_id
        
        game_state['bases'] = bases
        return game_state