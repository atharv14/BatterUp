from typing import Tuple, List, Dict
from models.schemas.game import TeamState, TeamLineup


class LineupManager:
    @staticmethod
    def initialize_lineup(deck: Dict) -> TeamLineup:
        """Initialize batting order and pitchers"""
        # Create batting order: Starts with hitters, then fielders
        batting_order = (
            deck['hitters'] +  # Designated hitters first
            deck['infielders'] +  # Then infielders
            deck['outfielders'] +  # Then outfielders
            deck['catchers']  # Catchers bat last
        )

        return TeamLineup(
            batting_order=batting_order,
            current_batter_index=0,
            current_pitcher_index=0,
            available_pitchers=deck['pitchers'].copy(),
            used_pitchers=[]
        )

    @staticmethod
    def next_batter(team_state: TeamState) -> str:
        """Get next batter in lineup and update batting order index"""
        lineup = team_state.lineup
        current_batter = lineup.batting_order[lineup.current_batter_index]

        # Update index for next batter
        lineup.current_batter_index = (
            lineup.current_batter_index + 1) % len(lineup.batting_order)

        return current_batter

    @staticmethod
    def can_change_pitcher(team_state: TeamState) -> bool:
        """Check if team can change pitchers"""
        return len(team_state.lineup.available_pitchers) > 0

    @staticmethod
    def change_pitcher(lineup: TeamState, new_pitcher_id: str) -> Tuple[bool, str]:
        """
        Attempt to change pitcher
        Returns: (success, message)
        """
        try:
            if new_pitcher_id not in lineup.available_pitchers:
                return False, "Pitcher not available or already used"
                
            # Get current pitcher
            if lineup.available_pitchers:
                current_pitcher = lineup.available_pitchers[lineup.current_pitcher_index]
                lineup.used_pitchers.append(current_pitcher)
                lineup.available_pitchers.remove(current_pitcher)
            
            # Add new pitcher
            if new_pitcher_id in lineup.used_pitchers:
                return False, "Pitcher has already been used"
                
            # lineup.available_pitchers.insert(0, new_pitcher_id)
            lineup.current_pitcher_index = lineup.current_pitcher_index + 1
            
            return True, "Pitcher changed successfully"
            
        except Exception as e:
            return False, f"Error changing pitcher: {str(e)}"
