from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.endpoints import auth, players, games, users

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

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to BatterUp MLB API"}


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
