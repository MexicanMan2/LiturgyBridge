import os
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import httpx
from sqlmodel import Session, select

from backend.app.database import get_session
from backend.app.models import User

# Load config from environment
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "http://localhost:8080").rstrip("/")
CLIENT_ID = os.getenv("NEXTCLOUD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("NEXTCLOUD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8001/api/v1/auth/callback")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = "HS256"

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/login")
def login_sso():
    if not CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO credentials not configured in backend environment."
        )
    
    # State parameter to prevent CSRF
    state = secrets.token_hex(16)
    
    authorize_url = (
        f"{NEXTCLOUD_URL}/index.php/apps/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )
    return RedirectResponse(authorize_url)

@router.get("/callback")
async def sso_callback(code: str, state: Optional[str] = None, session: Session = Depends(get_session)):
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SSO credentials not configured in backend environment."
        )

    # 1. Exchange code for access token
    token_url = f"{NEXTCLOUD_URL}/index.php/apps/oauth2/api/v1/token"
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
                auth=(CLIENT_ID, CLIENT_SECRET),
                timeout=10.0
            )
            token_response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access token not returned by Nextcloud."
            )

        # 2. Get user info and group memberships
        userinfo_url = f"{NEXTCLOUD_URL}/ocs/v2.php/cloud/user?format=json"
        try:
            user_response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            user_response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch user profile from Nextcloud: {str(e)}"
            )

        user_data = user_response.json()
        ocs_data = user_data.get("ocs", {}).get("data", {})
        
        user_id = ocs_data.get("id")
        email = ocs_data.get("email") or f"{user_id}@nextcloud.local"
        display_name = ocs_data.get("displayname") or user_id
        groups = ocs_data.get("groups", [])

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve user ID from Nextcloud profile."
            )

        # 3. Map groups to roles
        mapped_roles = []
        if "admin" in groups:
            mapped_roles.append("admin")
            mapped_roles.append("editor")
        if "clergy" in groups or "priests" in groups:
            mapped_roles.append("priest")
        if "choir" in groups:
            mapped_roles.append("choir")
        if not mapped_roles:
            mapped_roles.append("member")

        # 4. Save/Update User in Database
        db_user = session.exec(
            select(User).where((User.email == email) | (User.external_user_id == user_id))
        ).first()

        if not db_user:
            db_user = User(
                name=display_name,
                email=email,
                sso_provider="nextcloud",
                external_user_id=user_id,
                global_roles=mapped_roles,
                preferred_language="de"
            )
            session.add(db_user)
        else:
            db_user.name = display_name
            db_user.global_roles = mapped_roles
            session.add(db_user)
            
        session.commit()
        session.refresh(db_user)

        # 5. Generate local JWT Token
        payload = {
            "sub": str(db_user.id),
            "email": db_user.email,
            "roles": db_user.global_roles,
            "name": db_user.name,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # 6. Redirect back to frontend callback with token
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(REDIRECT_URI)
        frontend_netloc = parsed.netloc.split(":")[0] + ":5173"
        frontend_callback_url = urlunparse((
            parsed.scheme,
            frontend_netloc,
            "/auth/callback",
            "",
            f"token={jwt_token}",
            ""
        ))
        
        return RedirectResponse(frontend_callback_url)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Decodes the local JWT token and resolves the corresponding User from the database.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing sub claim."
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials."
        )
        
    db_user = session.get(User, uuid.UUID(user_id))
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return db_user

