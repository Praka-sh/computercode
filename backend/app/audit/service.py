import hashlib
import json
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import AuditEvent, User
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class AuditService:
    """Service for creating and managing tamper-evident audit events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        org_id: UUID,
        action: str,
        resource_type: str,
        outcome: str,
        actor_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Create an audit event with tamper-evident hash chain.

        The hash chain links each event to the previous event for the same organization,
        making tampering detectable.
        """
        # Get the previous event's hash for this org to build the chain
        prev_event = await self.db.execute(
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

        self.db.add(audit_event)
        await self.db.flush()

        # Log to structured logger as well
        logger.info(
            "audit_event",
            org_id=str(org_id),
            actor_id=str(actor_id) if actor_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            outcome=outcome,
            correlation_id=correlation_id,
            hash=event_hash,
        )

        return audit_event

    async def verify_chain(self, org_id: UUID) -> bool:
        """
        Verify the integrity of the audit event hash chain for an organization.
        Returns True if the chain is intact, False if tampering is detected.
        """
        events = await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.org_id == org_id)
            .order_by(AuditEvent.created_at.asc())
        )
        events = events.scalars().all()

        if not events:
            return True

        prev_hash = None
        for event in events:
            # Recompute hash for this event
            event_data = {
                "org_id": str(event.org_id),
                "actor_id": str(event.actor_id) if event.actor_id else None,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": str(event.resource_id) if event.resource_id else None,
                "outcome": event.outcome,
                "correlation_id": event.correlation_id,
                "metadata": event.metadata or {},
                "prev_hash": event.prev_hash,
                "created_at": event.created_at.isoformat(),
            }

            event_json = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
            computed_hash = hashlib.sha256(event_json.encode()).hexdigest()

            # Verify hash matches
            if computed_hash != event.hash:
                logger.error(
                    "audit_chain_verification_failed",
                    org_id=str(org_id),
                    event_id=str(event.id),
                    expected_hash=event.hash,
                    computed_hash=computed_hash,
                )
                return False

            # Verify chain link
            if event.prev_hash != prev_hash:
                logger.error(
                    "audit_chain_link_broken",
                    org_id=str(org_id),
                    event_id=str(event.id),
                    expected_prev_hash=prev_hash,
                    actual_prev_hash=event.prev_hash,
                )
                return False

            prev_hash = event.hash

        return True


async def get_audit_service(db: AsyncSession) -> AuditService:
    """Dependency injection for audit service."""
    return AuditService(db)