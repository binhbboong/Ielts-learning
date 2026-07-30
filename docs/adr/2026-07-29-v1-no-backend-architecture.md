# ADR: V1 Architecture is Client-Only, No Backend

Date: 2026-07-29
Slug: v1-no-backend-architecture
Status: Superseded by 2026-07-29-fullstack-vercel-claude-architecture
Related spec: N/A — no feature specs exist yet under docs/specs/

## Context

The PRD (`docs/business/PRD.md`) constrains V1 (Epics 1-5) to operate with no paid hosting, database, or backend service, and the Vision commits to full learner data ownership with no vendor lock-in. `docs/architecture/Architecture.md` was already drafted describing a single client-side Angular app with no server component, but that description existed only as architecture-writing output — no ADR had formally recorded it as a settled decision, so nothing durable stopped a future spec or plan from silently assuming a backend exists. Before implementation begins on any V1 epic, this needs to be locked down as an accepted decision.

## Decision

V1 of the Personal IELTS Learning Dashboard is a single client-side Angular application with no backend or server component. All learner data (study plan, vocabulary, mistakes, practice results) is persisted entirely in the browser — IndexedDB for structured records, LocalStorage only for small settings/config. The app deploys as a static build to GitHub Pages via CI. There is no authentication, no server-side database, and no API layer in V1. Any capability that would require server-side logic or held credentials — notably Epic-6 (AI-assisted Writing/Speaking coaching) — is explicitly out of V1's architecture and deferred to its own future decision when that epic is picked up.

## Consequences

- Easier: zero hosting/infra cost, no auth system to build or maintain, a simple static-deploy pipeline, and a single durability story (Epic-5's export/import) instead of a database backup strategy.
- Harder: no cross-device sync and no automatic cloud backup — data loss risk if the learner clears browser storage or switches devices without exporting first.
- Forecloses: implementing Epic-6 (AI-assisted coaching) within the V1 architecture as-is. Introducing a backend to proxy AI provider calls is a real future architectural change and should get its own decision (and likely its own ADR) when Epic-6 is actually picked up — not silently bolted onto V1's client-only design.
