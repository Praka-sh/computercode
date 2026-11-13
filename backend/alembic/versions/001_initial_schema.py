"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create enums
    op.execute("CREATE TYPE organization_role AS ENUM ('admin', 'knowledge_owner', 'support_agent', 'approver', 'auditor')")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'revoked')")
    op.execute("CREATE TYPE source_kind AS ENUM ('file', 'erpnext', 'gmail', 'slack', 'google_drive')")
    op.execute("CREATE TYPE source_status AS ENUM ('active', 'archived', 'syncing', 'error')")
    op.execute("CREATE TYPE knowledge_type AS ENUM ('fact', 'policy', 'process', 'decision', 'owner', 'exception')")
    op.execute("CREATE TYPE knowledge_status AS ENUM ('proposed', 'approved', 'rejected', 'superseded', 'disputed')")
    op.execute("CREATE TYPE conflict_severity AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE conflict_disposition AS ENUM ('pending', 'resolved_keep_a', 'resolved_keep_b', 'resolved_merge', 'resolved_supersede')")
    op.execute("CREATE TYPE skill_status AS ENUM ('draft', 'review', 'published', 'needs_review', 'deprecated')")
    op.execute("CREATE TYPE run_status AS ENUM ('pending', 'running', 'waiting_approval', 'completed', 'failed', 'aborted', 'escalated')")
    op.execute("CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'expired')")

    # organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('policy_settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'knowledge_owner', 'support_agent', 'approver', 'auditor', name='organization_role'), nullable=False, server_default='support_agent'),
        sa.Column('status', sa.Enum('active', 'revoked', name='user_status'), nullable=False, server_default='active'),
        sa.Column('provider_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'email', name='uq_org_user_email')
    )

    # connectors
    op.create_table(
        'connectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('encrypted_credential_ref', sa.String(500), nullable=False),
        sa.Column('sandbox', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scopes', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('sync_cursor', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # sources
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connector_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('kind', sa.Enum('file', 'erpnext', 'gmail', 'slack', 'google_drive', name='source_kind'), nullable=False),
        sa.Column('external_key', sa.String(500), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('acl_policy', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.Enum('active', 'archived', 'syncing', 'error', name='source_status'), nullable=False, server_default='active'),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connector_id'], ['connectors.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # source_versions
    op.create_table(
        'source_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('effective_at', sa.DateTime(), nullable=True),
        sa.Column('blob_uri', sa.String(1000), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('parser_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id', 'checksum', name='uq_source_version_checksum')
    )
    op.create_index('ix_source_version_source_effective', 'source_versions', ['source_id', 'effective_at'], unique=False)

    # chunks (with pgvector)
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(500), nullable=True),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),  # pgvector will be handled via raw SQL
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.ForeignKeyConstraint(['source_version_id'], ['source_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunk_source_version', 'chunks', ['source_version_id'], unique=False)

    # knowledge_units
    op.create_table(
        'knowledge_units',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('fact', 'policy', 'process', 'decision', 'owner', 'exception', name='knowledge_type'), nullable=False),
        sa.Column('label', sa.String(500), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('proposed', 'approved', 'rejected', 'superseded', 'disputed', name='knowledge_status'), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # knowledge_versions
    op.create_table(
        'knowledge_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('claim', postgresql.JSONB(), nullable=False),
        sa.Column('source_evidence', postgresql.JSONB(), nullable=False),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('proposed', 'approved', 'rejected', 'superseded', 'disputed', name='knowledge_status'), nullable=False, server_default='proposed'),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('extractor_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['unit_id'], ['knowledge_units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_version_unit_status', 'knowledge_versions', ['unit_id', 'status'], unique=False)
    op.create_index('ix_knowledge_version_effective', 'knowledge_versions', ['effective_from', 'effective_to'], unique=False)

    # evidence_links
    op.create_table(
        'evidence_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('link_type', sa.String(50), nullable=False),
        sa.Column('extractor_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ),
        sa.ForeignKeyConstraint(['knowledge_version_id'], ['knowledge_versions.id'], ),
        sa.ForeignKeyConstraint(['source_version_id'], ['source_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # entities
    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('canonical_name', sa.String(500), nullable=False),
        sa.Column('external_references', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('acl_policy', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'type', 'canonical_name', name='uq_org_entity')
    )

    # relationships
    op.create_table(
        'relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('src_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('src_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('predicate', sa.String(200), nullable=False),
        sa.Column('dst_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dst_unit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('evidence_link_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['dst_entity_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['dst_unit_id'], ['knowledge_units.id'], ),
        sa.ForeignKeyConstraint(['evidence_link_id'], ['evidence_links.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['src_entity_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['src_unit_id'], ['knowledge_units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # conflicts
    op.create_table(
        'conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_version_a_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_version_b_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='conflict_severity'), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('disposition', sa.Enum('pending', 'resolved_keep_a', 'resolved_keep_b', 'resolved_merge', 'resolved_supersede', name='conflict_disposition'), nullable=False, server_default='pending'),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['knowledge_version_a_id'], ['knowledge_versions.id'], ),
        sa.ForeignKeyConstraint(['knowledge_version_b_id'], ['knowledge_versions.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # skills
    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'review', 'published', 'needs_review', 'deprecated', name='skill_status'), nullable=False, server_default='draft'),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # skill_versions
    op.create_table(
        'skill_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('manifest', postgresql.JSONB(), nullable=False),
        sa.Column('tests', postgresql.JSONB(), nullable=False),
        sa.Column('digest', sa.String(64), nullable=False),
        sa.Column('dependency_snapshot', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.Enum('draft', 'review', 'published', 'needs_review', 'deprecated', name='skill_status'), nullable=False, server_default='draft'),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('skill_id', 'version', name='uq_skill_version')
    )

    # runs
    op.create_table(
        'runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticket_id', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'waiting_approval', 'completed', 'failed', 'aborted', 'escalated', name='run_status'), nullable=False, server_default='pending'),
        sa.Column('trace', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('idempotency_key', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['skill_version_id'], ['skill_versions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # run_events
    op.create_table(
        'run_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step', sa.String(100), nullable=False),
        sa.Column('input', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # approvals
    op.create_table(
        'approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_name', sa.String(100), nullable=False),
        sa.Column('action_arguments', postgresql.JSONB(), nullable=False),
        sa.Column('required_role', sa.String(50), nullable=False),
        sa.Column('allowed_scope', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'expired', name='approval_status'), nullable=False, server_default='pending'),
        sa.Column('decision', postgresql.JSONB(), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ticket_revision', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=False),
        sa.Column('correlation_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('prev_hash', sa.String(64), nullable=True),
        sa.Column('hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_event_org_created', 'audit_events', ['org_id', 'created_at'], unique=False)
    op.create_index('ix_audit_event_correlation', 'audit_events', ['correlation_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_event_correlation', table_name='audit_events')
    op.drop_index('ix_audit_event_org_created', table_name='audit_events')
    op.drop_table('audit_events')
    op.drop_table('approvals')
    op.drop_table('run_events')
    op.drop_table('runs')
    op.drop_table('skill_versions')
    op.drop_table('skills')
    op.drop_table('conflicts')
    op.drop_table('relationships')
    op.drop_table('entities')
    op.drop_table('evidence_links')
    op.drop_table('knowledge_versions')
    op.drop_table('knowledge_units')
    op.drop_table('chunks')
    op.drop_table('source_versions')
    op.drop_table('sources')
    op.drop_table('connectors')
    op.drop_table('users')
    op.drop_table('organizations')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS approval_status')
    op.execute('DROP TYPE IF EXISTS run_status')
    op.execute('DROP TYPE IF EXISTS skill_status')
    op.execute('DROP TYPE IF EXISTS conflict_disposition')
    op.execute('DROP TYPE IF EXISTS conflict_severity')
    op.execute('DROP TYPE IF EXISTS knowledge_status')
    op.execute('DROP TYPE IF EXISTS knowledge_type')
    op.execute('DROP TYPE IF EXISTS source_status')
    op.execute('DROP TYPE IF EXISTS source_kind')
    op.execute('DROP TYPE IF EXISTS user_status')
    op.execute('DROP TYPE IF EXISTS organization_role')