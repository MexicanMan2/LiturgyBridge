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
engine = create_engine(settings.DATABASE_URL, echo=echo_logs)

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
