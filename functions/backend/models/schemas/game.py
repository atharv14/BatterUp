from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime
from .base import GameStatus, PitchingStyle, HittingStyle
from .user import Deck

class BaseRunner(BaseModel):
    player_id: str
    starting_base: int  # The base where runner started this play
    is_forced: bool = False  # For force-out situations
    can_advance: bool = True  # Whether runner can advance on certain plays

class BaseState(BaseModel):
    first: Optional[str] = None  # player_id of runner
    second: Optional[str] = None
    third: Optional[str] = None

    def get_runners(self) -> List[BaseRunner]:
        """Get list of all runners currently on base"""
        runners = []
        if self.first:
            runners.append(('first', self.first))
        if self.second:
            runners.append(('second', self.second))
        if self.third:
            runners.append(('third', self.third))
        return runners

    def is_base_occupied(self, base: str) -> bool:
        """Check if a specific base is occupied"""
        return getattr(self, base) is not None

    def clear_bases(self) -> None:
        """Clear all bases"""
        self.first = None
        self.second = None
        self.third = None

class RunnerAdvancement(BaseModel):
    runner: BaseRunner
    from_base: str
    to_base: str
    scored: bool = False
    out: bool = False

class PlayerGameStats(BaseModel):
    hits: int = 0
    outs: int = 0
    runs: int = 0
    rbis: int = 0

class Action(BaseModel):
    player_id: str
    timestamp: datetime
    action_type: str  # "pitch" or "bat"
    selected_style: Union[PitchingStyle, HittingStyle]

class PlayResult(BaseModel):
    outcome: str  # "single", "double", "triple", "home_run", "out"
    description: str
    advancements: List[RunnerAdvancement] = []
    runs_scored: int = 0
    batting_team_runs: int = 0
    fielding_team_errors: int = 0

class TeamLineup(BaseModel):
    batting_order: List[str]  # List of player_ids in batting order
    current_batter_index: int = 0
    current_pitcher_index: int = 0
    available_pitchers: List[str]  # List of pitcher player_ids not yet used
    used_pitchers: List[str] = []  # List of pitcher player_ids already used

class TeamState(BaseModel):
    user_id: str
    deck: Deck
    lineup: TeamLineup
    score: int = 0
    hits: int = 0
    errors: int = 0
    player_stats: Dict[str, PlayerGameStats] = Field(default_factory=dict)

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