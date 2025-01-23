import requests
import json
from time import sleep

def fetch_players(season):
    """Fetch all MLB players for a specific season."""
    url = f"https://statsapi.mlb.com/api/v1/sports/1/players?season={season}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('people', [])
    else:
        print(f"Error fetching players list: {response.status_code}")
        return []

def fetch_player_details(player_id):
    """Fetch detailed information for a specific player."""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('people', [{}])[0]
    else:
        print(f"Error fetching player {player_id} details: {response.status_code}")
        return {}

def main():
    # Set the season
    season = 2024
    
    # Fetch all players
    print(f"Fetching players for {season} season...")
    players = fetch_players(season)
    print(f"Found {len(players)} players")
    
    # Create a list to store detailed player information
    detailed_players = []
    
    # Fetch details for each player
    for i, player in enumerate(players, 1):
        print(f"Fetching details for player {i}/{len(players)}: {player.get('fullName', 'Unknown')}")
        player_details = fetch_player_details(player['id'])
        if player_details:
            detailed_players.append(player_details)
        # Add a small delay to avoid overwhelming the API
        sleep(0.5)
    
    # Save the data to a JSON file
    filename = f"mlb_players_{season}_from_api.json"
    
    with open(filename, 'w') as f:
        json.dump(detailed_players, f, ensure_ascii=False, indent=4)
    
    print(f"\nData saved to {filename}")
    print(f"Total players processed: {len(detailed_players)}")

if __name__ == "__main__":
    main()