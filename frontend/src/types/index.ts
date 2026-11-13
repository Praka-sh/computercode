export interface Organization {
  id: string
  name: string
  policy_settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  org_id: string
  email: string
  full_name: string | null
  role: UserRole
  status: UserStatus
  provider_id: string | null
  created_at: string
  updated_at: string
}

export type UserRole =
  | 'admin'
  | 'knowledge_owner'
  | 'support_agent'
  | 'approver'
  | 'auditor'

export type UserStatus = 'active' | 'revoked'

export interface Source {
  id: string
  org_id: string
  connector_id: string | null
  kind: SourceKind
  external_key: string | null
  owner_id: string
  acl_policy: Record<string, unknown>
  status: SourceStatus
  current_version_id: string | null
  created_at: string
  updated_at: string
}

export type SourceKind = 'file' | 'erpnext' | 'gmail' | 'slack' | 'google_drive'
export type SourceStatus = 'active' | 'archived' | 'syncing' | 'error'

export interface SourceVersion {
  id: string
  source_id: string
  checksum: string
  captured_at: string
  effective_at: string | null
  blob_uri: string
  metadata: Record<string, unknown>
  parser_version: string | null
  created_at: string
}

export interface Chunk {
  id: string
  source_id: string
  source_version_id: string
  page: number | null
  section: string | null
  start_offset: number
  end_offset: number
  text: string
  embedding: number[] | null
  created_at: string
}

export interface KnowledgeUnit {
  id: string
  org_id: string
  type: KnowledgeType
  label: string
  owner_id: string | null
  status: KnowledgeStatus
  created_at: string
  updated_at: string
}

export type KnowledgeType = 'fact' | 'policy' | 'process' | 'decision' | 'owner' | 'exception'
export type KnowledgeStatus = 'proposed' | 'approved' | 'rejected' | 'superseded' | 'disputed'

export interface KnowledgeVersion {
  id: string
  unit_id: string
  claim: KnowledgeClaim
  source_evidence: EvidenceReference[]
  effective_from: string | null
  effective_to: string | null
  status: KnowledgeStatus
  reviewer_id: string | null
  reviewed_at: string | null
  extractor_version: string
  created_at: string
}

export interface KnowledgeClaim {
  kind: string
  subject: string
  predicate: string
  object: string
  qualifiers: Record<string, unknown>
  scope: Record<string, unknown>
  effective_from: string | null
  effective_to: string | null
}

export interface EvidenceReference {
  source_version_id: string
  chunk_id: string | null
  page: number | null
  span_start: number
  span_end: number
}

export interface Conflict {
  id: string
  org_id: string
  knowledge_version_a_id: string
  knowledge_version_b_id: string
  severity: ConflictSeverity
  rationale: string
  disposition: ConflictDisposition
  reviewed_by_id: string | null
  resolved_at: string | null
  created_at: string
}

export type ConflictSeverity = 'low' | 'medium' | 'high' | 'critical'
export type ConflictDisposition = 'pending' | 'resolved_keep_a' | 'resolved_keep_b' | 'resolved_merge' | 'resolved_supersede'

export interface Skill {
  id: string
  org_id: string
  name: string
  description: string | null
  status: SkillStatus
  current_version_id: string | null
  created_at: string
  updated_at: string
}

export type SkillStatus = 'draft' | 'review' | 'published' | 'needs_review' | 'deprecated'

export interface SkillVersion {
  id: string
  skill_id: string
  version: string
  content: string
  manifest: SkillManifest
  tests: SkillTests
  digest: string
  dependency_snapshot: Record<string, string>
  status: SkillStatus
  reviewer_id: string | null
  reviewed_at: string | null
  created_at: string
}

export interface SkillManifest {
  skill_id: string
  version: string
  digest: string
  allowed_tools: string[]
  required_roles: string[]
  source_version_ids: string[]
  expires_at: string | null
}

export interface SkillTests {
  happy_path: TestCase[]
  contradiction: TestCase[]
  missing_permission: TestCase[]
  missing_evidence: TestCase[]
  approval_rejection: TestCase[]
  duplicate_action: TestCase[]
}

export interface TestCase {
  name: string
  input: Record<string, unknown>
  expected_output: Record<string, unknown>
  should_pass: boolean
}

export interface Run {
  id: string
  org_id: string
  skill_version_id: string
  user_id: string
  ticket_id: string
  status: RunStatus
  trace: Record<string, unknown>
  idempotency_key: string
  created_at: string
  updated_at: string
}

export type RunStatus = 'pending' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'aborted' | 'escalated'

export interface RunEvent {
  id: string
  run_id: string
  step: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  status: string
  error: string | null
  created_at: string
}

export interface Approval {
  id: string
  run_id: string
  action_name: string
  action_arguments: Record<string, unknown>
  required_role: string
  allowed_scope: Record<string, unknown>
  status: ApprovalStatus
  decision: Record<string, unknown> | null
  actor_id: string | null
  ticket_revision: string
  expires_at: string
  decided_at: string | null
  created_at: string
}

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired'

export interface AuditEvent {
  id: string
  org_id: string
  actor_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  outcome: string
  correlation_id: string | null
  metadata: Record<string, unknown>
  created_at: string
}