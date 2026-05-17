"""
Authentication API routes - Login and Token Refresh
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import auth
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_refresh_token(subject: str) -> str:
    """Create a refresh token with longer expiration."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    import jwt
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def verify_refresh_token(token: str) -> str | None:
    """Verify refresh token and return user_id."""
    if not settings.secret_key:
        logger.warning("SECRET_KEY not configured - refresh token verification skipped")
        return None

    try:
        import jwt
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return access + refresh tokens.
    For MVP, uses simple email/password check against environment users.
    """
    if not settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )

    valid_users = [
        {"email": "admin@agentic-crm.com", "password": "admin123", "id": "1"},
    ]

    user = None
    for u in valid_users:
        if u["email"] == request.email and u["password"] == request.password:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = auth.create_access_token(subject=user["id"])
    refresh_token = create_refresh_token(subject=user["id"])

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(request: RefreshRequest):
    """
    Exchange a valid refresh token for a new access token.
    """
    user_id = verify_refresh_token(request.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = auth.create_access_token(subject=user_id)

    return RefreshResponse(
        access_token=access_token,
        expires_in=30 * 60,
    )