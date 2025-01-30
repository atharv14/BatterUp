from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime
from .base import GameStatus, PitchingStyle, HittingStyle
from .user import Deck

class BaseState(BaseModel):
    first: Optional[str] = None  # player_id of runner
    second: Optional[str] = None
    third: Optional[str] = None

class PlayerGameStats(BaseModel):
    hits: int = 0
    outs: int = 0
    runs: int = 0
    rbis: int = 0

class TeamState(BaseModel):
    user_id: str
    deck: Deck
    current_pitcher: str
    current_batter: str
    score: int = 0
    hits: int = 0
    errors: int = 0
    player_stats: Dict[str, PlayerGameStats] = Field(default_factory=dict)

class Action(BaseModel):
    player_id: str
    timestamp: datetime
    action_type: str  # "pitch" or "bat"
    selected_style: Union[PitchingStyle, HittingStyle]

class PlayResult(BaseModel):
    outcome: str  # "single", "double", "triple", "home_run", "out"
    description: str
    batting_team_runs: int = 0
    fielding_team_errors: int = 0

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    inning: int = 1
    is_top_inning: bool = True
    outs: int = 0
    bases: BaseState = Field(default_factory=BaseState)
    team1: TeamState
    team2: Optional[TeamState] = None
    last_action: Optional[Action] = None
    action_deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class GameHistory(BaseModel):
    inning: int
    is_top_inning: bool
    timestamp: datetime
    batting_team: str  # user_id
    pitching_team: str  # user_id
    action: Action
    result: PlayResult

class GameView(BaseModel):
    game_id: str
    state: GameState
    history: List[GameHistory] = []

    class Config:
        arbitrary_types_allowed = True

class GameCreate(BaseModel):
    user_id: str
    deck: Deck

class GameJoin(BaseModel):
    user_id: str
    deck: Deck