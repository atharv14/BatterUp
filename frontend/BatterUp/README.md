# BatterUp MLB Frontend

A React-based frontend for a baseball card game that provides an interactive MLB gameplay experience.

## Overview

This frontend application provides:
- Interactive baseball gameplay interface
- Real-time game state visualization
- Deck building and management
- Player statistics and card viewing
- Authentication and user management

## Tech Stack

- **Framework**: React
- **Authentication**: Firebase Auth
- **State Management**: React Context
- **Styling**: CSS

## Features

### Authentication
- Firebase Authentication integration
- Protected routes
- User profile management

### Deck Building
- Interactive deck builder
- Player card visualization
- Deck validation
- Position requirements:
  - 1 Catcher
  - 5 Pitchers
  - 4 Infielders
  - 3 Outfielders
  - 4 Hitters

### Gameplay Interface
- Real-time game state display
- Baseball field visualization
- Interactive pitch selection
- Batting interface
- Base runner visualization
- Score tracking
- Inning management

### Player Cards
- Player statistics display
- Card abilities visualization
- Player images and information

## Game Flow

1. Game Creation/Joining
   - Create new game
   - Join existing game
   - Deck selection

2. Gameplay
   - Pitcher turn
     - Pitch style selection
     - Animation
   - Batter turn
     - Hit style selection
     - Outcome animation
   - Base running visualization
   - Score updates

3. Game Completion
   - Final score display
   - Statistics summary
   - Return to lobby

4. Forfeit Game