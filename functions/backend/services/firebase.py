from firebase_admin import credentials, firestore, initialize_app
from core.config import settings
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        initialize_app(cred)
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

# Initialize Firestore DB
db = init_firebase()
if db:
    print("DB Initialized successfully")
