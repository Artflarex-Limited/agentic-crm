"""
JWT Authentication Middleware
Shared auth for all FastAPI microservices.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    iat: int | None = None
    role: str | None = None


class AuthMiddleware:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def create_access_token(
        self,
        subject: str,
        role: str = "user",
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        to_encode: dict[str, Any] = {
            "sub": str(subject),
            "exp": expire,
            "iat": now,
            "role": role,
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenPayload | None:
        """Verify and decode a JWT token."""
        if not self.secret_key:
            logger.warning("SECRET_KEY not configured - token verification skipped")
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> dict[str, Any] | None:
        """Extract current user from JWT token."""
        if not credentials:
            return None

        token = credentials.credentials
        payload = self.verify_token(token)

        if not payload or not payload.sub:
            return None

        return {
            "user_id": payload.sub,
            "role": payload.role,
        }


auth = AuthMiddleware()


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = security,
) -> dict[str, Any]:
    """Dependency for protected routes."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = auth.verify_token(token)

    if not payload or not payload.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": payload.sub,
        "role": payload.role,
    }


async def optional_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = security,
) -> dict[str, Any] | None:
    """Dependency for routes that work with or without auth."""
    return await auth.get_current_user(credentials)


def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    async def role_checker(request: Request, credentials: HTTPAuthorizationCredentials = security):
        user = await require_auth(request, credentials)
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user
    return role_checker