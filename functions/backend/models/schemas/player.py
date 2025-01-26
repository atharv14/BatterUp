from pydantic import BaseModel, Field
from typing import Dict, Optional, List


class PlayerBase(BaseModel):
    player_id: str
    basic_info: Dict
    batting_abilities: Dict
    pitching_abilities: Dict
    fielding_abilities: Dict
    role_info: Dict

    class Config:
        json_schema_extra = {
            "player_id": 650391,
            "basic_info": {
                "name": "Eloy Jiménez",
                "team": "2TM",
                "primary_position": "Hitter",
                "bats": "Right",
                "throws": "Right",
                "age": 28,
                "height": "6' 4\"",
                "weight": 250,
                "headshot_url": "https://securea.mlb.com/mlb/images/players/head_shot/650391.jpg"
            },
            "batting_abilities": {
                "contact": 72.6,
                "power": 50.4,
                "discipline": 57.8,
                "speed": 4.5
            },
            "pitching_abilities": {
                "control": 1.0,
                "velocity": 1.0,
                "stamina": 1.0,
                "effectiveness": 1.0
            },
            "fielding_abilities": {
                "defense": 1.6,
                "range": 4.0,
                "reliability": 75.7
            },
            "additional_info": {
                "debut_date": "2019-03-28",
                "birth_place": {
                    "city": "Santo Domingo",
                    "state": "",
                    "country": "Dominican Republic"
                },
                "awards": ""
            },
            "role_info": {
                "primary_role": "Hitter",
                "secondary_roles": [],
                "hitting_styles": [
                    "Designated Hitter"
                ]
            }
        }


class PlayerQuery(BaseModel):
    role: Optional[str] = Field(
        None, description="Player's role (e.g., Pitcher, Hitter)")
    team: Optional[str] = Field(
        None, description="Team abbreviation (e.g., NYY)")
    position: Optional[str] = Field(None, description="Primary position")


class PlayerList(BaseModel):
    players: List[PlayerBase]
    total: int = Field(...,
                       description="Total number of players matching the query")
