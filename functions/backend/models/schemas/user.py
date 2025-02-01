from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from .base import UserRole
from datetime import datetime

class DeckRequirements:
    CATCHERS = 1
    PITCHERS = 5
    INFIELDERS = 4
    OUTFIELDERS = 3
    HITTERS = 4

class Deck(BaseModel):
    catchers: List[str] = Field(..., min_items=DeckRequirements.CATCHERS, max_items=DeckRequirements.CATCHERS)
    pitchers: List[str] = Field(..., min_items=DeckRequirements.PITCHERS, max_items=DeckRequirements.PITCHERS)
    infielders: List[str] = Field(..., min_items=DeckRequirements.INFIELDERS, max_items=DeckRequirements.INFIELDERS)
    outfielders: List[str] = Field(..., min_items=DeckRequirements.OUTFIELDERS, max_items=DeckRequirements.OUTFIELDERS)
    hitters: List[str] = Field(..., min_items=DeckRequirements.HITTERS, max_items=DeckRequirements.HITTERS)

class UserStats(BaseModel):
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    total_hits: int = 0
    total_runs: int = 0
    total_strikeouts: int = 0

class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    firebase_uid: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    deck: Optional[Deck] = None

class UserResponse(UserBase):
    firebase_uid: str
    created_at: datetime
    updated_at: datetime
    deck: Optional[Deck] = None
    stats: UserStats = Field(default_factory=UserStats)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserInDB(UserResponse):
    pass
