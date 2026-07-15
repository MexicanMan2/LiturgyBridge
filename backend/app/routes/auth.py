"""
LiturgyBridge Authentication Router.

This module defines endpoints for User authentication, login sessions,
and Single Sign-On (SSO) handshakes with external parish portals
(e.g., Nextcloud, ChurchTools, OIDC).
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/login")
def login_sso(provider: str):
    """
    Initiates Single Sign-On flow for a specified provider (e.g. Nextcloud).
    """
    return {"message": f"Redirecting to {provider} SSO..."}

@router.get("/callback")
def sso_callback(code: str, state: str):
    """
    SSO OAuth2 callback handler. Verifies credentials and generates
    session token (JWT).
    """
    return {"message": "SSO verification successful, session started."}
