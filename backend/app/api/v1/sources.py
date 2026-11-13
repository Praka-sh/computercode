from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from typing import List, Optional
import os
from datetime import datetime

from app.db.session import get_db
from app.core.auth import get_current_user, get_current_org, TokenData
from app.core.config import settings
from app.connectors.s3 import S3Connector, compute_checksum, generate_object_key
from app.db.models import Source, SourceVersion, SourceKind, SourceStatus
from app.audit.service import get_audit_service, AuditService

router = APIRouter(prefix="/sources", tags=["sources"])

# Allowed file types and max sizes
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/markdown': '.md',
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    kind: str = "file",
    external_key: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    req: Request = None,
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Upload a source document.
    Returns source ID and job ID for async processing.
    """
    correlation_id = getattr(req.state, "correlation_id", None) if req else None

    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        await audit_service.log_event(
            org_id=org_id,
            actor_id=current_user.user_id,
            action="source.upload",
            resource_type="source",
            resource_id=None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"filename": file.filename, "content_type": file.content_type, "reason": "unsupported_file_type"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {list(ALLOWED_MIME_TYPES.keys())}",
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        await audit_service.log_event(
            org_id=org_id,
            actor_id=current_user.user_id,
            action="source.upload",
            resource_type="source",
            resource_id=None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"filename": file.filename, "file_size": len(content), "reason": "file_too_large"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE} bytes",
        )

    if len(content) == 0:
        await audit_service.log_event(
            org_id=org_id,
            actor_id=current_user.user_id,
            action="source.upload",
            resource_type="source",
            resource_id=None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"filename": file.filename, "reason": "empty_file"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file not allowed",
        )

    # Compute checksum for deduplication
    import io
    file_obj = io.BytesIO(content)
    checksum = compute_checksum(file_obj)

    # Check for existing source version with same checksum
    existing_version = await db.execute(
        select(SourceVersion).where(SourceVersion.checksum == checksum)
    )
    existing_version = existing_version.scalar_one_or_none()

    if existing_version:
        # Audit log for deduplicated upload
        await audit_service.log_event(
            org_id=org_id,
            actor_id=current_user.user_id,
            action="source.upload",
            resource_type="source",
            resource_id=existing_version.source_id,
            outcome="success",
            correlation_id=correlation_id,
            metadata={
                "filename": file.filename,
                "checksum": checksum,
                "deduplicated": True,
                "existing_version_id": str(existing_version.id),
            },
        )
        # Return existing source info - deduplicated
        return {
            "source_id": str(existing_version.source_id),
            "version_id": str(existing_version.id),
            "deduplicated": True,
            "message": "File already exists with same content",
        }

    # Create source record
    source = Source(
        id=uuid4(),
        org_id=org_id,
        kind=SourceKind(kind),
        external_key=external_key,
        owner_id=current_user.user_id,
        status=SourceStatus.ACTIVE,
    )
    db.add(source)
    await db.flush()

    # Generate S3 key and upload
    s3 = S3Connector()
    object_key = generate_object_key(org_id, str(source.id), file.filename or "unknown")

    # Upload to S3
    file_obj = io.BytesIO(content)
    blob_uri = s3.upload_file(file_obj, object_key, file.content_type, {
        "original_filename": file.filename or "unknown",
        "content_type": file.content_type,
        "checksum": checksum,
        "uploaded_by": current_user.user_id,
    })

    # Create source version
    source_version = SourceVersion(
        id=uuid4(),
        source_id=source.id,
        checksum=checksum,
        captured_at=datetime.utcnow(),
        blob_uri=blob_uri,
        metadata={
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content),
        },
    )
    db.add(source_version)
    await db.flush()

    # Update source with current version
    source.current_version_id = source_version.id

    await db.commit()

    # Audit log for successful upload
    await audit_service.log_event(
        org_id=org_id,
        actor_id=current_user.user_id,
        action="source.upload",
        resource_type="source",
        resource_id=source.id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={
            "filename": file.filename,
            "checksum": checksum,
            "version_id": str(source_version.id),
            "file_size": len(content),
            "content_type": file.content_type,
        },
    )

    # Queue async parsing job
    from app.ingestion.tasks import parse_source_task
    job = parse_source_task.delay(str(source_version.id))

    return {
        "source_id": str(source.id),
        "version_id": str(source_version.id),
        "job_id": job.id,
        "deduplicated": False,
        "status": "queued",
    }


@router.get("/")
async def list_sources(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    req: Request = None,
    audit_service: AuditService = Depends(get_audit_service),
):
    """List sources for the current organization."""
    query = select(Source).where(Source.org_id == org_id)

    if status_filter:
        query = query.where(Source.status == SourceStatus(status_filter))

    query = query.offset(skip).limit(limit).order_by(Source.created_at.desc())
    result = await db.execute(query)
    sources = result.scalars().all()

    correlation_id = getattr(req.state, "correlation_id", None) if req else None

    await audit_service.log_event(
        org_id=org_id,
        action="source.list",
        resource_type="source",
        resource_id=None,
        outcome="success",
        correlation_id=correlation_id,
        metadata={"count": len(sources), "status_filter": status_filter},
    )

    return [
        {
            "id": str(s.id),
            "kind": s.kind.value,
            "external_key": s.external_key,
            "status": s.status.value,
            "current_version_id": str(s.current_version_id) if s.current_version_id else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sources
    ]


@router.get("/{source_id}")
async def get_source(
    source_id: str,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    req: Request = None,
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get source details."""
    correlation_id = getattr(req.state, "correlation_id", None) if req else None

    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.org_id == org_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        await audit_service.log_event(
            org_id=org_id,
            action="source.get",
            resource_type="source",
            resource_id=source_id,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"reason": "not_found"},
        )
        raise HTTPException(status_code=404, detail="Source not found")

    await audit_service.log_event(
        org_id=org_id,
        action="source.get",
        resource_type="source",
        resource_id=source.id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={},
    )

    return {
        "id": str(source.id),
        "kind": source.kind.value,
        "external_key": source.external_key,
        "owner_id": str(source.owner_id),
        "status": source.status.value,
        "acl_policy": source.acl_policy,
        "current_version_id": str(source.current_version_id) if source.current_version_id else None,
        "created_at": source.created_at.isoformat(),
        "updated_at": source.updated_at.isoformat(),
    }


@router.get("/{source_id}/versions/{version_id}")
async def get_source_version(
    source_id: str,
    version_id: str,
    org_id: str = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
    req: Request = None,
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get source version details with provenance."""
    correlation_id = getattr(req.state, "correlation_id", None) if req else None

    result = await db.execute(
        select(SourceVersion)
        .join(Source)
        .where(SourceVersion.id == version_id, Source.id == source_id, Source.org_id == org_id)
    )
    version = result.scalar_one_or_none()

    if not version:
        await audit_service.log_event(
            org_id=org_id,
            action="source_version.get",
            resource_type="source_version",
            resource_id=version_id,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"source_id": source_id, "reason": "not_found"},
        )
        raise HTTPException(status_code=404, detail="Source version not found")

    # Generate presigned URL for authorized download
    s3 = S3Connector()
    object_key = version.blob_uri.replace(f"s3://{settings.MINIO_BUCKET}/", "")
    download_url = s3.generate_presigned_url(object_key)

    await audit_service.log_event(
        org_id=org_id,
        action="source_version.get",
        resource_type="source_version",
        resource_id=version.id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={"source_id": source_id},
    )

    return {
        "id": str(version.id),
        "source_id": str(version.source_id),
        "checksum": version.checksum,
        "captured_at": version.captured_at.isoformat(),
        "effective_at": version.effective_at.isoformat() if version.effective_at else None,
        "blob_uri": version.blob_uri,
        "download_url": download_url,
        "metadata": version.metadata,
        "parser_version": version.parser_version,
        "created_at": version.created_at.isoformat(),
    }