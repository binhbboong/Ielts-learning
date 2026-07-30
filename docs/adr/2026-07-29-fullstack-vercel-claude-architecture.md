# ADR: Adopt Full-Stack Architecture (Angular + FastAPI + Neon PostgreSQL + Claude API) on Vercel

Date: 2026-07-29
Slug: fullstack-vercel-claude-architecture
Status: Accepted
Related spec: N/A — this decision precedes and supersedes the per-epic specs listed under Consequences; those specs are not yet updated to match.

## Context

The V1 architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`) committed this project to a single client-only Angular app with no backend, IndexedDB as the sole data store, and static GitHub Pages deployment — chosen specifically to keep the project free to run and simple to maintain for one solo learner. Epic-1 (`study-plan-execution`) was fully implemented against that architecture: 19/19 tasks, IndexedDB-backed repository/facade, tested and verified running.

The user has now provided a new governing specification (`Personal_IELTS_Learning_Dashboard_Claude_Spec.md`, v3.0) that requires capabilities the client-only architecture cannot support: AI-graded Writing and Speaking submissions via the Claude API (which must never be called directly from the browser, to avoid exposing the API key), a server-side database, and deployment to Vercel rather than GitHub Pages. This is not a refinement of V1 — it is a different architecture with different constraints, and per this project's constitution (principle 1), a decision this consequential must be recorded before downstream docs are brought back into alignment with it, rather than left to drift silently.

## Decision

The project adopts a full-stack architecture:

- **Frontend**: Angular (unchanged as the UI framework), calling a REST API instead of reading/writing IndexedDB directly.
- **Backend**: FastAPI, owning all business logic and acting as the sole caller of any AI provider. The Claude API key lives only in backend environment variables and is never exposed to the frontend.
- **Database**: Neon PostgreSQL (managed, serverless Postgres), replacing IndexedDB as the system of record. Schema managed via SQLAlchemy models and Alembic migrations.
- **AI evaluation**: Writing and Speaking submissions are evaluated by an AI provider abstraction (`AIProvider` interface: `evaluate_writing()`, `evaluate_speaking()`, `generate_quiz()`, `chat()`) with Claude as the initial implementation (`ClaudeProvider`), selected via an `AI_PROVIDER` environment variable so the provider is swappable without a rewrite.
- **Speech-to-Text**: a separate external API produces the transcript for Speaking submissions; pronunciation is explicitly "Not Assessed" until a dedicated speech-assessment integration is added later.
- **Deployment**: both the Angular frontend and the FastAPI backend deploy to Vercel; Neon is accessed over the network from the Vercel-hosted backend. Secrets live only in Vercel environment variables.

## Consequences

- **Supersedes**: `docs/adr/2026-07-29-v1-no-backend-architecture.md` is marked Superseded by this ADR.
- **Directly obsoletes** the data-model ADRs written against the IndexedDB/client-only design — these will need new equivalents (or explicit revision) once the corresponding specs are rewritten:
  - `docs/adr/2026-07-29-study-plan-flat-task-store.md` (IndexedDB task/planState store)
  - `docs/adr/2026-07-29-vocab-forgot-resets-interval.md` (interval rule itself likely still valid, but the storage mechanism it's written against is not)
  - `docs/adr/2026-07-29-mistake-reason-category-enum-key.md` (IndexedDB key representation)
  - `docs/adr/2026-07-29-missed-question-type-taxonomy.md` (storage mechanism assumption)
  - `docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md` (this entire epic's premise — a manual export/import safety net for a browser-only store — is largely moot once a server-side Postgres database is the system of record; this needs a product-level decision, not just a technical rewrite, on what "backup" even means now)
- **Invalidates Epic-1's implementation**: the working `study-plan-execution` code (IndexedDB repository, facade, components) was built against the superseded architecture and cannot run against a REST API + Postgres backend without a rewrite of its data layer at minimum. Whether to discard, archive, or mine it for reusable UI component logic is an open product decision, not resolved by this ADR.
- **Vision-level tension, not just architectural**: `docs/business/Vision.md`'s Non-Goals explicitly excludes "AI-driven Writing/Speaking coaching in the first version" and its constraints assume no server hosting cost and no vendor dependency. The new spec makes AI coaching a Phase 2 target and introduces real vendor dependencies (Neon, Vercel, an AI provider). This ADR records the technical/architectural decision only — it does NOT revise Vision.md's goals, non-goals, or success metrics, which is a separate, required follow-up (`/business:vision`) before downstream docs are rewritten to match.
- **Easier**: unlocks AI-graded Writing/Speaking feedback, multi-device access to the same data (a real database is reachable from anywhere, unlike a single browser's IndexedDB), and a swappable AI provider layer instead of a single-vendor hard dependency.
- **Harder**: the project now has real operating costs (Neon, Vercel, AI API usage) and infrastructure to maintain (migrations, API deployment, secret management) that the V1 architecture was deliberately designed to avoid; API keys must be handled with real security discipline (server-side only, never committed).
