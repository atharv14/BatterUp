# BatterUp MLB Game

An interactive baseball card game that simulates MLB gameplay using real player statistics and dynamic game mechanics.

## Quick Links
- [Backend Documentation](functions/backend/README.MD)
- [Frontend Documentation](frontend/BatterUp/README.md)

## Overview

BatterUp MLB is a full-stack web application that allows users to:
- Build custom decks using MLB player cards
- Play real-time baseball games against other users
- Experience dynamic gameplay with pitch-by-pitch mechanics
- Track game statistics and history

### Key Features
- Card-based gameplay system
- Real MLB player statistics integration
- Dynamic game commentary
- Real-time multiplayer support
- Detailed game statistics tracking

## Tech Stack

### Frontend
- React
- Firebase Authentication
- CSS
- TypeScript

### Backend
- FastAPI
- Firebase/Firestore
- Google Cloud Platform
- Python

## Game Mechanics

### Deck Building
Each player must construct a deck with:
- 1 Catcher
- 5 Pitchers
- 4 Infielders
- 3 Outfielders
- 4 Hitters

### Gameplay Flow
1. Pitch Selection
   - Choose pitching style
   - Ball/Strike count system
2. Batting
   - Select hitting approach
   - Outcome based on player stats
3. Base Running
   - Automatic advancement
   - Run scoring

## Getting Started

1. Clone the repository
```bash
git clone [https://github.com/atharv14/BatterUp.git]
cd batterup-mlb
```

2. Set up environment
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend/BatterUp
npm install
```

3. Configure environment variables
```bash
# Backend (.env)
FIREBASE_CREDENTIALS_PATH=path/to/credentials.json
FIREBASE_STORAGE_BUCKET=batterup-mlb-hack.firebasestorage.app
GOOGLE_API_KEY=your-api-key

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_FIREBASE_CONFIG=your-firebase-config
```

4. Start development servers
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend/BatterUp
npm start
```

## Acknowledgments

- MLB Stats API
- Firebase/Google Cloud Platform
- Open source contributors