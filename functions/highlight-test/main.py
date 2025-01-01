# Create highlight-test/main.py
import functions_framework
from google.cloud import firestore
import json

db = firestore.Client()

@functions_framework.http
def create_test_highlight(request):
    """Create a test highlight with processed=false"""
    highlight_ref = db.collection('highlights').document()
    
    highlight_data = {
        'description': "Shohei Ohtani hits a grand slam (45) to deep center field. Mike Trout scores. Taylor Ward scores. Brandon Drury scores.",
        'game_pk': "716465",
        'importance_score': 0.9,
        'inning': 7,
        'is_scoring_play': True,
        'play_index': 52,
        'players': {
            'batter': "Shohei Ohtani",
            'pitcher': "Sonny Gray"
        },
        'processed': False, 
        'teams': {
            'away': "Los Angeles Angels",
            'home': "Minnesota Twins"
        },
        'timestamp': firestore.SERVER_TIMESTAMP
    }
    
    highlight_ref.set(highlight_data)
    
    return json.dumps({
        'success': True,
        'highlight_id': highlight_ref.id
    })