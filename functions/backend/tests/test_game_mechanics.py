import pytest
from services.game_mechanics import game_mechanics

def test_hit_calculation():
    batter_stats = {
        "batting_abilities": {
            "contact": 80,
            "power": 70,
            "discipline": 75,
            "speed": 60
        }
    }
    
    pitcher_stats = {
        "pitching_abilities": {
            "control": 70,
            "velocity": 75,
            "stamina": 80,
            "effectiveness": 72
        }
    }
    
    # Test multiple scenarios
    for _ in range(100):
        is_hit, hit_type = game_mechanics.calculate_hit_probability(
            batter_stats,
            pitcher_stats,
            "Fastballs",
            "power_hitter"
        )
        
        assert isinstance(is_hit, bool)
        assert hit_type in ["SINGLE", "DOUBLE", "TRIPLE", "HOME_RUN", "OUT"]

def test_hit_type_distribution():
    # Test hit type distribution
    hit_types = {
        "SINGLE": 0,
        "DOUBLE": 0,
        "TRIPLE": 0,
        "HOME_RUN": 0
    }
    
    # Run 1000 simulations
    for _ in range(1000):
        hit_type = game_mechanics.determine_hit_type(0.7)
        hit_types[hit_type] += 1
    
    # Check distribution roughly matches expected probabilities
    total = sum(hit_types.values())
    for hit_type, count in hit_types.items():
        probability = count / total
        assert abs(probability - game_mechanics.HIT_TYPES[hit_type]) < 0.1