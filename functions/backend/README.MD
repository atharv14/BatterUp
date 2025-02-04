# BatterUp MLB Backend

## Overview
BatterUp MLB is a baseball game simulation platform that provides a real-time, interactive baseball gaming experience.

## Technology Stack
- Python
- FastAPI
- Firebase Admin SDK
- Google Cloud Text-to-Speech
- Firestore
- Google Generative AI

## Prerequisites
- Python 3.9+
- Firebase account
- Google Cloud account

## API Endpoints

### Authenticatioin
- ```POST /api/v1/auth/register```: User registration
- ```GET /api/v1/auth/me```: Get current user profile
- ```PUT /api/v1/auth/me```: Update current user profile

### Game Management
- ```POST /api/v1/games/create```: Create a new game
- ```POST /api/v1/games/{game_id}/join```: Join an existing game
- ```GET /api/v1/games/{game_id}```: Get game state
- ```POST /api/v1/games/{game_id}/pitch```: Perform pitch action
- ```POST /api/v1/games/{game_id}/bat```: Perform batting action
- ```POST /api/v1/games/{game_id}/forfeit```: Forfeit the game
- ```GET /api/v1/games/{game_id}/history```: Get game history
- ```GET /api/v1/games/{game_id}/commentary```: Get game commentary


### Player Management
- ```GET /api/v1/players/{player_id}```: Get Player
- ```GET /api/v1/players/```: Get Players
- ```GET /api/v1/players/{player_id}/headshot```: Get Player Headshot
- ```GET /api/v1/players/list/deck-selection```: Get Players for deck

## Game Mechanics
### Pitch Styles

Fastballs
Breaking Balls
Changeups

### Hitting Styles

Power Hitter
Switch Hitter
Designated Hitter

### Audio Commentary

Generated using Google Cloud Text-to-Speech
Stored in Firebase Storage
Synchronized with game actions


