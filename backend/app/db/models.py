from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Integer, Boolean, Index, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_mixin, declared_attr
from pgvector.sqlalchemy import Vector

from app.db.session import Base

import enum


class OrganizationRole(str, enum.Enum):
    ADMIN = "admin"
    KNOWLEDGE_OWNER = "knowledge_owner"
    SUPPORT_AGENT = "support_agent"
    APPROVER = "approver"
    AUDITOR = "auditor"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class SourceKind(str, enum.Enum):
    FILE = "file"
    ERPNext = "erpnext"
    GMAIL = "gmail"
    SLACK = "slack"
    GOOGLE_DRIVE = "google_drive"


class SourceStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SYNCING = "syncing"
    ERROR = "error"


class KnowledgeType(str, enum.Enum):
    FACT = "fact"
    POLICY = "policy"
    PROCESS = "process"
    DECISION = "decision"
    OWNER = "owner"
    EXCEPTION = "exception"


class KnowledgeStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    DISPUTED = "disputed"


class ConflictSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictDisposition(str, enum.Enum):
    PENDING = "pending"
    RESOLVED_KEEP_A = "resolved_keep_a"
    RESOLVED_KEEP_B = "resolved_keep_b"
    RESOLVED_MERGE = "resolved_merge"
    RESOLVED_SUPERSEDE = "resolved_supersede"


class SkillStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    NEEDS_REVIEW = "needs_review"
    DEPRECATED = "deprecated"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    ESCALATED = "escalated"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    policy_settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="organization")
    sources = relationship("Source", back_populates="organization")
    knowledge_units = relationship("KnowledgeUnit", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(OrganizationRole), nullable=False, default=OrganizationRole.SUPPORT_AGENT)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    provider_id = Column(String(255))  # For OAuth
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="users")

    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_org_user_email"),
    )


class Connector(Base):
    __tablename__ = "connectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(String(50), nullable=False)
    encrypted_credential_ref = Column(String(500), nullable=False)
    sandbox = Column(Boolean, default=True, nullable=False)
    scopes = Column(JSONB, default={})
    sync_cursor = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    connector_id = Column(UUID(as_uuid=True), ForeignKey("connectors.id"), nullable=True)
    kind = Column(Enum(SourceKind), nullable=False)
    external_key = Column(String(500))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    acl_policy = Column(JSONB, default={})
    status = Column(Enum(SourceStatus), nullable=False, default=SourceStatus.ACTIVE)
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="sources")
    versions = relationship("SourceVersion", back_populates="source")
    chunks = relationship("Chunk", back_populates="source")


class SourceVersion(Base):
    __tablename__ = "source_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    checksum = Column(String(64), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    effective_at = Column(DateTime, nullable=True)
    blob_uri = Column(String(1000), nullable=False)
    metadata = Column(JSONB, default={})
    parser_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="versions")
    chunks = relationship("Chunk", back_populates="source_version")
    evidence_links = relationship("EvidenceLink", back_populates="source_version")

    __table_args__ = (
        UniqueConstraint("source_id", "checksum", name="uq_source_version_checksum"),
        Index("ix_source_version_source_effective", "source_id", "effective_at"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    source_version_id = Column(UUID(as_uuid=True), ForeignKey("source_versions.id"), nullable=False)
    page = Column(Integer)
    section = Column(String(500))
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=True)  # pgvector - dimension matches EMBEDDING_DIMENSIONS
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", back_populates="chunks")
    source_version = relationship("SourceVersion", back_populates="chunks")
    evidence_links = relationship("EvidenceLink", back_populates="chunk")

    __table_args__ = (
        Index("ix_chunk_source_version", "source_version_id"),
        Index("ix_chunk_embedding", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}),
    )


class KnowledgeUnit(Base):
    __tablename__ = "knowledge_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(Enum(KnowledgeType), nullable=False)
    label = Column(String(500), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(Enum(KnowledgeStatus), nullable=False, default=KnowledgeStatus.PROPOSED)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="knowledge_units")
    versions = relationship("KnowledgeVersion", back_populates="unit")
    owner = relationship("User")


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_units.id"), nullable=False)
    claim = Column(JSONB, nullable=False)  # {kind, subject, predicate, object, qualifiers, scope, effective_from, effective_to}
    source_evidence = Column(JSONB, nullable=False)  # list of evidence references
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    status = Column(Enum(KnowledgeStatus), nullable=False, default=KnowledgeStatus.PROPOSED)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    extractor_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    unit = relationship("KnowledgeUnit", back_populates="versions")
    reviewer = relationship("User")
    evidence_links = relationship("EvidenceLink", back_populates="knowledge_version")

    __table_args__ = (
        Index("ix_knowledge_version_unit_status", "unit_id", "status"),
        Index("ix_knowledge_version_effective", "effective_from", "effective_to"),
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    knowledge_version_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_versions.id"), nullable=False)
    source_version_id = Column(UUID(as_uuid=True), ForeignKey("source_versions.id"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=True)
    link_type = Column(String(50), nullable=False)  # direct, inferred, supporting
    extractor_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    knowledge_version = relationship("KnowledgeVersion", back_populates="evidence_links")
    source_version = relationship("SourceVersion", back_populates="evidence_links")
    chunk = relationship("Chunk", back_populates="evidence_links")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(String(100), nullable=False)
    canonical_name = Column(String(500), nullable=False)
    external_references = Column(JSONB, default={})
    acl_policy = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "type", "canonical_name", name="uq_org_entity"),
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    src_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True)
    src_unit_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_units.id"), nullable=True)
    predicate = Column(String(200), nullable=False)
    dst_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=True)
    dst_unit_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_units.id"), nullable=True)
    evidence_link_id = Column(UUID(as_uuid=True), ForeignKey("evidence_links.id"), nullable=True)
    status = Column(String(50), nullable=False, default="proposed")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Conflict(Base):
    __tablename__ = "conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    knowledge_version_a_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_versions.id"), nullable=False)
    knowledge_version_b_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_versions.id"), nullable=False)
    severity = Column(Enum(ConflictSeverity), nullable=False)
    rationale = Column(Text, nullable=False)
    disposition = Column(Enum(ConflictDisposition), nullable=False, default=ConflictDisposition.PENDING)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviewer = relationship("User")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(SkillStatus), nullable=False, default=SkillStatus.DRAFT)
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    versions = relationship("SkillVersion", back_populates="skill")


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    version = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)  # SKILL.md content
    manifest = Column(JSONB, nullable=False)  # manifest.json content
    tests = Column(JSONB, nullable=False)  # tests.json content
    digest = Column(String(64), nullable=False)  # content hash
    dependency_snapshot = Column(JSONB, default={})  # {knowledge_version_id: digest}
    status = Column(Enum(SkillStatus), nullable=False, default=SkillStatus.DRAFT)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    skill = relationship("Skill", back_populates="versions")
    reviewer = relationship("User")

    __table_args__ = (
        UniqueConstraint("skill_id", "version", name="uq_skill_version"),
    )


class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    skill_version_id = Column(UUID(as_uuid=True), ForeignKey("skill_versions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ticket_id = Column(String(255), nullable=False)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.PENDING)
    trace = Column(JSONB, default={})
    idempotency_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    skill_version = relationship("SkillVersion")
    user = relationship("User")
    events = relationship("RunEvent", back_populates="run")
    approvals = relationship("Approval", back_populates="run")


class RunEvent(Base):
    __tablename__ = "run_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    step = Column(String(100), nullable=False)
    input = Column(JSONB, default={})
    output = Column(JSONB, default={})
    status = Column(String(50), nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="events")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    action_name = Column(String(100), nullable=False)
    action_arguments = Column(JSONB, nullable=False)
    required_role = Column(String(50), nullable=False)
    allowed_scope = Column(JSONB, default={})
    status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    decision = Column(JSONB, nullable=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ticket_revision = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("Run", back_populates="approvals")
    actor = relationship("User")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    outcome = Column(String(50), nullable=False)  # success, failure, denied
    correlation_id = Column(String(255), nullable=True)
    metadata = Column(JSONB, default={})
    prev_hash = Column(String(64), nullable=True)  # for tamper-evident chain
    hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    actor = relationship("User")

    __table_args__ = (
        Index("ix_audit_event_org_created", "org_id", "created_at"),
        Index("ix_audit_event_correlation", "correlation_id"),
    )