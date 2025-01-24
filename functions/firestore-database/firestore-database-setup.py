import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime
import os

def initialize_firestore():
    """Initialize Firestore with default database."""
    try:
        cred_path = 'firebase-service-account-key.json'

        if not os.path.exists(cred_path):
            print(f"Error: Credentials file not found at {cred_path}")
            return None

        cred = credentials.Certificate(cred_path)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        # Initialize client (will use default database)
        db = firestore.client()
        print("Firestore initialized successfully with default database")

        # Test connection
        test_ref = db.collection('test').document('test')
        test_ref.set({'test': 'test'})
        print("Test write successful")

        return db
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        print(f"Credential path tried: {os.path.abspath(cred_path)}")
        return None

def upload_player_cards(db, player_cards: dict):
    """Upload player cards to Firestore with progress tracking."""
    if not db:
        print("Database connection not initialized")
        return False
        
    total_players = len(player_cards)
    print(f"Starting upload of {total_players} players")
    
    try:
        # Upload in batches of 500
        batch_size = 500
        players_processed = 0
        
        while players_processed < total_players:
            # Create new batch
            batch = db.batch()
            
            # Process current batch
            current_batch_players = list(player_cards.items())[players_processed:players_processed + batch_size]
            
            for player_id, card_data in current_batch_players:
                doc_ref = db.collection('players').document(str(player_id))
                batch.set(doc_ref, card_data)
            
            # Commit batch
            batch.commit()
            
            players_processed += len(current_batch_players)
            print(f"Processed {players_processed}/{total_players} players")
        
        print("Upload completed successfully")
        return True
        
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        return False

def main():
    # Initialize Firestore
    print("Initializing Firestore...")
    db = initialize_firestore()
    
    if not db:
        print("Failed to initialize database")
        return
        
    # Load player cards
    print("Loading player cards from file...")
    try:
        with open('../Custom Player Stats Data/processed_data/player_cards.json', 'r', encoding='utf-8') as f:
            player_cards = json.load(f)
            print(f"Loaded {len(player_cards)} player cards")
    except Exception as e:
        print(f"Error loading player cards: {e}")
        return
    
    # Upload data
    print("Starting upload process...")
    success = upload_player_cards(db, player_cards)
    
    if success:
        print("Upload process completed successfully")
        
        # Update metadata
        try:
            meta_ref = db.collection('players').document('metadata')
            meta_ref.set({
                'total_players': len(player_cards),
                'last_updated': firestore.SERVER_TIMESTAMP
            })
            print("Metadata updated successfully")
        except Exception as e:
            print(f"Error updating metadata: {e}")
    else:
        print("Upload process failed")

if __name__ == "__main__":
    main()