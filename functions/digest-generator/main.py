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
    """Create digest from recent highlights"""
    highlights_ref = db.collection('highlights')\
        .order_by('importance_score', direction=firestore.Query.DESCENDING)\
        .limit(10)
    
    print("Querying for highlights...")
    highlights = list(highlights_ref.stream())
    print(f"Found {len(highlights)} highlights")
    
    digest_content = []
    
    for highlight in highlights:
        highlight_data = highlight.to_dict()
        print(f"Processing highlight: {highlight.id}") 
        commentary = generate_commentary(highlight_data)
        
        # Convert timestamp to string format
        if 'timestamp' in highlight_data:
            highlight_data['timestamp'] = convert_timestamp(highlight_data['timestamp'])
        
        digest_content.append({
            'highlight_id': highlight.id,
            'description': highlight_data['description'],
            'commentary': commentary,
            'teams': highlight_data['teams'],
            'players': highlight_data['players'],
            'importance_score': highlight_data['importance_score'],
            'inning': highlight_data.get('inning', 0),
            'timestamp': highlight_data.get('timestamp')
        })
        
        # Mark highlight as processed
        highlight.reference.update({'processed': True})
    
    if digest_content:
        try:
            # Store digest in Firestore
            digest_ref = db.collection('digests').document()
            current_time = datetime.now().isoformat()
            
            digest_data = {
                'created_at': firestore.SERVER_TIMESTAMP,
                'highlights': digest_content,
                'status': 'created'
            }
            
            # Store full content in Cloud Storage
            bucket_name = f"{PROJECT_ID}-digests"
            try:
                bucket = storage_client.get_bucket(bucket_name)
            except Exception as e:
                print(f"Creating bucket {bucket_name}")
                bucket = storage_client.create_bucket(bucket_name, location="us-central1")

            blob = bucket.blob(f"digests/{digest_ref.id}.json")
            
            # Convert digest content to JSON-serializable format
            storage_content = {
                'created_at': current_time,
                'highlights': digest_content,
                'status': 'created'
            }
            
            blob.upload_from_string(
                json.dumps(storage_content),
                content_type='application/json'
            )
            
            # Add storage reference to Firestore
            digest_data['content_url'] = f"gs://{PROJECT_ID}-digests/digests/{digest_ref.id}.json"
            digest_ref.set(digest_data)
            
            print(f"Successfully created digest {digest_ref.id}")
            return digest_ref.id
        
        except Exception as e:
            print(f"Error creating digest: {str(e)}")
            raise e
    
    return None

@functions_framework.cloud_event
def generate_digest(cloud_event):
    """Cloud Function entry point"""
    try:
        print("Starting digest generation...")
        digest_id = create_digest()
        
        if digest_id:
            print(f"Created digest with ID: {digest_id}")
            return json.dumps({
                'success': True,
                'digest_id': digest_id
            })
        
        print("No new highlights to process")
        return json.dumps({
            'success': True,
            'message': 'No new highlights to process'
        })
        
    except Exception as e:
        print(f'Error generating digest: {str(e)}')
        return f'Error: {str(e)}', 500