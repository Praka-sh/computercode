# Company Brain MVP

> Turn fragmented company knowledge into verified, versioned, executable AI workflows.

**Status:** Specification / pre-implementation. No features described here should be assumed implemented.

## The problem

Company know-how is fragmented across documents, conversations, business tools, decisions, and employees. Search and document chat help find information, but do not reliably establish the *current authoritative procedure* or enable safe execution. This product creates an evidence-backed, permission-aware map of policies, decisions, processes, owners, and exceptions and compiles reviewed processes into usable agent skills.

## MVP promise

Given an organization's policy documents and a sandbox ERPNext Helpdesk account, an authorized user can:

1. Ingest content and inspect its original evidence.
2. Review extracted knowledge units and linked entities.
3. Identify and resolve contradictory or superseded policies.
4. Ask grounded questions and see citations or a clear abstention.
5. Generate, review, version, and export a `SKILL.md` for a process.
6. Run the approved support-ticket skill in a **sandbox**, propose a response, require human approval, and perform only allowed ticket actions with a full audit trail.

**Not** a generic autonomous agent, universal integration layer, or unrestricted company-wide chatbot.

## First use case: ERPNext support-ticket triage

Example: a ticket says, “I paid for a course, but I cannot access it.” The agent loads the ticket, searches approved enrollment/access procedures, checks an authorized test account, drafts a recommended response, and pauses for an agent's approval. Only after approval may it update the test ticket and send a reply through an explicitly enabled tool. Uncertain or conflicting policy results in escalation, not improvisation.

## Tech stack

| Layer | Selection |
|---|---|
| Frontend | Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, React Flow |
| API | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Data | PostgreSQL 16+ with pgvector; graph modeled with relational entity/edge tables |
| Files | S3-compatible object storage (MinIO locally) |
| Processing | Celery + Redis; Docling for text/table extraction; PyMuPDF as fallback |
| AI | Configurable LLM and embedding providers, structured JSON outputs |
| Agent | LangGraph with durable checkpoints, typed tools, explicit approval gates |
| Observability | JSON logs, OpenTelemetry, optional Langfuse |
| Deployment | Docker Compose local/single-VPS; HTTPS reverse proxy for deployed demo |

Use one FastAPI service plus workers, **not microservices**. PostgreSQL is the single metadata, graph, and vector store for MVP.

## Repository structure (target)

```text
company-brain/
├── README.md
├── PRD.md
├── ARCHITECTURE.md
├── AGENTS.md
├── TASKS.md
├── CONTEXT.md
├── CHANGELOG.md
├── TESTING.md
├── .env.example                 # safe placeholders only
├── docker-compose.yml
├── frontend/                    # Next.js application
├── backend/
│   ├── app/
│   │   ├── api/                 # versioned endpoints
│   │   ├── core/                # config, authz, tenant context
│   │   ├── db/                  # schema, migrations
│   │   ├── connectors/          # file + ERPNext
│   │   ├── ingestion/           # parsing/chunking/provenance
│   │   ├── extraction/          # typed knowledge units
│   │   ├── reconciliation/      # duplicate/conflict/version checks
│   │   ├── retrieval/           # ACL-filtered hybrid search
│   │   ├── skills/              # compiler, versioning, validation
│   │   ├── agents/              # graph, tools, approval pauses
│   │   └── audit/
│   └── tests/
├── evaluation/                  # curated synthetic datasets and gold labels
└── samples/                     # synthetic documents and tickets only
```

## Local setup (once code exists)

Prerequisites: Docker Engine + Compose, Node.js 22 LTS, Python 3.12+, and a configured AI provider API key. Exact startup commands may change as implementation is completed.

```bash
cp .env.example .env
# Fill in local credentials and API keys; NEVER commit .env
docker compose up --build
```

Target URLs: frontend `http://localhost:3000`, API `http://localhost:8000/docs`. These are *planned* defaults, not confirmed running services.

## Core demo

1. Create an organization and sign in as administrator.
2. Upload two synthetic policy versions with an intentional contradiction.
3. Confirm both evidence references are visible and the newer policy is not silently made authoritative.
4. Have the policy owner resolve the conflict and approve a process.
5. Generate and approve a versioned support-ticket `SKILL.md`.
6. Connect a sandbox ERPNext site with a least-privilege service account.
7. Run a synthetic ticket; inspect planned actions, approve the response, then verify the ticket changed and the audit log recorded all steps.
8. Attempt an unauthorized operation; verify it is denied.

## Non-negotiable safeguards

- Tenant and user authorization **before** returning any retrieval results, not just in the UI.
- Source documents, emails, and tickets are **untrusted data**, never executable instructions.
- No production ERPNext writes or outbound customer messages in the initial demo.
- Model output never directly authorizes a business action.
- Every publishable policy and skill has reviewer, evidence, version, and status.
- Secrets in environment/secret store; encrypt connector credentials; redact sensitive logs.
- Keep a tamper-evident audit sequence of approvals, tool calls, and results.

## Reading order

1. [PRD.md](PRD.md) — goals, stories, acceptance criteria.
2. [ARCHITECTURE.md](ARCHITECTURE.md) — components, data model, API contracts, and workflows.
3. [AGENTS.md](AGENTS.md) — rules for coding agents and runtime AI agents.
4. [TASKS.md](TASKS.md) — actionable implementation checklist and dependencies.
5. [TESTING.md](TESTING.md) — quality gates and safety tests.
6. [CONTEXT.md](CONTEXT.md) — assumptions and fixed product decisions.
7. [CHANGELOG.md](CHANGELOG.md) — tracked specification changes.

## Suggested development workflow

Complete one numbered task from `TASKS.md` at a time; implement the matching test; update docs and `CHANGELOG.md`; and verify the acceptance criteria before marking the task complete. All externally connected data should be synthetic or explicitly authorized.

## References

- YC request: https://www.ycombinator.com/rfs#company-brain
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- MCP: https://modelcontextprotocol.io/
- pgvector: https://github.com/pgvector/pgvector

See [CONTEXT.md](CONTEXT.md) for scope decisions. This repository documentation is the planned product specification, not an implementation claim.
