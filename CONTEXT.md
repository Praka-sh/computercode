# Shared Project Context and Decisions

**Read before making product or architecture decisions.** This file records assumptions, boundaries, open questions and decisions so that collaborators and coding agents don't repeatedly redesign the same MVP.

## 1. Source problem statement

YC's *Company Brain* concept describes a missing domain-knowledge layer for AI automation. Company knowledge is fragmented across email, chat, support, databases and people's heads. A company brain should structure and refresh that knowledge, reflect how the business works and compile it into reusable agent skills. It must be more than enterprise search or document-chat RAG.

Reference: https://www.ycombinator.com/rfs#company-brain

## 2. Working product definition

**Working name:** Company Brain MVP (placeholder; no brand decision).  
**One-line value proposition:** Evidence-backed company procedures converted into reviewable, safe-to-execute AI skills.  
**Initial persona:** support/operations administrator and policy owner.  
**Initial integration:** sandbox ERPNext Helpdesk; files first.  
**First skill:** ticket triage and resolution proposal with explicit human approval before external response or ticket update.

**Design center:** trustworthy process knowledge and safe execution, not breadth of connectors or model cleverness.

## 3. Locked MVP decisions (ADR log)

| ADR | Decision | Reason | Revisit condition |
|---|---|---|---|
| ADR-001 | Next.js/TypeScript frontend; FastAPI/Python backend | Fast UI iteration and mature AI tooling | Proven team/runtime constraint |
| ADR-002 | PostgreSQL + pgvector + relational edges | Lower operational complexity than separate graph/vector services | Measured retrieval/graph bottleneck |
| ADR-003 | Celery/Redis jobs and S3-compatible blobs | Async, resumable document processing | Operational complexity warrants change |
| ADR-004 | LangGraph for the first approval-gated agent | Durable state and explicit checkpoints | Demonstrated simpler safe alternative |
| ADR-005 | Human-reviewed knowledge and skill publication | LLM proposals can be inaccurate | Never waive for critical business actions |
| ADR-006 | File upload + sandbox ERPNext only | Focused vertical slice with measurable result | P0 completed, user demand proven |
| ADR-007 | No production outbound writes in MVP | Prevent accidental customer impact | Formal security/release approval |
| ADR-008 | Skills are instructions, not permissions | Avoid authorization bypass through text | Do not change |
| ADR-009 | Separate coding-agent and runtime-agent policy | Development instructions differ from business actions | Do not change |

## 4. Key vocabulary

- **Source:** uploaded file or synchronized external record, with ACL and provenance.
- **Source version:** immutable snapshot of source content and parser metadata.
- **Knowledge unit:** normalized concept such as a policy, decision, owner or process.
- **Knowledge version:** specific sourced claim and its review/effective-date state.
- **Evidence link:** reference to exact source version and page/span supporting a claim.
- **Conflict:** proposal that two claims cannot simultaneously apply under same scope/time.
- **Skill:** instructions for an AI workflow compiled from reviewed procedures.
- **Skill version:** immutable reviewed artifact with dependency snapshot and hash.
- **Tool:** backend-operated integration method with a typed schema and authorization policy.
- **Agent run:** durable workflow instance with actions, approvals and audit trail.
- **Approval:** revocable, expiring human authorization for a *specific* proposed action.

## 5. Environments and assumptions

- **Local:** Docker Compose; synthetic test organization and documents.
- **Demo:** secured HTTPS deployment with synthetic tickets, sandbox ERPNext and restricted service account.
- **Production:** outside MVP; requires independent security review, incident response, DR, privacy compliance, and operational readiness.
- Assume a provider API for extraction and embedding; permit local provider substitution only through existing typed interfaces.
- No live credentials, server IPs, private company data or personal identifiers belong in repository documentation.
- Costs and delivery time are estimates to be validated, not guarantees.

## 6. Open product questions (not blockers to starting scaffolding)

1. Which design partners will participate, and what are their strongest repetitive support workflows?
2. What exact ERPNext versions, ticket fields and permissions are present in the sandbox?
3. Which LLM/embedding provider, region, privacy terms and budget ceiling are acceptable?
4. What retention/deletion requirements do target organizations need?
5. Who is authorized to review each policy type, and how is role delegation handled?
6. Which languages do early users require for documents and ticket replies?
7. Should the first demo send actual **sandbox** replies, or only simulate send-and-verify?

Resolve in implementation issues; until answered, choose secure, documented defaults without expanding scope.

## 7. Explicitly deferred

Automatic extraction from employee conversations; live email/Slack sync; production ERPNext access; full self-service enterprise onboarding; financial automation; autonomous publishing; large graph visual analytics; company-wide search product positioning; native apps.

## 8. Handoff guidance

When starting a new development session, read `TASKS.md` and locate the next unblocked item. Cross-check expected behavior against `PRD.md`, data/API design against `ARCHITECTURE.md`, security rules against `AGENTS.md`, and acceptance tests against `TESTING.md`. Record architectural changes here with rationale and date, then update `CHANGELOG.md`.
