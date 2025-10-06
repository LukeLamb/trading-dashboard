"""
Trading Game API
FastAPI backend for Phase 1: Character & Profile System
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from contextlib import asynccontextmanager

# Import database connection
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import DatabaseConnection, check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Trading Game API...")
    DatabaseConnection.initialize()
    logger.info("Database connection initialized")

    yield

    # Shutdown
    logger.info("Shutting down Trading Game API...")
    DatabaseConnection.close()
    logger.info("Database connection closed")

# Create FastAPI app
app = FastAPI(
    title="Trading Game API",
    description="Backend API for the Trading Game - Gamified Trading Education Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Trading Game API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with database status"""
    db_health = check_database_health()

    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "api": "running",
        "database": db_health["status"],
        "message": db_health.get("message", "Database check failed")
    }

# Import and include routers
from api.routes import auth, users, characters

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(characters.router, prefix="/api/characters", tags=["Characters"])

# Additional routers (to be added):
# from api.routes import achievements, social, leaderboard
# app.include_router(achievements.router, prefix="/api/achievements", tags=["Achievements"])
# app.include_router(social.router, prefix="/api/social", tags=["Social"])
# app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
