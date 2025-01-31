from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from .base import GameStatus

class InningHistory(BaseModel):
    inning_number: int
    is_top_inning: bool
    batting_team_id: str
    pitching_team_id: str
    runs_scored: int
    hits: int
    errors: int
    plays: List[Dict]  # Detailed play-by-play data

class PlayerGameStats(BaseModel):
    # Batting Stats
    at_bats: int = 0
    hits: int = 0
    runs: int = 0
    rbis: int = 0
    strikeouts: int = 0
    
    # Pitching Stats
    innings_pitched: float = 0.0
    earned_runs: int = 0
    strikeouts_thrown: int = 0
    hits_allowed: int = 0

class GameHistory(BaseModel):
    game_id: str
    start_time: datetime
    end_time: Optional[datetime]
    team1_id: str
    team2_id: str
    final_score: Dict[str, int]
    winner_id: Optional[str]
    status: GameStatus
    innings: List[InningHistory]
    player_stats: Dict[str, PlayerGameStats]  # player_id -> stats