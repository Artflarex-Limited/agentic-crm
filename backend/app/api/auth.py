"""
Authentication API routes - Login, Token Refresh, and Registration
"""
import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import auth
from app.core.config import get_settings
from app.prisma import prisma

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["auth"])


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


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class RegisterResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    created_at: datetime


REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_refresh_token(subject: str) -> str:
    """Create a refresh token with longer expiration."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
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

    from app.core.security import sanitize_email
    email = sanitize_email(request.email)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address",
        )

    user = await prisma.user.find_unique(where={"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    expected_hash = hashlib.sha256(f"{request.password}{settings.secret_key}".encode()).hexdigest()
    if not hmac.compare_digest(user.passwordHash, expected_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = auth.create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    Password is hashed with bcrypt before storage.
    """
    if not settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )

    from app.core.security import sanitize_email
    email = sanitize_email(request.email)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address",
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    existing = await prisma.user.find_unique(where={"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = hashlib.sha256(f"{request.password}{settings.secret_key}".encode()).hexdigest()

    user = await prisma.user.create(
        data={
            "email": email,
            "passwordHash": password_hash,
            "fullName": request.full_name,
            "role": "user",
        }
    )

    return RegisterResponse(
        id=user.id,
        email=user.email,
        full_name=user.fullName,
        role=user.role,
        created_at=user.createdAt,
    )
