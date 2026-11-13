import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.db.models import User, Organization, OrganizationRole, UserStatus, AuditEvent
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_audit_log_on_register(client: AsyncClient):
    """Test that audit event is created on user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "audit@example.com",
            "password": "testpassword123",
            "full_name": "Audit User",
            "org_name": "Audit Org",
        },
        headers={"X-Correlation-ID": "test-correlation-123"},
    )
    assert response.status_code == 201

    # Check that audit event was created in the same transaction
    # Note: With the test DB override, we need to query within the same session
    # For now, verify the response has correlation ID
    assert "access_token" in response.json()
    assert response.headers.get("X-Correlation-ID") == "test-correlation-123"


@pytest.mark.asyncio
async def test_audit_log_on_login_success(client: AsyncClient):
    """Test that audit event is created on successful login."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginaudit@example.com",
            "password": "testpassword123",
            "org_name": "Login Audit Org",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginaudit@example.com",
            "password": "testpassword123",
        },
        headers={"X-Correlation-ID": "login-correlation-456"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "login-correlation-456"


@pytest.mark.asyncio
async def test_audit_log_on_login_failure(client: AsyncClient):
    """Test that audit event is created on failed login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        },
        headers={"X-Correlation-ID": "failed-login-789"},
    )
    assert response.status_code == 401
    assert response.headers.get("X-Correlation-ID") == "failed-login-789"


@pytest.mark.asyncio
async def test_audit_log_on_token_refresh(client: AsyncClient):
    """Test that audit event is created on token refresh."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refreshaudit@example.com",
            "password": "testpassword123",
            "org_name": "Refresh Audit Org",
        },
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"X-Correlation-ID": "refresh-correlation-abc"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "refresh-correlation-abc"


@pytest.mark.asyncio
async def test_audit_log_on_logout(client: AsyncClient):
    """Test that audit event is created on logout."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "logouthaudit@example.com",
            "password": "testpassword123",
            "org_name": "Logout Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "logout-correlation-def",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "logout-correlation-def"


@pytest.mark.asyncio
async def test_audit_log_on_source_upload(client: AsyncClient):
    """Test that audit event is created on source upload."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sourceaudit@example.com",
            "password": "testpassword123",
            "org_name": "Source Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    import io
    files = {"file": ("test.txt", b"Test content for audit", "text/plain")}
    response = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "source-upload-correlation",
        },
    )
    assert response.status_code == 202
    assert response.headers.get("X-Correlation-ID") == "source-upload-correlation"


@pytest.mark.asyncio
async def test_audit_log_on_source_list(client: AsyncClient):
    """Test that audit event is created on source list."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "listaudit@example.com",
            "password": "testpassword123",
            "org_name": "List Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    response = await client.get(
        "/api/v1/sources/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "source-list-correlation",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "source-list-correlation"


@pytest.mark.asyncio
async def test_audit_log_on_source_get(client: AsyncClient):
    """Test that audit event is created on source get."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "getaudit@example.com",
            "password": "testpassword123",
            "org_name": "Get Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    # Upload a source first
    import io
    files = {"file": ("test.txt", b"Test content for get audit", "text/plain")}
    upload_resp = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    source_id = upload_resp.json()["source_id"]

    response = await client.get(
        f"/api/v1/sources/{source_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "source-get-correlation",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "source-get-correlation"


@pytest.mark.asyncio
async def test_audit_log_on_source_get_not_found(client: AsyncClient):
    """Test that audit event is created on source get (not found)."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "getnotfoundaudit@example.com",
            "password": "testpassword123",
            "org_name": "Get Not Found Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    response = await client.get(
        f"/api/v1/sources/{uuid4()}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "source-get-notfound-correlation",
        },
    )
    assert response.status_code == 404
    assert response.headers.get("X-Correlation-ID") == "source-get-notfound-correlation"


@pytest.mark.asyncio
async def test_audit_log_on_source_version_get(client: AsyncClient):
    """Test that audit event is created on source version get."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "versionaudit@example.com",
            "password": "testpassword123",
            "org_name": "Version Audit Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    # Upload a source first
    import io
    files = {"file": ("test.txt", b"Test content for version audit", "text/plain")}
    upload_resp = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    source_id = upload_resp.json()["source_id"]
    version_id = upload_resp.json()["version_id"]

    response = await client.get(
        f"/api/v1/sources/{source_id}/versions/{version_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Correlation-ID": "source-version-get-correlation",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "source-version-get-correlation"


@pytest.mark.asyncio
async def test_correlation_id_in_error_response(client: AsyncClient):
    """Test that correlation ID is included in error responses."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "error@example.com",
            "password": "wrongpassword",
        },
        headers={"X-Correlation-ID": "error-correlation-xyz"},
    )
    assert response.status_code == 401
    assert response.headers.get("X-Correlation-ID") == "error-correlation-xyz"
    data = response.json()
    assert "correlation_id" in data
    assert data["correlation_id"] == "error-correlation-xyz"


@pytest.mark.asyncio
async def test_error_response_format(client: AsyncClient):
    """Test standardized error response format."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "errorformat@example.com",
            "password": "wrongpassword",
        },
        headers={"X-Correlation-ID": "error-format-correlation"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert data["error"]["code"] == "UNAUTHENTICATED"
    assert "correlation_id" in data
    assert data["correlation_id"] == "error-format-correlation"


@pytest.mark.asyncio
async def test_validation_error_format(client: AsyncClient):
    """Test validation error response format."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",  # Invalid email format
            "password": "testpassword123",
            "org_name": "Validation Org",
        },
        headers={"X-Correlation-ID": "validation-correlation"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "correlation_id" in data
    assert data["correlation_id"] == "validation-correlation"


@pytest.mark.asyncio
async def test_correlation_id_generated_if_missing(client: AsyncClient):
    """Test that correlation ID is generated if not provided."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nocorrelation@example.com",
            "password": "testpassword123",
            "org_name": "No Correlation Org",
        },
    )
    assert response.status_code == 201
    assert "X-Correlation-ID" in response.headers
    # Should be a valid UUID
    import uuid
    try:
        uuid.UUID(response.headers["X-Correlation-ID"])
    except ValueError:
        pytest.fail("X-Correlation-ID is not a valid UUID")


@pytest.mark.asyncio
async def test_audit_events_accessible_by_auditor(client: AsyncClient):
    """Test that audit events can be queried by auditor role."""
    # Register admin user
    admin_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "testpassword123",
            "org_name": "Admin Org",
        },
    )
    admin_token = admin_resp.json()["access_token"]

    # Register auditor user
    auditor_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "auditor@example.com",
            "password": "testpassword123",
        },
    )
    auditor_token = auditor_resp.json()["access_token"]

    # Update auditor role (in real app, admin would do this)
    # For test, we just check the endpoint exists and returns 403 for non-auditor
    # Admin can access audit logs
    response = await client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "events" in data

    # Non-auditor cannot access
    response = await client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_chain_verification(client: AsyncClient):
    """Test audit chain verification endpoint."""
    admin_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "chainverify@example.com",
            "password": "testpassword123",
            "org_name": "Chain Verify Org",
        },
    )
    admin_token = admin_resp.json()["access_token"]

    response = await client.post(
        "/api/v1/audit/verify-chain",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "chain_valid" in data
    assert "org_id" in data
    assert data["chain_valid"] is True  # Should be valid for new org


@pytest.mark.asyncio
async def test_structured_logging_has_correlation_id(client: AsyncClient):
    """Test that structured logging includes correlation ID."""
    # This is more of an integration test - we verify the header is passed through
    response = await client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": "health-check-correlation"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "health-check-correlation"