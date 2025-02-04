from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

class Position(str, Enum):
    PITCHER = "Pitcher"
    CATCHER = "Catcher"
    INFIELDER = "Infielder"
    OUTFIELDER = "Outfielder"
    HITTER = "Hitter"

class PitchingStyle(str, Enum):
    FASTBALLS = "Fastballs"
    BREAKING_BALLS = "Breaking Balls"
    CHANGEUPS = "Changeups"

class HittingStyle(str, Enum):
    POWER = "Power Hitter"
    SWITCH = "Switch Hitter"
    DESIGNATED = "Designated Hitter"

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
