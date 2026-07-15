"""
LiturgyBridge FastAPI Entrypoint.

This module bootstraps the FastAPI application, registers middleware (CORS, safety),
includes sub-routers for different resources (auth, community, liturgy, sync),
and manages lifecycle events (like database table auto-creation on startup).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(f"Starting {settings.PROJECT_NAME} in environment: {settings.ENV}")
    # Auto-create tables (in development)
    create_db_and_tables()
    yield
    # Shutdown actions
    print(f"Stopping {settings.PROJECT_NAME}...")

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Digital multilingual companion for Orthodox worship",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up CORS middleware to allow connection from Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Routers
from backend.app.routes import auth, community, liturgy, sync, wiki

# Include Routers with API prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(community.router, prefix="/api/v1")
app.include_router(liturgy.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(wiki.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "healthy",
        "api_documentation": "/docs"
    }
