"""
LiturgyBridge Configuration Module.

This module defines the system settings and environment variables needed
to run the application. It loads configurations for database connections,
Single Sign-On (SSO) clients, external AI APIs, and local server base URLs.
"""

from typing import Optional
import os
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

class Settings:
    # 1. Server Configuration
    PROJECT_NAME: str = "LiturgyBridge"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    ENV: str = os.getenv("ENV", "development")

    # 2. Database Configuration
    # Fallback to local postgres or SQLite if postgres is not configured
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/liturgybridge"
    )

    # 3. Security & Auth (SSO)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_session_token_key")
    NEXTCLOUD_SSO_CLIENT_ID: Optional[str] = os.getenv("NEXTCLOUD_SSO_CLIENT_ID")
    NEXTCLOUD_SSO_CLIENT_SECRET: Optional[str] = os.getenv("NEXTCLOUD_SSO_CLIENT_SECRET")
    CHURCHTOOLS_API_KEY: Optional[str] = os.getenv("CHURCHTOOLS_API_KEY")

    # 4. Translation & AI APIs
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEEPL_API_KEY: Optional[str] = os.getenv("DEEPL_API_KEY")

# Instantiate settings singleton
settings = Settings()
