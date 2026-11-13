from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.audit.service import AuditService, get_audit_service
from app.core.auth import get_current_user, require_role
from app.db.models import User, OrganizationRole
from app.core.errors import NotFoundError

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
async def list_audit_events(
    org_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    outcome: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    List audit events with filtering.
    Only auditors and admins can access audit logs.
    """
    # Check if user has auditor or admin role
    if current_user.role not in [OrganizationRole.AUDITOR, OrganizationRole.ADMIN]:
        from app.core.errors import AuthorizationError
        raise AuthorizationError("Only auditors and admins can access audit logs")

    # Use user's org_id if not specified (admins can only see their org)
    target_org_id = org_id or current_user.org_id

    # Build query
    from sqlalchemy import select, and_
    from app.db.models import AuditEvent

    query = select(AuditEvent).where(AuditEvent.org_id == target_org_id)

    if actor_id:
        query = query.where(AuditEvent.actor_id == actor_id)
    if action:
        query = query.where(AuditEvent.action == action)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)
    if outcome:
        query = query.where(AuditEvent.outcome == outcome)
    if correlation_id:
        query = query.where(AuditEvent.correlation_id == correlation_id)

    query = query.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "events": [
            {
                "id": str(e.id),
                "org_id": str(e.org_id),
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": str(e.resource_id) if e.resource_id else None,
                "outcome": e.outcome,
                "correlation_id": e.correlation_id,
                "metadata": e.metadata,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
        "limit": limit,
        "offset": offset,
    }


@router.get("/events/{event_id}")
async def get_audit_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get a specific audit event by ID."""
    if current_user.role not in [OrganizationRole.AUDITOR, OrganizationRole.ADMIN]:
        from app.core.errors import AuthorizationError
        raise AuthorizationError("Only auditors and admins can access audit logs")

    from sqlalchemy import select
    from app.db.models import AuditEvent

    result = await db.execute(
        select(AuditEvent).where(
            AuditEvent.id == event_id,
            AuditEvent.org_id == current_user.org_id
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise NotFoundError("Audit event not found", "audit_event")

    return {
        "id": str(event.id),
        "org_id": str(event.org_id),
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "action": event.action,
        "resource_type": event.resource_type,
        "resource_id": str(event.resource_id) if event.resource_id else None,
        "outcome": event.outcome,
        "correlation_id": event.correlation_id,
        "metadata": event.metadata,
        "prev_hash": event.prev_hash,
        "hash": event.hash,
        "created_at": event.created_at.isoformat(),
    }


@router.post("/verify-chain")
async def verify_audit_chain(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Verify the integrity of the audit event hash chain."""
    if current_user.role not in [OrganizationRole.AUDITOR, OrganizationRole.ADMIN]:
        from app.core.errors import AuthorizationError
        raise AuthorizationError("Only auditors and admins can verify audit chain")

    is_valid = await audit_service.verify_chain(current_user.org_id)

    return {
        "org_id": str(current_user.org_id),
        "chain_valid": is_valid,
    }