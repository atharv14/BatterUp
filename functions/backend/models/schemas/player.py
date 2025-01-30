from .base import Position, PitchingStyle, HittingStyle
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class BasicInfo(BaseModel):
    name: str
    team: str
    primary_position: Position
    bats: str
    throws: str
    age: int
    height: str
    weight: int
    headshot_url: str

class Abilities(BaseModel):
    contact: float = Field(ge=0, le=100)
    power: float = Field(ge=0, le=100)
    discipline: float = Field(ge=0, le=100)
    speed: float = Field(ge=0, le=100)

class PitchingAbilities(BaseModel):
    control: float = Field(ge=0, le=100)
    velocity: float = Field(ge=0, le=100)
    stamina: float = Field(ge=0, le=100)
    effectiveness: float = Field(ge=0, le=100)

class FieldingAbilities(BaseModel):
    defense: float = Field(ge=0, le=100)
    range: float = Field(ge=0, le=100)
    reliability: float = Field(ge=0, le=100)

class RoleInfo(BaseModel):
    primary_role: Position
    secondary_roles: List[Position] = []
    pitching_styles: Optional[List[PitchingStyle]] = None
    hitting_styles: Optional[List[HittingStyle]] = None

class PlayerCard(BaseModel):
    player_id: str
    basic_info: BasicInfo
    batting_abilities: Abilities
    pitching_abilities: PitchingAbilities
    fielding_abilities: FieldingAbilities
    role_info: RoleInfo

class PlayerList(BaseModel):
    players: List[PlayerCard]
    total: int