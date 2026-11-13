# Changelog

All notable project changes are recorded here. This follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions represent **specification or software milestones**; the current release is documentation-only.

## [Unreleased]

### Added
- T-001: Repository foundation with Next.js 14 (App Router), FastAPI, Docker Compose
- Backend: FastAPI app with config, logging, Celery, SQLAlchemy 2, pgvector models
- Frontend: Next.js with TypeScript, Tailwind CSS, shadcn/ui components
- Docker Compose: PostgreSQL+pgvector, Redis, MinIO, API, Worker, Beat, Web
- Environment template (.env.example) with all required configuration
- Database models for organizations, users, sources, knowledge, skills, runs, approvals, audit
- Alembic migration setup
- Health check endpoints and structured logging with correlation IDs
- Authentication framework with JWT tokens and role-based access
- T-002: CI pipeline with lint, typecheck, unit tests, security/dependency checks (GitHub Actions)
- T-003: PostgreSQL + pgvector, Alembic migrations, MinIO, Redis/Celery configured
- T-004: Authentication, org memberships, roles and tenant isolation with cross-tenant tests
- T-005: Audit event schema with tamper-evident hash chain, correlation IDs middleware, standardized API error contract, structured logging

### Planned

- Source upload, immutable versions, parsing, extraction and evidence-backed knowledge.
- Knowledge review, conflicts, permission-aware retrieval and cited answers.
- Skill compilation, publishing, dependency invalidation and export.
- Approval-gated sandbox ERPNext Helpdesk ticket workflow.
- Safety evaluation, deployment runbook and audit trail.

## [0.1.0-spec] — 2026-11-13

### Added

- `README.md`: project overview, MVP demonstration and setup expectations.
- `PRD.md`: target users, journeys, P0/P1 scope, functional requirements and success criteria.
- `ARCHITECTURE.md`: service architecture, data model, API, knowledge lifecycle and safety controls.
- `AGENTS.md`: implementation-agent instructions and runtime-agent trust/tool rules.
- `TASKS.md`: sequenced, testable backlog for MVP development.
- `CONTEXT.md`: decision log, assumptions, vocabulary and open questions.
- `TESTING.md`: unit, integration, security and evaluation strategy.
- This changelog.

### Note

No application code, infrastructure, integration or benchmarks are included in this specification release. Mark any subsequent feature as **implemented** only after testing.

<!-- Future entry template:
## [version] — YYYY-MM-DD
### Added
### Changed
### Fixed
### Security
### Tests
### Known limitations
-->
