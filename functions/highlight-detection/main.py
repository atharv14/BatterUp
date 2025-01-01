# Updated highlight-detection/main.py
import functions_framework
from google.cloud import firestore
import json
import requests
import google.generativeai as genai
from vertexai.language_models import TextGenerationModel
import vertexai
import os

# Initialize clients
db = firestore.Client()
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

# Initialize Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # We'll set this when deploying
genai.configure(api_key=GOOGLE_API_KEY)

def get_game_plays(game_pk):
    """Fetch game plays from MLB GUMBO API"""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch game data: {response.status_code}")
    
    game_data = response.json()
    return {
        'plays': game_data.get('liveData', {}).get('plays', {}).get('allPlays', []),
        'game_info': game_data.get('gameData', {}),
        'teams': game_data.get('gameData', {}).get('teams', {})
    }

def analyze_play_importance(play_data, game_info):
    """Analyze play importance using Gemini"""
    # Configure the model
    model = genai.GenerativeModel('gemini-pro')
    
    # Extract relevant play information
    inning = play_data.get('about', {}).get('inning', 0)
    is_scoring_play = play_data.get('about', {}).get('isScoringPlay', False)
    rbi = play_data.get('result', {}).get('rbi', 0)
    description = play_data.get('result', {}).get('description', '')
    
    prompt = f"""
    Rate this baseball play's importance from 0 to 1 (1 being most important):
    
    Description: {description}
    Inning: {inning}
    Is Scoring Play: {is_scoring_play}
    RBI: {rbi}
    
    Return only a number between 0 and 1.
    """
    
    try:
        response = model.generate_content(prompt)
        try:
            score = float(response.text.strip())
            return min(max(score, 0), 1)
        except:
            return 0.5 if is_scoring_play else 0.3
    except Exception as e:
        print(f"Error calling Gemini: {str(e)}")
        return 0.5 if is_scoring_play else 0.3

@functions_framework.http
def process_play(request):
    """Cloud Function entry point"""
    try:
        request_json = request.get_json()
        
        if not request_json:
            return 'No data provided', 400
        
        game_pk = request_json.get('game_pk')
        if not game_pk:
            return 'Missing game_pk parameter', 400
        
        # Get all game plays
        game_data = get_game_plays(game_pk)
        plays = game_data['plays']
        
        # Process each play
        highlights = []
        for play in plays:
            importance_score = analyze_play_importance(play, game_data['game_info'])
            
            if importance_score > 0.6:  # Highlight-worthy threshold
                # Store highlight
                highlight_ref = db.collection('highlights').document()
                highlight_data = {
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'game_pk': str(game_pk),
                    'play_index': play.get('about', {}).get('atBatIndex'),
                    'importance_score': importance_score,
                    'description': play.get('result', {}).get('description', ''),
                    'is_scoring_play': play.get('about', {}).get('isScoringPlay', False),
                    'inning': play.get('about', {}).get('inning', 0),
                    'teams': {
                        'home': game_data['teams'].get('home', {}).get('name', ''),
                        'away': game_data['teams'].get('away', {}).get('name', '')
                    },
                    'players': {
                        'batter': play.get('matchup', {}).get('batter', {}).get('fullName', ''),
                        'pitcher': play.get('matchup', {}).get('pitcher', {}).get('fullName', '')
                    },
                    'processed': False
                }
                highlight_ref.set(highlight_data)
                highlights.append({
                    'highlight_id': highlight_ref.id,
                    'importance_score': importance_score
                })
        
        return json.dumps({
            'success': True,
            'highlights_created': len(highlights),
            'highlights': highlights
        })
        
    except Exception as e:
        print(f'Error processing game: {str(e)}')
        return f'Error: {str(e)}', 500