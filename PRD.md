# Product Requirements Document (PRD)

**Product:** Company Brain MVP  
**Revision:** 0.1 (2026-11-13)  
**Status:** Proposed / pending implementation

## 1. Problem and thesis

Business-critical knowledge resides in documents, threads, support tickets, systems, and unwritten decisions. A search interface can surface fragments but usually cannot establish which procedure applies, who approves an exception, and which actions are safe. **Hypothesis:** a source-backed, living knowledge model plus reviewed agent skills improves accuracy and reduces repetitive support effort compared with document-only RAG.

## 2. Target customer and users

**Initial customer:** 10–200-person service, education, or operations-heavy organization already using ERPNext/Helpdesk and maintaining SOPs in documents. This is a validation hypothesis, not proven demand.

| Role | Goal | Permissions (baseline) |
|---|---|---|
| Organization admin | Set up workspace, members, sources | Manage org and connections; not implicit access to every restricted document |
| Knowledge owner | Approve policies/processes | Review assigned knowledge, reconcile conflicts, publish skills |
| Support agent | Resolve tickets reliably | Search authorized sources, propose workflow, request approval |
| Approver | Authorize sensitive steps | Approve/reject specifically assigned runs and actions |
| Auditor | Inspect decisions and actions | Read permitted audit events and associated evidence |

## 3. Outcomes and success measures

Validate with at least **50 synthetic, manually labeled scenarios** covering current/old policies, conflicts, access limitations, missing data, and tool failures.

| Metric | MVP target | Measurement |
|---|---:|---|
| Grounded answer accuracy | >= 90% | Correct, evidence-supported answer on gold set |
| Citation support rate | >= 95% | Answer claims supported by cited source spans |
| Critical contradiction recall | >= 90% | Detected critical conflicting policies in gold set |
| Safe workflow completion | >= 90% | Correctly completed permitted sandbox scenarios |
| Unauthorized writes/messages | **0** | Security tests and audit log |
| Approval bypasses | **0** | Forced requests and state-transition tests |
| Ingestion visibility | 100% | Every processed item has result or explicit error status |

These are **targets**, not achieved measurements. Report false positives and false negatives, not only a single score.

## 4. Required MVP user journeys

### J1 — Import and process a policy

An admin uploads a permitted PDF/DOCX/MD/TXT; UI displays ingestion status, extracted text and page/section citations. Processing failures surface actionable errors. Duplicate uploads are deduplicated by organization and source version/hash.

**Acceptance:** no orphan records; source traceability retained; inaccessible material is not indexed for other users; malformed/large files fail safely.

### J2 — Review discovered company rules

The system proposes typed knowledge records (facts, policies, processes, decisions, owners, exceptions) and relationship edges, each grounded in source spans. An owner can approve, reject, edit with attribution, or flag conflicts.

**Acceptance:** unreviewed or conflicted rules cannot drive write-capable skills; all edits append history; source and effective-date visible.

### J3 — Ask a company question

A permitted user asks “Who approves a refund above the threshold?” Retrieval filters ACLs and tenant, uses keyword+vector matching, and responds with source spans or “insufficient approved evidence.”

**Acceptance:** answers never cite inaccessible documents; outdated evidence is labeled; unauthorized user receives no content leakage (including autocomplete/snippets).

### J4 — Compile an agent skill

Owner selects an approved process and requests a generated `SKILL.md`. The compiler includes purpose, prerequisites, precise steps, exception paths, evidence version references, allowed tools, approval gates, and tests. Owner reviews and publishes a new immutable skill version.

**Acceptance:** cannot publish with unresolved critical conflicts or unapproved dependency policies; export is deterministic for a fixed published version; schema and permission checks pass.

### J5 — Run a support workflow

Agent chooses a published support skill and a sandbox ERPNext ticket. The system retrieves ticket/customer state through authorized read tools, shows a proposed response, pauses for human approval, then executes only individually allowed writes/replies.

**Acceptance:** rejection aborts writes; duplicate approval/retry cannot send duplicate replies; stale approval or changed ticket requires replanning; full event trace available.

### J6 — Detect change

Reimport revised policy or update a source. The Brain identifies impacted records and skills, marks dependent skills `needs_review`, and requires republishing before affected writes.

**Acceptance:** source invalidation propagates to dependent skills; existing past runs remain auditable against their original version.

## 5. Features and prioritization

### P0 — must ship

- Single-organization-at-a-time user onboarding, secure multi-tenant schema and role enforcement.
- File-based ingestion and one read-only ERPNext ticket data connector.
- Evidence spans (document version, page/section/character range), content-hash deduplication, processing status.
- Structured extraction, editable knowledge registry and basic typed relationship graph.
- Duplicate/contradiction proposals with human reconciliation.
- ACL-filtered hybrid retrieval, grounded answers with citations and abstention.
- Skill generator (`SKILL.md`), review, publish/version/export.
- Sandboxed one-ticket workflow, approval checkpoints, allowlisted ERPNext action tools.
- Auditing, basic logs/metrics and evaluation suite.

### P1 — after MVP

- Gmail/Slack/Google Drive incremental connectors, deletion propagation, source change webhooks.
- Scheduled policy-review reminders; richer graph exploration; approval delegation.
- Additional skills (refund review, onboarding) only after safety evidence.
- Better multilingual indexing, policy OCR, role provisioning automation.

### Explicit non-goals

- No full autonomous operation or bulk updates.
- No unrestricted browser/computer automation or unreviewed skill auto-publishing.
- No fine-tuning, custom foundation model training, or unsupervised policy arbitration.
- No Neo4j, Kubernetes, marketplace, native mobile app, or 20+ integrations in v0.1.
- No production money movement, refunds, billing changes, or sensitive HR actions.

## 6. Main application screens

1. Sign in / Organization Settings / Members.
2. Sources: uploads, sync status, failures, source permission settings.
3. Brain Explorer: knowledge units, status, evidence, relation view, conflicts.
4. Ask Brain: answer, citations, evidence freshness and abstention.
5. Skills Studio: drafts, dependencies, review diffs, version history, export.
6. Agent Runs: select ticket, preview actions, approve/reject, replay trace.
7. Audit / Brain Health: unresolved conflicts, source failures, stale skills.

## 7. Functional requirements (testable)

- **FR-01:** Every resource is bound to an `org_id`; client-provided org IDs alone cannot grant access.
- **FR-02:** Source ACL rules carry through chunks, embeddings, facts and answer generation.
- **FR-03:** Every extracted rule has at least one evidence reference and status `proposed | approved | rejected | superseded | disputed`.
- **FR-04:** Search returns source citations and separately indicates approved versus unapproved material.
- **FR-05:** Critical conflicting rules block publishing dependent skills until a named reviewer resolves them.
- **FR-06:** Every skill version references specific approved knowledge versions and permitted tool contracts.
- **FR-07:** Tool calls validate org, user, skill, ticket, action, arguments and approvals server-side.
- **FR-08:** Side effects use idempotency keys and durable execution records.
- **FR-09:** Source changes invalidate relevant knowledge and mark dependent skills for review.
- **FR-10:** All write attempts, approvals, denials and tool outcomes are audited.

## 8. Nonfunctional requirements

- **Security:** TLS for deployments; encryption of connector secrets; least privilege; defensible tenant isolation; input/file limits; prompt-injection resistance; outbound tool allowlists.
- **Privacy:** configurable retention, no default training on tenant data, minimize PII sent to model providers, support source deletion and index cleanup.
- **Reliability:** resumable ingestion; retry with exponential backoff; deterministic action idempotency; network failures never imply success.
- **Performance objectives:** API non-AI read p95 < 500 ms in a small demo environment; Q&A p95 < 15 s for the evaluation dataset excluding major provider outages; queue file processing asynchronously.
- **Accessibility:** keyboard-usable approvals, error states, responsive screens, WCAG-aligned components.
- **Operability:** health checks, migrations, backup/restore runbook and per-run trace IDs.

## 9. Key risks and mitigations

| Risk | Mitigation |
|---|---|
| Conflicting or stale policy | Owner review, explicit effective dates, dependency invalidation |
| Prompt injection in untrusted content | Treat source text as data, not instructions; typed tool boundaries |
| Cross-tenant data leakage | Query-level tenant+ACL filters; adversarial isolation tests |
| Hallucinated procedure | Evidence-linked extraction; abstention; no unapproved actions |
| Accidental duplicate message | Idempotency key and ticket-state check |
| Unexpected LLM costs | Token budgets, async queues, per-org rate limits and spend limits |
| Unreliable ERPNext API | Sandbox fixtures, contract tests, retries on safe reads only |

## 10. Definition of MVP done

All P0 requirements pass `TESTING.md` gates. Demo contains one change-detection scenario, one source-grounded Q&A, one approved skill export, one approved sandbox ticket resolution, one rejected approval, and one blocked unauthorized operation. Documentation, runbook and setup instructions are reproducible by a second developer.
