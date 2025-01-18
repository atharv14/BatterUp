import functions_framework
from google.cloud import firestore
from google.cloud import storage
import google.generativeai as genai
import json
from datetime import datetime, timedelta
import os

# Initialize clients
db = firestore.Client()
storage_client = storage.Client()
PROJECT_ID = os.getenv('PROJECT_ID')

# Initialize Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

def convert_timestamp(obj):
    """Convert Firestore timestamp to ISO format string"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj

def generate_commentary(highlight_data):
    """Generate commentary using Gemini"""
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Generate exciting baseball commentary for this play:
    Description: {highlight_data['description']}
    Teams: {highlight_data['teams']['away']} vs {highlight_data['teams']['home']}
    Players: {highlight_data['players']['batter']} batting against {highlight_data['players']['pitcher']}
    Inning: {highlight_data.get('inning', '?')}
    
    Generate a short, exciting commentary that captures the moment. Keep it under 50 words. Focus on:
    1. The excitement of the moment
    2. The impact on the game
    3. Any notable achievements
    
    Make it engaging for baseball fans.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating commentary: {str(e)}")
        return highlight_data['description']

def create_digest():
    """Create digests for all users based on their preferences"""
    digest_ids = []
    users_ref = db.collection('users').stream()
    
    for user in users_ref:
        doc_id = user.id  # This is the document ID
        user_data = user.to_dict()
        print(f"Processing digests for user: {doc_id}")
        
        # Get user preferences using doc_id
        prefs = db.collection('user_preferences').document(doc_id).get()
        if not prefs.exists:
            print(f"No preferences found for user {doc_id}")
            continue
            
        prefs_data = prefs.to_dict()
        print(f"User preferences: {prefs_data}")
        
        # Query highlights
        highlights_ref = db.collection('highlights')\
            .where('processed', '==', False)\
            .order_by('importance_score', direction=firestore.Query.DESCENDING)
        
        highlights = list(highlights_ref.stream())
        print(f"Found {len(highlights)} unprocessed highlights")
        
        # Filter highlights
        filtered_highlights = []
        for highlight in highlights:
            highlight_data = highlight.to_dict()
            
            teams = highlight_data.get('teams', {})
            players = highlight_data.get('players', {})
            
            team_match = any(team in teams.values() for team in prefs_data.get('teams', []))
            player_match = any(player in players.values() for player in prefs_data.get('players', []))
            
            if team_match or player_match:
                filtered_highlights.append(highlight)
        
        print(filtered_highlights)
        
        if filtered_highlights:
            print(f"Creating digest for user {doc_id} with {len(filtered_highlights)} highlights")
            digest_id = create_user_digest(doc_id, prefs_data, filtered_highlights)
            if digest_id:
                digest_ids.append(digest_id)
                # Mark highlights as processed
                for highlight in filtered_highlights:
                    highlight.reference.update({'processed': True})
        else:
            print("No highlights match user preferences")
            
    return digest_ids if digest_ids else None

def create_user_digest(user_doc_id, prefs_data, highlights):
    """Create a personalized digest for a specific user"""
    digest_content = []
    
    for highlight in highlights:
        highlight_data = highlight.to_dict()
        commentary = generate_commentary(highlight_data)
        
        digest_content.append({
            'highlight_id': highlight.id,
            'description': highlight_data['description'],
            'commentary': commentary,
            'teams': highlight_data['teams'],
            'players': highlight_data['players'],
            'importance_score': highlight_data['importance_score'],
            'inning': highlight_data.get('inning', 0),
            'timestamp': convert_timestamp(highlight_data.get('timestamp'))
        })
    
    if digest_content:
        # Create digest document
        digest_ref = db.collection('digests').document()
        digest_data = {
            'user_doc_id': user_doc_id,  # Store the document ID instead of user_id
            'created_at': firestore.SERVER_TIMESTAMP,
            'language': prefs_data['language'],
            'highlights': digest_content,
            'status': 'created'
        }
        
        # Store in Cloud Storage
        bucket_name = f"{PROJECT_ID}-digests"
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"digests/{user_doc_id}/{digest_ref.id}.json")
        
        blob.upload_from_string(
            json.dumps(digest_data, default=str),
            content_type='application/json'
        )
        
        # Store reference in Firestore
        digest_data['content_url'] = blob.name
        digest_ref.set(digest_data)
        
        return digest_ref.id
    return None

@functions_framework.cloud_event
def generate_digest(cloud_event):
    """Cloud Function entry point"""
    try:
        print("Starting digest generation...")
        digest_ids = create_digest()
        
        if digest_ids:
            print(f"Created digest with ID: {digest_ids}")
            return json.dumps({
                'success': True,
                'digest_id': digest_ids
            })
        
        print("No new highlights to process")
        return json.dumps({
            'success': True,
            'message': 'No new highlights to process'
        })
        
    except Exception as e:
        print(f'Error generating digest: {str(e)}')
        return f'Error: {str(e)}', 500