from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.endpoints import players
from api.v1.endpoints import games

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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
