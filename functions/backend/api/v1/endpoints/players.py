from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from models.schemas.player import PlayerCard, PlayerList
from services.firebase import db
from google.cloud.firestore import FieldFilter

router = APIRouter()


@router.get("/{player_id}", response_model=PlayerCard)
async def get_player(player_id: str):
    """Get a specific player by ID"""
    try:
        doc_ref = db.collection('players').document(str(player_id))
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found"
            )

        player_data = doc.to_dict()
        # Ensure player_id is string in response
        player_data['player_id'] = str(player_data['player_id'])
        return player_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving player: {str(e)}"
        )


@router.get("/", response_model=PlayerList)
async def get_players(
    role: Optional[str] = Query(None, description="Filter by role"),
    team: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get players with filters"""
    try:
        query = db.collection('players')

        # Don't query the metadata document
        query = query.where('player_id', '!=', 'metadata')

        # Apply filters if provided
        if role:
            query = query.where('role_info.primary_role', '==', role)
        if team:
            query = query.where('basic_info.team', '==', team)
        if position:
            query = query.where('basic_info.primary_position', '==', position)

        # Execute query
        docs = query.stream()

        # Convert to list and ensure player_id is string
        players = []
        for doc in docs:
            player_data = doc.to_dict()
            player_data['player_id'] = str(player_data['player_id'])
            players.append(player_data)

        # Apply pagination
        total = len(players)
        paginated_players = players[offset:offset + limit]

        return PlayerList(players=paginated_players, total=total)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving players: {str(e)}"
        )


@router.get("/{player_id}/headshot")
async def get_player_headshot(player_id: str):
    """Get player's headshot URL"""
    try:
        # Get player document to verify existence
        doc_ref = db.collection('players').document(str(player_id))
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found"
            )

        player_data = doc.to_dict()
        headshot_url = player_data.get('basic_info', {}).get('headshot_url')

        if not headshot_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Headshot URL not found for player"
            )

        # Option 1: Return the URL directly
        return JSONResponse({
            "url": headshot_url,
            "player_id": str(player_id)
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving headshot: {str(e)}"
        )


@router.get("/list/deck-selection", response_model=List[PlayerCard])
async def get_players_for_deck(
    position: Optional[str] = Query(None, description="Filter by position")
):
    """Get players suitable for deck selection"""
    try:
        if position:
            query = (
                db.collection('players')
                .where(filter=FieldFilter("basic_info.primary_position", "==", position))
            )
        else:
            query = db.collection('players')

        # Get all documents
        docs = query.stream()
        players = []

        # Process documents synchronously since Firebase Admin doesn't support async iteration
        for doc in docs:
            player_data = doc.to_dict()
            if player_data and 'player_id' in player_data and player_data['player_id'] != 'metadata':
                # Ensure player_id is string
                player_data['player_id'] = str(player_data['player_id'])
                players.append(player_data)

        return players

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving players: {str(e)}"
        )
