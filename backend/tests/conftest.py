import os
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import jwt

# Set dummy env vars for testing before importing app settings
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "dummy-service-role-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-key-for-testing-12345"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["ENVIRONMENT"] = "test"

from app.config import get_settings
from app.core.dependencies import get_auth_service, get_db_client
from app.db.supabase import set_supabase_client
from app.main import app
from app.schemas.auth import CurrentUser, UserRole
from app.services.auth_service import AuthService


@pytest.fixture(autouse=True)
def reset_settings_and_client():
    get_settings.cache_clear()
    mock_client = MagicMock()
    mock_exec = MagicMock()
    mock_exec.data = []
    mock_exec.count = 0

    # Mock chaining query builder
    builder = MagicMock()
    builder.select.return_value = builder
    builder.order.return_value = builder
    builder.limit.return_value = builder
    builder.range.return_value = builder
    builder.eq.return_value = builder
    builder.execute.return_value = mock_exec
    mock_client.table.return_value = builder

    set_supabase_client(mock_client)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_jwt_secret():
    return "test-jwt-secret-key-for-testing-12345"


@pytest.fixture
def agent_token(test_jwt_secret):
    payload = {
        "sub": "agent-user-uuid-1234",
        "email": "agent@example.com",
        "aud": "authenticated",
        "role": "authenticated",
    }
    return jwt.encode(payload, test_jwt_secret, algorithm="HS256")


@pytest.fixture
def admin_token(test_jwt_secret):
    payload = {
        "sub": "admin-user-uuid-5678",
        "email": "admin@example.com",
        "aud": "authenticated",
        "role": "authenticated",
    }
    return jwt.encode(payload, test_jwt_secret, algorithm="HS256")


@pytest.fixture
def mock_auth_service():
    """Mock auth service returning CurrentUser according to user_id/sub."""
    mock_service = MagicMock(spec=AuthService)

    def verify_token_side_effect(token, client=None):
        try:
            payload = jwt.decode(
                token,
                "test-jwt-secret-key-for-testing-12345",
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            sub = payload.get("sub")
            if "admin" in sub:
                return CurrentUser(
                    id=sub,
                    email=payload.get("email"),
                    role=UserRole.ADMIN,
                    full_name="Admin User",
                )
            else:
                return CurrentUser(
                    id=sub,
                    email=payload.get("email"),
                    role=UserRole.AGENT,
                    full_name="Agent User",
                )
        except Exception:
            from app.core.exceptions import UnauthorizedError
            raise UnauthorizedError("Invalid or expired authentication token")

    mock_service.verify_token.side_effect = verify_token_side_effect
    return mock_service
