from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class PlayerRole(str, Enum):
    PITCHER = "Pitcher"
    HITTER = "Hitter"
    FIELDER = "Fielder"

class PitchingStyle(str, Enum):
    FASTBALLS = "Fastballs"
    BREAKING_BALLS = "Breaking Balls"
    CHANGEUPS = "Changeups"

class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PlayerSelection(BaseModel):
    player_id: str
    role: PlayerRole
    role_specific_info: Dict = Field(
        default_factory=dict,
        description="Role-specific attributes (e.g., pitching_styles for pitchers)"
    )

class GameCreate(BaseModel):
    player1_id: str
    player2_id: Optional[str] = None  # Optional for waiting for opponent
    player1_selection: PlayerSelection

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    player1: PlayerSelection
    player2: Optional[PlayerSelection] = None
    current_state: Dict = Field(
        default_factory=dict,
        description="Current game state including scores, inning, etc."
    )
    created_at: str
    updated_at: str