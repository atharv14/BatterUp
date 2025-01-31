import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime
import os
from backend.core.config import settings

def initialize_firestore():
    """Initialize Firestore with default database."""
    try:
        print(settings.FIREBASE_CREDENTIALS_PATH)
        cred_path = settings.FIREBASE_CREDENTIALS_PATH

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
    
def validate_player_card(card_data: dict) -> bool:
    """
    Validate player card data before upload.
    """
    required_fields = [
        'player_id', 'basic_info', 'batting_abilities', 
        'pitching_abilities', 'fielding_abilities', 'role_info'
    ]

    try:
        # Check required fields
        for field in required_fields:
            if field not in card_data:
                print(f"Missing required field: {field}")
                return False

        # Validate role_info structure
        role_info = card_data.get('role_info', {})
        if not role_info.get('primary_role'):
            print("Missing primary_role in role_info")
            return False

        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

def create_role_based_metadata(db, player_cards: dict):
    """
    Create role-based metadata for querying.
    """
    try:
        role_stats = {
            'Pitcher': 0,    # Changed from 'pitcher'
            'Hitter': 0,     # Changed from 'hitter'
            'Infielder': 0,  # Changed from 'infielder'
            'Outfielder': 0, # Changed from 'outfielder'
            'Catcher': 0,    # Changed from 'catcher'
            'pitching_styles': {
                'Fastballs': 0,
                'Breaking Balls': 0,
                'Changeups': 0
            },
            'hitting_styles': {
                'Power Hitter': 0,
                'Switch Hitter': 0,
                'Designated Hitter': 0
            }
        }
        
        # Count players by role
        for card in player_cards.values():
            role_info = card.get('role_info', {})
            primary_role = role_info.get('primary_role')
            
            if primary_role:
                role_stats[primary_role] += 1
            
            # Count pitching styles
            if 'pitching_styles' in role_info:
                for style in role_info['pitching_styles']:
                    role_stats['pitching_styles'][style] += 1
                    
            # Count hitting styles
            if 'hitting_styles' in role_info:
                for style in role_info['hitting_styles']:
                    role_stats['hitting_styles'][style] += 1
        
        # Upload metadata
        meta_ref = db.collection('players').document('role_metadata')
        meta_ref.set({
            'role_distribution': role_stats,
            'last_updated': firestore.SERVER_TIMESTAMP
        })
        
        print("Role-based metadata created successfully")
        return True
    except Exception as e:
        print(f"Error creating role metadata: {e}")
        return False

def upload_player_cards(db, player_cards: dict):
    """Upload player cards to Firestore with validation and progress tracking."""
    if not db:
        print("Database connection not initialized")
        return False
        
    total_players = len(player_cards)
    print(f"Starting upload of {total_players} players")
    
    try:
        # Upload in batches of 500
        batch_size = 500
        players_processed = 0
        invalid_cards = []
        
        while players_processed < total_players:
            # Create new batch
            batch = db.batch()
            
            # Process current batch
            current_batch_players = list(player_cards.items())[players_processed:players_processed + batch_size]
            
            for player_id, card_data in current_batch_players:
                # Validate card data
                if validate_player_card(card_data):
                    doc_ref = db.collection('players').document(str(player_id))
                    batch.set(doc_ref, card_data)
                else:
                    invalid_cards.append(player_id)
            
            # Commit batch
            batch.commit()
            
            players_processed += len(current_batch_players)
            print(f"Processed {players_processed}/{total_players} players")
        
        if invalid_cards:
            print(f"Warning: {len(invalid_cards)} invalid cards found: {invalid_cards}")
        
        # Create role-based metadata
        create_role_based_metadata(db, player_cards)
        
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
        with open('Custom Player Stats Data/processed_data/player_cards.json', 'r', encoding='utf-8') as f:
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
                'last_updated': firestore.SERVER_TIMESTAMP,
                'data_version': '2.0'
            })
            print("Metadata updated successfully")
        except Exception as e:
            print(f"Error updating metadata: {e}")
    else:
        print("Upload process failed")

if __name__ == "__main__":
    main()