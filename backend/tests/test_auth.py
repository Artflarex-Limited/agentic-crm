"""
Tests for Auth API endpoints
"""
from datetime import UTC
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login returns tokens."""
    from app.api.auth import LoginRequest, login

    request = LoginRequest(email="admin@agentic-crm.com", password="admin123")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"
        mock_settings.smtp_user = "test@test.com"

        response = await login(request)

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "bearer"
        assert response.expires_in == 30 * 60


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials returns 401."""
    from fastapi import HTTPException

    from app.api.auth import LoginRequest, login

    request = LoginRequest(email="wrong@email.com", password="wrongpass")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"
        mock_settings.smtp_user = "test@test.com"

        with pytest.raises(HTTPException) as exc_info:
            await login(request)

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_no_secret_key():
    """Test login when secret key not configured."""
    from fastapi import HTTPException

    from app.api.auth import LoginRequest, login

    request = LoginRequest(email="admin@agentic-crm.com", password="admin123")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = ""

        with pytest.raises(HTTPException) as exc_info:
            await login(request)

        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_refresh_success():
    """Test successful token refresh."""
    from app.api.auth import RefreshRequest, refresh

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"

        from datetime import datetime, timedelta

        import jwt
        expire = datetime.now(UTC) + timedelta(days=7)
        payload = {
            "sub": "1",
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }
        refresh_token = jwt.encode(payload, "test-secret-key", algorithm="HS256")

        request = RefreshRequest(refresh_token=refresh_token)
        response = await refresh(request)

        assert response.access_token is not None
        assert response.token_type == "bearer"
        assert response.expires_in == 30 * 60


@pytest.mark.asyncio
async def test_refresh_invalid_token():
    """Test refresh with invalid token returns 401."""
    from fastapi import HTTPException

    from app.api.auth import RefreshRequest, refresh

    request = RefreshRequest(refresh_token="invalid-token")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"

        with pytest.raises(HTTPException) as exc_info:
            await refresh(request)

        assert exc_info.value.status_code == 401
