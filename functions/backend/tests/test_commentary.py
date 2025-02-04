from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
import google.generativeai as genai
from datetime import datetime

app = FastAPI()

class TeamSide(str, Enum):
    HOME = "home"
    AWAY = "away"

class GameStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    EXTRA_INNINGS = "extra_innings"

class Player(BaseModel):
    id: str
    name: str
    position: str
    batting_stats: Dict[str, int] = {}
    pitching_stats: Dict[str, int] = {}

class Team(BaseModel):
    name: str
    players: List[Player]
    lineup: List[str]  # Player IDs in batting order
    current_batter_index: int = 0
    
    def next_batter(self) -> Player:
        self.current_batter_index = (self.current_batter_index + 1) % len(self.lineup)
        return next(p for p in self.players if p.id == self.lineup[self.current_batter_index])

class BaseRunner(BaseModel):
    player_id: str
    base: int  # 1, 2, or 3

class InningState(BaseModel):
    outs: int = 0
    balls: int = 0
    strikes: int = 0
    runners: List[BaseRunner] = []
    runs_this_inning: int = 0

class PitchEvent(BaseModel):
    pitch_type: str
    velocity: float
    location: Dict[str, float]  # x, y coordinates
    result: str
    count: Dict[str, int]  # balls, strikes

class BatEvent(BaseModel):
    hit_type: Optional[str]
    exit_velocity: Optional[float]
    launch_angle: Optional[float]
    result: str
    runners_advanced: Optional[List[Dict[str, int]]]  # List of {player_id: new_base}

class GameState:
    def __init__(self, home_team: Team, away_team: Team):
        self.home_team = home_team
        self.away_team = away_team
        self.current_inning = 1
        self.inning_half = "top"
        self.score = {TeamSide.HOME: 0, TeamSide.AWAY: 0}
        self.inning_state = InningState()
        self.status = GameStatus.NOT_STARTED
        self.last_pitch: Optional[PitchEvent] = None
        self.last_bat: Optional[BatEvent] = None
        self.batting_team: Team = away_team
        self.fielding_team: Team = home_team
        self.current_pitcher: Optional[Player] = None
        self.current_batter: Optional[Player] = None
        self.inning_history: List[Dict] = []
        
    def switch_sides(self):
        self.inning_state = InningState()
        if self.inning_half == "top":
            self.inning_half = "bottom"
            self.batting_team = self.home_team
            self.fielding_team = self.away_team
        else:
            self.inning_half = "top"
            self.current_inning += 1
            self.batting_team = self.away_team
            self.fielding_team = self.home_team
            
        # Archive inning data
        self.inning_history.append({
            "inning": self.current_inning,
            "half": self.inning_half,
            "score": self.score.copy()
        })
    
    def check_game_status(self) -> bool:
        """Returns True if game should continue, False if game is complete"""
        if self.current_inning > 9:
            if self.inning_half == "bottom" and self.score[TeamSide.HOME] > self.score[TeamSide.AWAY]:
                self.status = GameStatus.COMPLETE
                return False
            elif self.current_inning >= 9 and self.inning_half == "bottom" and self.score[TeamSide.HOME] != self.score[TeamSide.AWAY]:
                self.status = GameStatus.COMPLETE
                return False
            self.status = GameStatus.EXTRA_INNINGS
        return True

    def update_count(self, balls: int, strikes: int):
        self.inning_state.balls = balls
        self.inning_state.strikes = strikes
        
    def add_run(self):
        self.score[TeamSide.HOME if self.batting_team == self.home_team else TeamSide.AWAY] += 1
        self.inning_state.runs_this_inning += 1

# Initialize Gemini
genai.configure(api_key='your-api-key')
model = genai.GenerativeModel('gemini-1.5-pro')

async def generate_game_commentary(event_type: str, event: Any, game_state: GameState) -> str:
    situation = f"""
    Game Situation:
    {game_state.inning_half.capitalize()} of inning {game_state.current_inning}
    Score: {game_state.home_team.name} {game_state.score[TeamSide.HOME]}, {game_state.away_team.name} {game_state.score[TeamSide.AWAY]}
    Outs: {game_state.inning_state.outs}
    Count: {game_state.inning_state.balls}-{game_state.inning_state.strikes}
    
    Batting: {game_state.current_batter.name if game_state.current_batter else 'Unknown'}
    Pitching: {game_state.current_pitcher.name if game_state.current_pitcher else 'Unknown'}
    
    Runners on base: {', '.join(f"{r.base}B: {next((p.name for p in game_state.batting_team.players if p.id == r.player_id), 'Unknown')}" for r in game_state.inning_state.runners)}
    """
    
    if event_type == "pitch":
        event_details = f"""
        Pitch Details:
        Type: {event.pitch_type}
        Velocity: {event.velocity} mph
        Result: {event.result}
        """
    else:  # bat event
        event_details = f"""
        Bat Result:
        Hit Type: {event.hit_type if event.hit_type else 'N/A'}
        Exit Velocity: {event.exit_velocity if event.exit_velocity else 'N/A'} mph
        Result: {event.result}
        """
    
    prompt = f"Generate exciting baseball commentary for this {event_type} event.\n{situation}\n{event_details}"
    
    try:
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt).text
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Commentary generation failed: {str(e)}")

@app.post("/start_game")
async def start_game(home_team: Team, away_team: Team):
    game_state = GameState(home_team, away_team)
    game_state.status = GameStatus.IN_PROGRESS
    game_state.current_pitcher = next(p for p in game_state.fielding_team.players if p.position == "P")
    game_state.current_batter = game_state.batting_team.next_batter()
    
    return {
        "message": "Game started",
        "home_team": home_team.name,
        "away_team": away_team.name,
        "starting_pitcher": game_state.current_pitcher.name,
        "leadoff_batter": game_state.current_batter.name
    }

@app.post("/pitch")
async def handle_pitch(pitch: PitchEvent):
    if game_state.status == GameStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Game is complete")
        
    game_state.last_pitch = pitch
    game_state.update_count(pitch.count["balls"], pitch.count["strikes"])
    
    commentary = await generate_game_commentary("pitch", pitch, game_state)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "event_type": "pitch",
        "commentary": commentary,
        "game_state": {
            "inning": game_state.current_inning,
            "half": game_state.inning_half,
            "score": game_state.score,
            "count": {"balls": game_state.inning_state.balls, "strikes": game_state.inning_state.strikes},
            "outs": game_state.inning_state.outs,
            "status": game_state.status
        }
    }

@app.post("/bat")
async def handle_bat(bat: BatEvent):
    if game_state.status == GameStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Game is complete")
        
    game_state.last_bat = bat
    
    # Process bat result
    if "out" in bat.result.lower():
        game_state.inning_state.outs += 1
        if game_state.inning_state.outs >= 3:
            game_state.switch_sides()
            game_state.check_game_status()
    
    # Update runners and score
    if bat.runners_advanced:
        for runner_update in bat.runners_advanced:
            for player_id, new_base in runner_update.items():
                if new_base > 3:  # Runner scored
                    game_state.add_run()
                else:  # Runner advanced
                    existing_runner = next((r for r in game_state.inning_state.runners if r.player_id == player_id), None)
                    if existing_runner:
                        existing_runner.base = new_base
                    else:
                        game_state.inning_state.runners.append(BaseRunner(player_id=player_id, base=new_base))
    
    # Update batter
    game_state.current_batter = game_state.batting_team.next_batter()
    
    commentary = await generate_game_commentary("bat", bat, game_state)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "event_type": "bat",
        "commentary": commentary,
        "game_state": {
            "inning": game_state.current_inning,
            "half": game_state.inning_half,
            "score": game_state.score,
            "outs": game_state.inning_state.outs,
            "status": game_state.status,
            "next_batter": game_state.current_batter.name
        }
    }

@app.get("/game_status")
async def get_game_status():
    return {
        "status": game_state.status,
        "current_inning": game_state.current_inning,
        "inning_half": game_state.inning_half,
        "score": game_state.score,
        "inning_state": game_state.inning_state,
        "batting_team": game_state.batting_team.name,
        "current_batter": game_state.current_batter.name if game_state.current_batter else None,
        "current_pitcher": game_state.current_pitcher.name if game_state.current_pitcher else None,
        "inning_history": game_state.inning_history
    }