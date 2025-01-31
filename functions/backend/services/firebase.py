from firebase_admin import credentials, firestore, auth, initialize_app
from core.config import settings
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        initialize_app(cred)
        db = firestore.client()
        print("🔥 Firestore DB Initialized Successfully")
        return db
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        raise

# Initialize Firestore DB
db = init_firebase()

def verify_firebase_token(id_token: str):
    """
    Verifies Firebase ID Token and returns decoded user info.
    
    :param id_token: Firebase Authentication Token
    :return: Decoded user claims if token is valid, else None
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # Returns user details (UID, email, etc.)
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        return None
