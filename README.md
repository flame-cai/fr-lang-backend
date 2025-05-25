# French Language Learning Backend

A Google Cloud Run backend service for a French language learning application that provides conversational practice, vocabulary exercises, and speech recognition features.

## Features

- **Conversation Companion**: AI-powered French conversation practice with weekly curriculum
- **Vocab Vault**: Word meaning review 
- **Grammar Games**: Interactive grammar games with a scoring system
- **Paragraph Parler**: Paragraph reading practice with audio playback
- **Speech Recognition**: Audio transcription and pronunciation checking using OpenAI Whisper
- **Progress Tracking**: User progress tracking and analytics


## Frontend

The frontend for this application is available at: https://github.com/flame-cai/french_AI_bot

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export OPENAI_API_KEY="your_openai_api_key"
export GOOGLE_OAUTH2_CLIENT_ID="your_google_client_id"
export PROJECT_ID="your_gcp_project_id"
export COLLECTION_NAME="your_firestore_collection"
```

3. **Deploy to Google Cloud Run**