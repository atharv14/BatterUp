import json
import os
from typing import Dict, Any
from pathlib import Path

def calculate_batting_abilities(batting_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate batting abilities using provided formulas."""
    try:
        # Contact Rating
        ba = float(batting_data.get('Hits/At Bats', 0))
        contact = min(100, (ba * 250) + 25)
        
        # Power Rating
        slg = float(batting_data.get('Total Bases/At Bats', 0))
        power = min(100, slg * 200)
        
        # Discipline Rating
        obp = float(batting_data.get('(H + BB + HBP) / (At Bats + BB + HBP + SF)', 0))
        discipline = min(100, obp * 250)
        
        # Speed Rating
        sb = batting_data.get('Stolen Bases', 0)
        cs = batting_data.get('Caught Stealing', 0)
        if sb + cs > 0:
            speed = min(100, ((sb * 100)/(sb + cs)) * (sb/50))
        else:
            speed = 0
            
        return {
            "contact": round(max(0, contact), 1),
            "power": round(max(0, power), 1),
            "discipline": round(max(0, discipline), 1),
            "speed": round(max(0, speed), 1)
        }
    except Exception as e:
        print(f"Error calculating batting abilities: {e}")
        return {"contact": 0, "power": 0, "discipline": 0, "speed": 0}

def calculate_pitching_abilities(pitching_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate pitching abilities using provided formulas."""
    try:
        # Control Rating
        bb9 = float(pitching_data.get('9*BB/IP', 0))
        whip = float(pitching_data.get('(BB + H)/IP', 1))
        so_bb = float(pitching_data.get('SO/BB', 0))
        
        base_control = 100 - (bb9 * 10)
        whip_modifier = (1.5 - whip) * 10
        command_modifier = so_bb * 5
        
        control = max(0, min(100, (base_control * 0.5) + (whip_modifier * 0.3) + (command_modifier * 0.2)))
        
        # Velocity Rating
        so9 = float(pitching_data.get('9*SO/IP', 0))
        velocity = min(100, (so9 * 10))
        
        # Stamina Rating
        ip_str = str(pitching_data.get('Innings Pitched', '0'))
        ip = float(ip_str.replace('.1', '.33').replace('.2', '.67')) if '.' in ip_str else float(ip_str)
        g = max(1, pitching_data.get('Games Pitched', 1))
        gs = pitching_data.get('Games Started', 0)
        gf = pitching_data.get('Games Finished', 0)
        cg = pitching_data.get('Completed Games', 0)
        bf = pitching_data.get('Batters Faced', 0)
        
        base = ((ip/g) * 10)
        role_modifier = (20 if gs/g > 0.8 else (-15 if gf/g > 0.8 else 0))
        durability_modifier = ((cg/gs if gs > 0 else 0) * 25)
        endurance_factor = ((bf/g)/5)
        
        stamina = min(100, base + role_modifier + durability_modifier + endurance_factor)
        
        # Effectiveness Rating
        era_plus = float(pitching_data.get('ERA+', 100))
        fip = float(pitching_data.get('Fielding Independent Pitching', 4.0))
        effectiveness = min(100, (era_plus/2) + (50 - (fip * 10)))
        
        return {
            "control": round(control, 1),
            "velocity": round(velocity, 1),
            "stamina": round(stamina, 1),
            "effectiveness": round(effectiveness, 1)
        }
    except Exception as e:
        print(f"Error calculating pitching abilities: {e}")
        return {"control": 0, "velocity": 0, "stamina": 0, "effectiveness": 0}

def calculate_fielding_abilities(fielding_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate fielding abilities using provided formulas."""
    try:
        # Defense Rating
        fld_pct = float(fielding_data.get('Fielding Percentage', 0))
        defense = min(100, fld_pct * 100)
        
        # Range Rating
        rf9 = float(fielding_data.get('Range Factor per 9 Innings', 0))
        rdrs = float(fielding_data.get('Runs Saved Above Average', 0))
        range_rating = min(100, max(0, (rf9 * 10) + (rdrs * 2)))
        
        # Reliability Rating
        errors = fielding_data.get('Errors', 0)
        chances = fielding_data.get('Defensive Chances', 1)
        dp = fielding_data.get('Double Plays Turned', 0)
        innings = float(fielding_data.get('Innings Played in Field', 0))
        games = fielding_data.get('Games Played', 1)
        
        error_factor = (100 - ((errors * 100) / chances)) * 0.4
        consistency = (50 + (dp * 0.2)) * 0.3
        endurance = (innings / (games * 9) * 100) * 0.3
        
        reliability = min(100, error_factor + consistency + endurance)
        
        return {
            "defense": round(defense, 1),
            "range": round(range_rating, 1),
            "reliability": round(reliability, 1)
        }
    except Exception as e:
        print(f"Error calculating fielding abilities: {e}")
        return {"defense": 0, "range": 0, "reliability": 0}
    
def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to a 1-100 scale."""
    if min_val == max_val:
        return 50  # Default middle value when no range
    normalized = ((value - min_val) / (max_val - min_val)) * 99 + 1  # Scale 1-100
    return round(max(1, min(100, normalized)), 1)

def get_position_type(player_info: Dict, fielding_data: Dict) -> str:
    """Determine player's primary position type."""
    position = (player_info.get('primaryPosition', {}).get('type', ''))

    if any(pos in str(position) for pos in ['P', 'Pitcher']):
        return 'Pitcher'
    elif any(pos in str(position) for pos in ['C', 'Catcher']):
        return 'Catcher'
    elif any(pos in str(position) for pos in ['1B', '2B', '3B', 'SS', 'Infielder']):
        return 'Infielder'
    elif any(pos in str(position) for pos in ['LF', 'CF', 'RF', 'OF', 'Outfielder']):
        return 'Outfielder'
    else:
        return 'Hitter'
    
def calculate_position_based_abilities(position_type: str, batting_data: Dict, 
                                pitching_data: Dict, fielding_data: Dict) -> Dict[str, Dict[str, float]]:
    """Calculate abilities based on player's position."""
    abilities = {
        "batting_abilities": {"contact": 1.0, "power": 1.0, "discipline": 1.0, "speed": 1.0},
        "pitching_abilities": {"control": 1.0, "velocity": 1.0, "stamina": 1.0, "effectiveness": 1.0},
        "fielding_abilities": {"defense": 1.0, "range": 1.0, "reliability": 1.0}
    }
    
    # Calculate based on position
    if position_type == 'Pitcher':
        abilities["pitching_abilities"] = calculate_pitching_abilities(pitching_data)
        abilities["fielding_abilities"] = calculate_fielding_abilities(fielding_data)
        # Minimal batting abilities for pitchers
        if batting_data:
            abilities["batting_abilities"] = calculate_batting_abilities(batting_data)
    else:
        # Position players
        if batting_data:
            abilities["batting_abilities"] = calculate_batting_abilities(batting_data)
        if fielding_data:
            abilities["fielding_abilities"] = calculate_fielding_abilities(fielding_data)
        # Some position players might have pitching stats (rare cases)
        if pitching_data:
            abilities["pitching_abilities"] = calculate_pitching_abilities(pitching_data)
    
    return abilities

def create_player_card(batting_data: Dict, pitching_data: Dict,
                      fielding_data: Dict, player_info: Dict) -> Dict:
    """Create a player card with the original structure."""
    
    # Determine position type
    position_type = get_position_type(player_info, fielding_data)
    
    # Calculate abilities based on position
    abilities = calculate_position_based_abilities(
        position_type, batting_data, pitching_data, fielding_data
    )

    return {
        "player_id": player_info.get('id', ''),
        "basic_info": {
            "name": player_info.get('fullName', ''),
            "team": batting_data.get('Team', '') or pitching_data.get('Team', '') or fielding_data.get('Team', ''),
            "primary_position": position_type,
            "bats": player_info.get('batSide', {}).get('description', ''),
            "throws": player_info.get('pitchHand', {}).get('description', ''),
            "age": player_info.get('currentAge', 0),
            "height": player_info.get('height', ''),
            "weight": player_info.get('weight', 0)
        },
        "batting_abilities": abilities["batting_abilities"],
        "pitching_abilities": abilities["pitching_abilities"],
        "fielding_abilities": abilities["fielding_abilities"],
        "additional_info": {
            "debut_date": player_info.get('mlbDebutDate', ''),
            "birth_place": {
                "city": player_info.get('birthCity', ''),
                "state": player_info.get('birthStateProvince', ''),
                "country": player_info.get('birthCountry', '')
            },
            "awards": (batting_data.get('Awards', '') or 
                      pitching_data.get('Awards', '') or 
                      fielding_data.get('Awards', ''))
        }
    }

def process_player_cards(data: Dict[str, list]) -> Dict[str, Dict]:
    """Process all players and create their cards."""
    player_cards = {}
    
    # Process each player from player info
    for player_info in data['player_info']:
        player_name = player_info.get('fullName', '')
        if not player_name:
            continue
            
        # Find corresponding stats using improved matching
        batting_stats = get_matching_stats(data['batting'], player_name)
        pitching_stats = get_matching_stats(data['pitching'], player_name)
        fielding_stats = get_matching_stats(data['fielding'], player_name)
        
        # Create player card
        player_card = create_player_card(
            batting_stats, pitching_stats, fielding_stats, player_info
        )
        
        # Store using player_id as key
        player_cards[str(player_info.get('id', ''))] = player_card
    
    return player_cards

def get_matching_stats(data_list: list, player_name: str) -> Dict:
    """
    Find player stats with proper name matching, handling asterisks and variations.
    """
    # Try exact match first
    stats = next((item for item in data_list if item.get('Player Name', '') == player_name), None)
    
    # If no match, try matching with/without asterisk
    if not stats:
        if '*' in player_name:
            clean_name = player_name.replace('*', '')
            stats = next((item for item in data_list if item.get('Player Name', '').replace('*', '') == clean_name), {})
        else:
            stats = next((item for item in data_list if item.get('Player Name', '').replace('*', '') == player_name), {})
    
    return stats or {}

def load_all_data(base_dir: Path) -> Dict[str, list]:
    """Load all JSON files and return their contents."""
    files = {
        'batting': base_dir / "baseball_batting_stats.json",
        'pitching': base_dir / "baseball_pitching_stats.json",
        'fielding': base_dir / "baseball_fielding_stats.json",
        'player_info': base_dir / "mlb_players_2024_from_api.json"
    }
    
    data = {}
    for key, file_path in files.items():
        print(f"Loading {key} data from {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data[key] = json.load(file)
            print(f"Successfully loaded {key} data - {len(data[key])} records")
        except Exception as e:
            print(f"Error loading {key} data: {e}")
            data[key] = []
    
    return data

if __name__ == "__main__":
    # Set up paths
    base_dir = Path("../2024 MLB season data")
    output_dir = Path("processed_data")

    # Load all data
    print("Loading data files...")
    all_data = load_all_data(base_dir)

    # Process player cards
    print("\nProcessing player cards...")
    player_cards = process_player_cards(all_data)

    output_file = Path("processed_data/player_cards.json")

    print(f"\nSaving processed data to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(player_cards, f, ensure_ascii=False, indent=4)

    # Print sample
    sample_player_id = next(iter(player_cards))
    print("\nSample player card:")
    print(json.dumps(player_cards[sample_player_id], indent=4))

    print(f"\nProcessing complete!")
    print(f"Total players processed: {len(player_cards)}")
