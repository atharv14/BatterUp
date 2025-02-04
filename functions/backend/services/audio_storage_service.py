import base64
import uuid
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import storage
from core.config import settings
from services.firebase import bucket


class AudioStorageService:

    @staticmethod
    def initialize_storage():
        """
        Initialize Firebase Storage with bucket name from settings
        """
        try:
            print("Initializing Firebase storage...")

            # Check if app is already initialized
            if not firebase_admin._apps:
                print("Firebase not initialized. Initializing now...")
                cred = credentials.Certificate(
                    settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
            else:
                print("Firebase already initialized.")
            return storage.bucket()
            # client = storage.Client()
            # buckets = list(client.list_buckets())

            # print("Available Buckets:")
            # for bucket in buckets:
            #     print(bucket.name)
            # return client.bucket(settings.FIREBASE_STORAGE_BUCKET)
        except Exception as e:
            print(f"Error initializing storage: {e}")
            return None

    @staticmethod
    async def upload_audio_commentary(game_id: str, audio_base64: str) -> str:
        """
        Upload audio commentary to Firebase Storage

        Args:
            game_id: ID of the game
            audio_base64: Base64 encoded audio content

        Returns:
            Public URL of the uploaded audio
        """
        try:

            # # Initialize bucket
            # bucket = AudioStorageService.initialize_storage()

            if not bucket:
                raise ValueError("❌ Firebase Storage bucket not initialized")

            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_base64)

            # Generate unique filename
            filename = f"commentaries/{game_id}/{uuid.uuid4()}.mp3"

            # Upload file to Firebase Storage
            blob = bucket.blob(filename)
            blob.upload_from_string(audio_bytes, content_type="audio/mp3")

            # Make the file publicly accessible
            blob.make_public()

            return blob.public_url

        except Exception as e:
            print(f"Error uploading audio: {e}")
            return None

    @staticmethod
    async def cleanup_old_audio_files(game_id: str, days_to_keep: int = 7):
        """
        Clean up old audio files for a specific game

        Args:
            game_id: ID of the game
            days_to_keep: Number of days to keep audio files
        """
        try:
            if not bucket:
                raise ValueError("❌ Firebase Storage bucket not initialized")

            blobs = bucket.list_blobs(prefix=f"commentaries/{game_id}/")
            current_time = datetime.utcnow()

            for blob in blobs:
                blob_age = current_time - blob.updated
                if blob_age > timedelta(days=days_to_keep):
                    blob.delete()
                    print(f"🗑 Deleted old audio file: {blob.name}")

        except Exception as e:
            print(f"Error cleaning up audio files: {e}")
