from unittest.mock import MagicMock
from app.core.dependencies import get_auth_service
from app.main import app
from app.schemas.auth import CurrentUser, UserRole


def test_unauthenticated_request_returns_401(client):
    """Protected endpoints should return 401 when no Authorization header is provided."""
    response = client.get("/api/v1/customers")
    assert response.status_code == 401
    assert "Missing or invalid authentication token" in response.json()["detail"]


def test_invalid_token_returns_401(client, mock_auth_service):
    """Protected endpoints should return 401 when token is invalid or malformed."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    response = client.get("/api/v1/customers", headers={"Authorization": "Bearer invalid-garbage-token"})
    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_agent_can_access_protected_staff_route(client, agent_token, mock_auth_service):
    """Agent role can access general staff routes (e.g. /auth/me, /customers)."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {agent_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "agent-user-uuid-1234"
    assert data["role"] == "agent"
    assert data["email"] == "agent@example.com"


def test_agent_cannot_access_admin_route(client, agent_token, mock_auth_service):
    """Agent role must receive 403 Forbidden when accessing admin-restricted routes."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    # POST /templates requires admin
    new_template = {
        "name": "Order Notice",
        "trigger_event": "order.created",
        "subject": "Thank you",
        "body_html": "<p>Thanks!</p>",
        "is_active": True,
    }
    response = client.post(
        "/api/v1/templates",
        json=new_template,
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]

    # GET /sync/status requires admin
    sync_resp = client.get(
        "/api/v1/sync/status",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert sync_resp.status_code == 403
    assert "Admin privileges required" in sync_resp.json()["detail"]


def test_admin_can_access_admin_route(client, admin_token, mock_auth_service):
    """Admin role can access admin-restricted routes."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    # Check GET /api/v1/auth/me for admin
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "admin"

    # GET /sync/status with admin token (mocked service returns successfully)
    sync_resp = client.get(
        "/api/v1/sync/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert sync_resp.status_code == 200
    assert "recent_logs" in sync_resp.json()

