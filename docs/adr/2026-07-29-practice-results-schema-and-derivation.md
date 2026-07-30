# ADR: Practice Results Table Shape and On-Demand Trend Derivation

Date: 2026-07-29
Slug: practice-results-schema-and-derivation
Status: Accepted
Related spec: docs/specs/progress-tracking/Specification.md

## Context

Epic-4 is being rebuilt against the new full-stack architecture
(`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`): Neon PostgreSQL via SQLAlchemy
models and Alembic migrations, replacing the superseded IndexedDB design that
`docs/adr/2026-07-29-missed-question-type-taxonomy.md` was written against (that ADR's storage
assumption is already flagged stale in `docs/adr/DECISIONS.md`; its taxonomy-is-a-fixed-list
decision itself still stands and is not revisited here).

Two forks need deciding before a migration or service code can be written, and both are the kind
of thing other code will depend on once written: (1) how a `PracticeResult` row is shaped
relationally — in particular how `skill` and `missed_question_types` are represented — and (2)
how the average score, trend direction, 4-session threshold (FR-8), and missed-type breakdown
(FR-7) get computed. PRD Epic-4's scope note additionally requires that the schema not make it
awkward to later fold in Writing/Speaking band estimates once those epics exist, which bears
directly on how `skill` is typed.

## Decision

**Table shape**: one denormalized `practice_results` table (no per-learner column — single-learner
system per the architecture's simplification). `skill` is a plain `VARCHAR`, not a Postgres native
`ENUM` type and not a `CHECK` constraint enumerating exactly `Reading`/`Listening` — validity is
enforced in the service layer against a small, code-level allow-list, so adding `Writing` or
`Speaking` later is a one-line code change, not a migration that alters a DB type (native Postgres
enums require `ALTER TYPE ... ADD VALUE`, which cannot run inside the same transaction as other
DDL/DML on some Postgres versions — a real, if minor, migration-time footgun for a decision this
easy to avoid). `missed_question_types` is a Postgres `ARRAY(VARCHAR)` column on the same row (not
a separate join table) — the fixed per-skill taxonomy (per the taxonomy ADR) makes a normalized
many-to-many table unnecessary complexity at this scale (a handful of tags per record, no reuse of
tag rows across records that needs referential integrity). The taxonomy's canonical constant now
lives in backend code (`backend/app/models/practice_result_taxonomy.py`) and is exposed read-only
to the frontend via `GET /practice-results/taxonomy`, since "one shared constant" from the prior
ADR can no longer mean one file once frontend and backend are separate processes/languages.

**Derivation**: average score, trend direction, threshold status, and missed-type breakdown are
computed on demand, in the service layer, from one indexed SQL `SELECT` per request (filtered by
`skill` and a `logged_at` cutoff for the selected period) — never persisted as a running aggregate.
See the Implementation Plan's Approach section for the full comparison; the reasoning mirrors the
superseded plan's Approach 1 (sliding time windows make persisted aggregates stale, and this
data scale — one learner, realistically hundreds of rows over years — makes recomputation
trivially cheap).

## Consequences

- **Easier**: extending `skill` to include `Writing`/`Speaking` later is an allow-list edit plus
  (if those epics store richer per-skill fields) an additive migration, not a destructive one;
  the trend/breakdown computation has a single code path with no cache or second table to keep in
  sync, so FR-7's "always render together" constraint and FR-11's refresh requirement are direct
  consequences of the data flow rather than something that has to be separately guaranteed.
- **Harder**: every trend/history read does a full-row fetch for the matching skill/period rather
  than reading a pre-summed value; acceptable at this project's scale (see Implementation Plan),
  but would need revisiting if this became a multi-tenant product.
- **Forecloses**: a DB-level guarantee that `skill` only ever holds two specific values — validity
  is an application-level contract now, not a schema-level one. Also forecloses ever storing a
  `missed_question_type` value that isn't a simple string tag without a follow-up migration (the
  array column has no room for per-tag metadata); acceptable since the taxonomy ADR already fixes
  the tags as a closed, flat, per-skill list.
- **Does not decide**: the actual taxonomy content (still open, see Implementation Plan Risks), nor
  how Writing/Speaking submissions will eventually be scored or stored (Epic-7/8's own plans).
