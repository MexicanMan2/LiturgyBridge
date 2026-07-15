"""
LiturgyBridge Database Connection Module.

This module initializes the database engine (PostgreSQL/SQLModel) and provides
session generators for routing handlers, ensuring proper resource management.
"""

from sqlmodel import create_engine, Session, SQLModel
from backend.app.config import settings

# Initialize database engine
# echo=True prints raw SQL logs - useful for development debugging
echo_logs = settings.ENV == "development"

# PostgreSQL connection pooling settings to handle concurrent requests
engine = create_engine(
    settings.DATABASE_URL,
    echo=echo_logs,
    pool_size=20,          # Maintain up to 20 persistent connections
    max_overflow=10,       # Allow up to 10 additional temporary overflow connections
    pool_recycle=3600,     # Recycle connections older than 1 hour to prevent stale handles
)

def create_db_and_tables():
    """
    Creates all database tables defined in models.py.
    Should be called during application startup.
    """
    # Import models here to register schemas on SQLModel.metadata
    from backend.app import models  # noqa
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    FastAPI dependency that yields a database session.
    Automatically closes the session after the API request finishes.
    """
    with Session(engine) as session:
        yield session
