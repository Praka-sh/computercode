# MVP Implementation Tasks

**Tracking:** `[ ]` not started, `[x]` tested and complete. All tasks begin unchecked because this package contains planning files only.  
**Scope authority:** `PRD.md` and `ARCHITECTURE.md`.  
**Rule:** Do not check off a task before matching tests pass; track blockers next to the task.

## Milestone M0 — Repository foundation

- [x] **T-001** Initialize monorepo, Next.js app, FastAPI app, `.env.example`, Docker Compose. **Done when:** clean clone starts UI/API/database/worker locally and secrets are not committed.
- [x] **T-002** Add CI lint, typecheck, unit tests, security/dependency checks. **Depends:** T-001. **Done when:** PR pipeline reliably rejects failing tests.
- [x] **T-003** Configure PostgreSQL + pgvector, Alembic, MinIO, Redis/Celery. **Depends:** T-001. **Done when:** migrations apply on clean DB and workers process a sample job.
- [x] **T-004** Authentication, org memberships, roles and tenant isolation. **Depends:** T-003. **Done when:** unauthorized/cross-org requests are denied, tested at API and DB query layers.
- [x] **T-005** Audit event schema, correlation IDs, API error contract and structured logging. **Depends:** T-003/T-004. **Done when:** access denials and writes have traceable events without secrets.

## Milestone M1 — Source ingestion

- [ ] **T-101** Create source/version/chunk schema with ACL and ownership fields. **Depends:** T-003/T-004. **Done when:** source versions immutable and org-scoped.
- [ ] **T-102** Implement PDF/DOCX/MD/TXT upload, size/type validation and safe S3 storage. **Depends:** T-101. **Done when:** authorized uploads return job IDs; unsupported/malicious files fail closed.
- [ ] **T-103** Implement async parse/chunk pipeline preserving page and span references. **Depends:** T-102. **Done when:** test docs reproduce attributable citations and error statuses.
- [ ] **T-104** Deduplicate source versions by content hash and index ACL-filtered pgvector embeddings. **Depends:** T-103. **Done when:** duplicates do not multiply chunks and permissions are inherited.
- [ ] **T-105** Build Sources UI with upload, processing states, source details and errors. **Depends:** T-102/T-103. **Done when:** keyboard-usable end-to-end flow works.

## Milestone M2 — Knowledge model and review

- [ ] **T-201** Define Pydantic extraction contracts for fact/policy/process/decision/exception/owner and evidence spans. **Depends:** T-103. **Done when:** malformed, unsupported or uncited output rejected.
- [ ] **T-202** Implement extraction worker with configurable provider, token budgets and fixture-based tests. **Depends:** T-201. **Done when:** same fixtures produce valid typed records or explicit errors.
- [ ] **T-203** Create entities, relationships and knowledge version/history schema. **Depends:** T-201. **Done when:** graph traversal exposes permitted evidence.
- [ ] **T-204** Implement duplicate/conflict/supersession proposals with effective date and scope. **Depends:** T-202/T-203. **Done when:** synthetic conflict gold set evaluated with precision and recall.
- [ ] **T-205** Implement owner review and conflict resolution API with optimistic version locks. **Depends:** T-204/T-004. **Done when:** rejected/unreviewed knowledge cannot be marked authoritative without proper role.
- [ ] **T-206** Build Brain Explorer UI: knowledge status, source citation, relation edges, conflicts and reviews. **Depends:** T-205. **Done when:** reviewer can resolve a sample contradiction and view history.

## Milestone M3 — Grounded Q&A

- [ ] **T-301** Implement authorization-filtered hybrid keyword/vector retrieval and ranked evidence. **Depends:** T-104/T-205. **Done when:** cross-tenant and source-ACL leak tests pass.
- [ ] **T-302** Implement `/ask` grounded generation with citation verification, effective dates and abstention. **Depends:** T-301. **Done when:** answer claims point to authorized spans; contradictions trigger abstention.
- [ ] **T-303** Implement Ask Brain UI with citations, empty/error/insufficient-evidence states. **Depends:** T-302. **Done when:** user can inspect a referenced original span.
- [ ] **T-304** Build 50-scenario evaluation set and baseline comparison with document-only retrieval. **Depends:** T-302. **Done when:** metrics and errors are reproducible and reported honestly.

## Milestone M4 — Skills Studio

- [ ] **T-401** Define skill schema, dependencies, version/digest and review states. **Depends:** T-205. **Done when:** published versions immutable and org-scoped.
- [ ] **T-402** Implement skill compiler to `SKILL.md`, `manifest.json`, `tests.json` with source snapshots. **Depends:** T-401. **Done when:** fixed inputs yield reproducible export and clear missing-dependency errors.
- [ ] **T-403** Implement owner approval/publish, diff view, download and invalidation on source change. **Depends:** T-402/T-204. **Done when:** unresolved conflict blocks publish; changed source marks skill stale.
- [ ] **T-404** Build Skills Studio UI with compile/review/version history/export. **Depends:** T-403. **Done when:** owner publishes and downloads a reviewed support skill.

## Milestone M5 — Sandbox ERPNext execution

- [ ] **T-501** Implement pinned-host, least-privilege, sandbox-only ERPNext connector and mock server. **Depends:** T-004. **Done when:** connector rejects production/unapproved URLs and can read synthetic tickets.
- [ ] **T-502** Define allowlisted typed read and write tool contracts with role/action checks. **Depends:** T-501/T-005. **Done when:** arbitrary endpoints/tool names/arguments are rejected.
- [ ] **T-503** Implement durable LangGraph run state, planning and controlled evidence retrieval. **Depends:** T-302/T-403/T-502. **Done when:** run resumes after process restart without lost state.
- [ ] **T-504** Implement one-time approval gate tied to exact action, arguments, skill, revision and expiry. **Depends:** T-503. **Done when:** denial, tampering, replay, expiry and wrong approver tests all block writes.
- [ ] **T-505** Implement idempotent sandbox write, remote-state revalidation and post-action audit. **Depends:** T-504. **Done when:** duplicate submission creates at most one side effect.
- [ ] **T-506** Build Agent Workspace: run plan, evidence, approve/reject controls, trace, outcome. **Depends:** T-505. **Done when:** end-to-end sandbox ticket flow works and errors are visible.

## Milestone M6 — Hardening and demonstration

- [ ] **T-601** End-to-end abuse tests: prompt injection, cross-tenant ACL, source deletion, stale skills, duplicate actions, forged approval. **Depends:** M1–M5. **Done when:** all critical safety tests pass.
- [ ] **T-602** Performance, cost caps, accessibility and failure/recovery testing. **Depends:** M1–M5. **Done when:** test results recorded against PRD targets.
- [ ] **T-603** Deployment guide, backups, restore test, setup fixtures and synthetic demonstration video/script. **Depends:** T-601. **Done when:** second developer deploys from clean clone.
- [ ] **T-604** Conduct 5–10 design-partner interviews and record usability findings. **Depends:** M3–M5 prototype. **Done when:** prioritized feedback in `CONTEXT.md`/product backlog.

## Suggested 4-week sequence (stretch target, not guarantee)

| Week | Focus | Exit demo |
|---|---|---|
| 1 | M0 + M1 | Secure organization uploads a source and sees citations |
| 2 | M2 + M3 | Owner resolves policy conflict; Ask Brain cites evidence |
| 3 | M4 + M5 core | Skill published; sandbox agent pauses for approval |
| 4 | M5 complete + M6 | Verified ticket action + replay/denial/cross-tenant tests |

## Task selection instructions for coding agents

1. Select lowest-numbered unblocked task; do **not** implement unrelated features.
2. Implement schema/API/UI/tests as required by the acceptance condition.
3. Record any blocked dependency and avoid silently skipping authorization tests.
4. Run relevant test commands from `TESTING.md`.
5. Check off task, update `CHANGELOG.md`, and report evidence of completion.
