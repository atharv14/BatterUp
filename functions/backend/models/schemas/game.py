from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Union
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

class HitType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    OUT = "out"

class PlayResult(BaseModel):
    outcome: str  # "single", "double", "triple", "home_run", "out"
    description: str
    advancements: List[RunnerAdvancement] = []
    runs_scored: int = 0
    batting_team_runs: int = 0
    hits: int = 0
    hit_type: Optional[HitType] = None
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

# class GameView(BaseModel):
#     game_id: str
#     state: GameState
#     history: List[GameHistory] = []

#     class Config:
#         arbitrary_types_allowed = True

class GameCreate(BaseModel):
    user_id: str
    deck: Deck

class GameJoin(BaseModel):
    user_id: str
    deck: Deck

class GameEvent(BaseModel):
    event_type: Literal["game_created", "player_joined"]
    timestamp: datetime
    player_id: Optional[str] = None
    event_data: Dict = Field(default_factory=dict)

class PlayAction(BaseModel):
    inning: int
    is_top_inning: bool
    batting_team: str
    pitching_team: str
    action: Dict
    result: Dict
    timestamp: datetime
    play_data: Dict = Field(default_factory=dict)

class HistoryEntry(BaseModel):
    entry_type: Literal["event", "play"]
    data: Union[GameEvent, PlayAction]

class GameView(BaseModel):
    game_id: str
    state: GameState
    history: List[HistoryEntry]

class CommentaryResponse(BaseModel):
    game_id: str
    status: GameStatus
    commentaries: List[str] = []  # List of all commentaries
    audio_commentaries: Optional[List[str]] = None
    latest_commentary: str
    latest_audio_commentary: Optional[str] = None
    play_data: Optional[Dict] = None


class AtBatState(BaseModel):
    balls: int = 0
    strikes: int = 0
    batter_id: str
    pitcher_id: str
    is_complete: bool = False
    result: Optional[str] = None

class PitchOutcome(str, Enum):
    BALL = "ball"
    STRIKE = "strike"
    IN_PLAY = "in_play"

class PlayState(BaseModel):
    current_at_bat: Optional[AtBatState] = None
    last_pitch_style: Optional[str] = None
    last_hit_style: Optional[str] = None
    last_pitch_outcome: Optional[PitchOutcome] = None
    bases_before_play: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {"first": None, "second": None, "third": None}
    )

class EnhancedGameState(GameState):
    play_state: PlayState = Field(default_factory=PlayState)
    at_bat_history: List[AtBatState] = Field(default_factory=list)
