## Step 1. Initial Setup
- ```brew install google-cloud-sdk```
- ```gcloud auth login```
- ```gcloud projects create "unique_project_id" --name=""project_name""```
- ```gcloud config set project "unique_project_id"```
- #enable services ```gcloud services enable \
    aiplatform.googleapis.com \
    translate.googleapis.com \
    cloudfunctions.googleapis.com \
    storage.googleapis.com \
    pubsub.googleapis.com \
    firestore.googleapis.com \
    cloudbuild.googleapis.com```
- #service account ```gcloud iam service-accounts create batterup-service \
    --display-name="BatterUp Service Account"```
- #necessary permission ```gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:batterup-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"```
- #storage buckets ```gsutil mb gs://$PROJECT_ID-highlights
    gsutil mb gs://$PROJECT_ID-user-digests
    gsutil mb gs://$PROJECT_ID-temp```
- #CORS policy ```cat > cors.json << EOL
[
    {
        "origin": ["*"],
        "method": ["GET"],
        "maxAgeSeconds": 3600
    }
]
EOL```
```gsutil cors set cors.json gs://$PROJECT_ID-highlights```

## Step 2. Setup Firestore
- Create new database using firestore from google cloud console
- Create new collection called "users"
    - Create a test document with ID 'test_user'
    - Add fields:
        - email (string)
        - display_name (string)
        - followed_teams (array)
        - followed_players (array)
        - preferred_language (string)
- Create new collection called "user_preferences"
    - Create a test document with ID 'test_user'
    - Add fields:
        - teams (array)
        - players (array)
        - language (string)
        - digest_frequency (map)
- Let the Cloud Function populate collection called "user_highlights"
- Let the Cloud Function populate collection called "digests"
- Let the Cloud Function populate collection called "highlights"

## Step 3. Writing and deploying basic cloud functions for highlight-detection and digest-generator

## Step 4. Testing the basic deployment  with curl and CLI commands
- #curl for highlight ```curl -X POST https://us-central1-[$PROJECT_ID].cloudfunctions.net/highlight-detection \
  -H "Content-Type: application/json" \
  -d '{"game_pk": "123", "play_id": "456"}'```
    - response: ```{"success": true, "message": "Processed successfully"}```
- #command for digest ```gcloud pubsub topics publish generate-digest --message="generate_digest_test"```
    - response: ```messageIds:'13398670210125928'```

Note - always ignore one set of quotes