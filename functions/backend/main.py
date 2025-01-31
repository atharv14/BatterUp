import sys
import os

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from services.firebase import verify_firebase_token, db 
from core.config import settings
from api.v1.endpoints import players
from api.v1.endpoints import games
from api.v1.endpoints import users

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def get_current_user(authorization: str = Header(None)):
    """
    Dependency that extracts and verifies Firebase token from Authorization header.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = authorization.split("Bearer ")[-1]  # Extract token from "Bearer <token>"
    decoded_token = verify_firebase_token(token)
    
    if not decoded_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    
    return decoded_token 

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Baseball Card Game API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    players.router,
    prefix=f"{settings.API_V1_STR}/players",
    tags=["players"]
)

app.include_router(
    games.router,
    prefix=f"{settings.API_V1_STR}/games",
    tags=["games"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to BatterUp MLB API"}

@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {
        "message": "This is a protected endpoint!",
        "user": {
            "uid": user["uid"],
            "email": user.get("email", "No email"),
            "name": user.get("name", "No name"),
        }
    }

@app.get(f"{settings.API_V1_STR}/")
async def api_root():
    return {
        "version": "1.0",
        "endpoints": {
            "players": f"{settings.API_V1_STR}/players",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }
