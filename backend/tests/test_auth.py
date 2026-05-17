"""
Tests for Auth API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login returns tokens."""
    from app.api.auth import login, LoginRequest

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
    from app.api.auth import login, LoginRequest
    from fastapi import HTTPException

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
    from app.api.auth import login, LoginRequest
    from fastapi import HTTPException

    request = LoginRequest(email="admin@agentic-crm.com", password="admin123")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = ""

        with pytest.raises(HTTPException) as exc_info:
            await login(request)

        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_refresh_success():
    """Test successful token refresh."""
    from app.api.auth import refresh, RefreshRequest

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"

        import jwt
        from datetime import datetime, timedelta, timezone
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        payload = {
            "sub": "1",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
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
    from app.api.auth import refresh, RefreshRequest
    from fastapi import HTTPException

    request = RefreshRequest(refresh_token="invalid-token")

    with patch('app.api.auth.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"

        with pytest.raises(HTTPException) as exc_info:
            await refresh(request)

        assert exc_info.value.status_code == 401