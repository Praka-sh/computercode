import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Source, SourceVersion, User, Organization, SourceKind, SourceStatus


@pytest.mark.asyncio
async def test_upload_source_invalid_type(client: AsyncClient):
    """Test that unsupported file types are rejected."""
    # Create a fake file with unsupported type
    files = {"file": ("test.exe", b"fake content", "application/octet-stream")}
    response = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_source_empty_file(client: AsyncClient):
    """Test that empty files are rejected."""
    files = {"file": ("test.txt", b"", "text/plain")}
    response = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"}
    )
    assert response.status_code == 400
    assert "Empty file not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_source_oversized(client: AsyncClient):
    """Test that oversized files are rejected."""
    # Create a file larger than MAX_FILE_SIZE (50MB)
    large_content = b"x" * (51 * 1024 * 1024)
    files = {"file": ("large.txt", large_content, "text/plain")}
    response = await client.post(
        "/api/v1/sources/upload",
        files=files,
        data={"kind": "file"}
    )
    assert response.status_code == 400
    assert "exceeds maximum" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_sources(client: AsyncClient):
    """Test listing sources."""
    response = await client.get("/api/v1/sources/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_source_not_found(client: AsyncClient):
    """Test getting non-existent source returns 404."""
    fake_id = str(uuid4())
    response = await client.get(f"/api/v1/sources/{fake_id}")
    assert response.status_code == 404