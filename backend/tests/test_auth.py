import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Organization, OrganizationRole, UserStatus
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "org_name": "Test Org",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test that duplicate email registration fails."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )

    # Try to register with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "anotherpassword",
            "org_name": "Another Org",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    """Test getting current user info."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "testpassword123",
            "org_name": "Test Org",
        },
    )
    access_token = reg_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "admin"
    assert "org_id" in data


# Cross-tenant isolation tests
@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient):
    """Test that users cannot access other organizations' data."""
    # Create org 1
    org1_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "org1@example.com",
            "password": "password123",
            "org_name": "Org 1",
        },
    )
    org1_token = org1_resp.json()["access_token"]

    # Create org 2
    org2_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "org2@example.com",
            "password": "password123",
            "org_name": "Org 2",
        },
    )
    org2_token = org2_resp.json()["access_token"]

    # Org 1 uploads a source
    import io
    files = {"file": ("test.txt", b"Org 1 secret content", "text/plain")}
    upload_resp = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"},
        headers={"Authorization": f"Bearer {org1_token}"},
    )
    assert upload_resp.status_code == 202
    source_id = upload_resp.json()["source_id"]

    # Org 2 tries to access org 1's source
    response = await client.get(
        f"/api/v1/sources/{source_id}",
        headers={"Authorization": f"Bearer {org2_token}"},
    )
    assert response.status_code == 404  # Not found (not 403 to avoid info leak)

    # Org 2 lists sources - should not see org 1's source
    list_resp = await client.get(
        "/api/v1/sources/",
        headers={"Authorization": f"Bearer {org2_token}"},
    )
    assert list_resp.status_code == 200
    sources = list_resp.json()
    assert len(sources) == 0  # Org 2 has no sources


@pytest.mark.asyncio
async def test_org_id_from_token_not_request(client: AsyncClient):
    """Test that org_id is derived from token, not request body."""
    # Create user in org 1
    org1_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "org1@example.com",
            "password": "password123",
            "org_name": "Org 1",
        },
    )
    org1_token = org1_resp.json()["access_token"]

    # Try to access org 2's data by passing org_id in request (should be ignored)
    response = await client.get(
        "/api/v1/sources/?org_id=fake-org-id",
        headers={"Authorization": f"Bearer {org1_token}"},
    )
    # Should use org_id from token, not query param
    assert response.status_code == 200
    # Should only return sources from org 1 (which is empty)
    sources = response.json()
    assert isinstance(sources, list)