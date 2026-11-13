from celery import shared_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from uuid import UUID
import asyncio
import hashlib
import json
from datetime import datetime
import structlog

from app.core.config import settings
from app.db.models import SourceVersion, SourceStatus, Chunk
from app.db.session import Base

logger = structlog.get_logger()


async def _log_audit_event(session: AsyncSession, org_id: UUID, action: str, resource_type: str, outcome: str, actor_id: UUID = None, resource_id: UUID = None, correlation_id: str = None, metadata: dict = None):
    """Log an audit event with tamper-evident hash chain."""
    from app.db.models import AuditEvent

    # Get the previous event's hash for this org to build the chain
    prev_event = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.org_id == org_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(1)
    )
    prev_event = prev_event.scalar_one_or_none()
    prev_hash = prev_event.hash if prev_event else None

    # Prepare the data to hash
    event_data = {
        "org_id": str(org_id),
        "actor_id": str(actor_id) if actor_id else None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "outcome": outcome,
        "correlation_id": correlation_id,
        "metadata": metadata or {},
        "prev_hash": prev_hash,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Compute hash (SHA256 of JSON-serialized event data)
    event_json = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
    event_hash = hashlib.sha256(event_json.encode()).hexdigest()

    # Create audit event
    audit_event = AuditEvent(
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        correlation_id=correlation_id,
        metadata=metadata or {},
        prev_hash=prev_hash,
        hash=event_hash,
    )

    session.add(audit_event)
    await session.flush()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_source_task(self, source_version_id: str):
    """Async task to parse and chunk a source document."""
    return asyncio.run(_parse_source_async(source_version_id))


async def _parse_source_async(source_version_id: str):
    """Parse source document and create chunks with page/span references."""
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get source version
            result = await session.execute(
                select(SourceVersion).where(SourceVersion.id == UUID(source_version_id))
            )
            version = result.scalar_one_or_none()

            if not version:
                logger.error("source_version_not_found", version_id=source_version_id)
                await _log_audit_event(
                    session, version.source_id, "source.parse", "source_version",
                    "failure", resource_id=version.id,
                    metadata={"reason": "source_version_not_found"}
                )
                return {"status": "failed", "error": "Source version not found"}

            # Update source status to processing
            from app.db.models import Source
            source_result = await session.execute(
                select(Source).where(Source.id == version.source_id)
            )
            source = source_result.scalar_one()
            source.status = SourceStatus.SYNCING
            await session.commit()

            # Audit log: parse started
            await _log_audit_event(
                session, source.org_id, "source.parse", "source_version",
                "success", resource_id=version.id,
                metadata={"status": "started", "content_type": version.metadata.get("content_type")}
            )

            # Download file from S3
            from app.connectors.s3 import S3Connector
            s3 = S3Connector()
            object_key = version.blob_uri.replace(f"s3://{settings.MINIO_BUCKET}/", "")

            try:
                file_content = s3.download_file(object_key)
            except Exception as e:
                logger.error("s3_download_failed", version_id=source_version_id, error=str(e))
                source.status = SourceStatus.ERROR
                await session.commit()
                await _log_audit_event(
                    session, source.org_id, "source.parse", "source_version",
                    "failure", resource_id=version.id,
                    metadata={"reason": "s3_download_failed", "error": str(e)}
                )
                return {"status": "failed", "error": f"S3 download failed: {e}"}

            # Parse based on content type
            content_type = version.metadata.get("content_type", "application/octet-stream")
            chunks = await _parse_document(file_content, content_type, str(version.id))

            # Save chunks
            for chunk_data in chunks:
                chunk = Chunk(
                    source_id=version.source_id,
                    source_version_id=version.id,
                    page=chunk_data.get("page"),
                    section=chunk_data.get("section"),
                    start_offset=chunk_data["start_offset"],
                    end_offset=chunk_data["end_offset"],
                    text=chunk_data["text"],
                    embedding=None,  # Will be populated by embedding task
                )
                session.add(chunk)

            # Update source status
            source.status = SourceStatus.ACTIVE
            await session.commit()

            # Audit log: parse completed
            await _log_audit_event(
                session, source.org_id, "source.parse", "source_version",
                "success", resource_id=version.id,
                metadata={"status": "completed", "chunks_created": len(chunks)}
            )

            logger.info("source_parsed", version_id=source_version_id, chunks_created=len(chunks))

            # Queue embedding task
            from app.ingestion.tasks import embed_chunks_task
            embed_chunks_task.delay(str(version.id))

            return {"status": "completed", "chunks_created": len(chunks)}

        except Exception as e:
            logger.error("parse_failed", version_id=source_version_id, error=str(e))
            # Update source status to error
            try:
                source_result = await session.execute(
                    select(Source).where(Source.id == version.source_id)
                )
                source = source_result.scalar_one()
                source.status = SourceStatus.ERROR
                await session.commit()
                await _log_audit_event(
                    session, source.org_id, "source.parse", "source_version",
                    "failure", resource_id=version.id,
                    metadata={"reason": "parse_failed", "error": str(e)}
                )
            except Exception:
                pass
            raise self.retry(exc=e)


async def _parse_document(content: bytes, content_type: str, source_version_id: str) -> list:
    """Parse document based on type and return list of chunk dicts."""
    chunks = []

    if content_type == "application/pdf":
        chunks = _parse_pdf(content)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        chunks = _parse_docx(content)
    elif content_type in ("text/plain", "text/markdown"):
        chunks = _parse_text(content)
    else:
        # Fallback: treat as text
        chunks = _parse_text(content)

    # Add source_version_id to each chunk
    for chunk in chunks:
        chunk["source_version_id"] = source_version_id

    return chunks


def _parse_pdf(content: bytes) -> list:
    """Parse PDF and extract text with page numbers."""
    import io
    import pypdf

    chunks = []
    pdf_file = io.BytesIO(content)
    reader = pypdf.PdfReader(pdf_file)

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if not text.strip():
            continue

        # Simple chunking by paragraphs (can be improved)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        offset = 0
        for para in paragraphs:
            chunks.append({
                "page": page_num,
                "section": None,
                "start_offset": offset,
                "end_offset": offset + len(para),
                "text": para,
            })
            offset += len(para) + 2  # Account for paragraph breaks

    return chunks


def _parse_docx(content: bytes) -> list:
    """Parse DOCX and extract text with section references."""
    import io
    from docx import Document

    chunks = []
    doc_file = io.BytesIO(content)
    doc = Document(doc_file)

    offset = 0
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Use heading style as section if available
        section = para.style.name if para.style and para.style.name.startswith("Heading") else None

        chunks.append({
            "page": None,
            "section": section,
            "start_offset": offset,
            "end_offset": offset + len(text),
            "text": text,
        })
        offset += len(text) + 1

    return chunks


def _parse_text(content: bytes) -> list:
    """Parse plain text/markdown with simple chunking."""
    text = content.decode("utf-8", errors="replace")

    # Simple chunking: split by double newline, max ~500 chars per chunk
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    offset = 0
    for para in paragraphs:
        # Further split long paragraphs
        if len(para) > 1000:
            sub_chunks = [para[i:i+1000] for i in range(0, len(para), 1000)]
            for sub in sub_chunks:
                chunks.append({
                    "page": None,
                    "section": None,
                    "start_offset": offset,
                    "end_offset": offset + len(sub),
                    "text": sub,
                })
                offset += len(sub)
        else:
            chunks.append({
                "page": None,
                "section": None,
                "start_offset": offset,
                "end_offset": offset + len(para),
                "text": para,
            })
            offset += len(para) + 2

    return chunks


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_chunks_task(self, source_version_id: str):
    """Async task to generate embeddings for chunks."""
    return asyncio.run(_embed_chunks_async(source_version_id))


async def _embed_chunks_async(source_version_id: str):
    """Generate embeddings for all chunks of a source version."""
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get source version to get org_id
            result = await session.execute(
                select(SourceVersion).where(SourceVersion.id == UUID(source_version_id))
            )
            version = result.scalar_one_or_none()

            if not version:
                logger.error("source_version_not_found", version_id=source_version_id)
                return {"status": "failed", "error": "Source version not found"}

            # Get chunks without embeddings
            result = await session.execute(
                select(Chunk)
                .where(Chunk.source_version_id == UUID(source_version_id))
                .where(Chunk.embedding.is_(None))
            )
            chunks = result.scalars().all()

            if not chunks:
                logger.info("no_chunks_to_embed", version_id=source_version_id)
                await _log_audit_event(
                    session, version.source_id, "source.embed", "source_version",
                    "success", resource_id=version.id,
                    metadata={"status": "no_chunks", "embedded": 0}
                )
                return {"status": "completed", "embedded": 0}

            # Audit log: embedding started
            await _log_audit_event(
                session, version.source_id, "source.embed", "source_version",
                "success", resource_id=version.id,
                metadata={"status": "started", "chunks_to_embed": len(chunks)}
            )

            # Generate embeddings (placeholder - will use actual embedding provider)
            from app.ingestion.embeddings import generate_embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = await generate_embeddings(texts)

            # Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding

            await session.commit()

            # Audit log: embedding completed
            await _log_audit_event(
                session, version.source_id, "source.embed", "source_version",
                "success", resource_id=version.id,
                metadata={"status": "completed", "embedded": len(chunks)}
            )

            logger.info("chunks_embedded", version_id=source_version_id, count=len(chunks))
            return {"status": "completed", "embedded": len(chunks)}

        except Exception as e:
            logger.error("embed_failed", version_id=source_version_id, error=str(e))
            try:
                result = await session.execute(
                    select(SourceVersion).where(SourceVersion.id == UUID(source_version_id))
                )
                version = result.scalar_one_or_none()
                if version:
                    await _log_audit_event(
                        session, version.source_id, "source.embed", "source_version",
                        "failure", resource_id=version.id,
                        metadata={"reason": "embed_failed", "error": str(e)}
                    )
            except Exception:
                pass
            raise self.retry(exc=e)