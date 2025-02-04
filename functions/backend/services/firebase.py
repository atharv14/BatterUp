import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, storage
from core.config import settings
import os


def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # 🔹 Update with your actual path
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            # 🔹 Ensure this matches your bucket name
            "storageBucket": "batterup-mlb-hack.firebasestorage.app"
        })

        # Initialize Firebase Storage bucket (Global Variable)
        bucket = storage.bucket()
        db = firestore.client()
        return db, bucket
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise


# Initialize Firestore DB
db, bucket = init_firebase()
if db:
    print("DB Initialized successfully")
if bucket:
    print("Bucket Initialized successfully")
