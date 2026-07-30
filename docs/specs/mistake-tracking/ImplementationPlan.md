# Implementation Plan: Mistake Tracking & Pattern Insight
Spec: docs/specs/mistake-tracking/Specification.md
Architecture: docs/architecture/Architecture.md (Mistake Notebook module)
Supersedes: the prior version of this plan, written against the now-superseded client-only/IndexedDB
architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`). Rewritten against
`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`. No code exists against either version yet,
so this is a full rewrite, not a migration.

## Constitution Check

- **Principle 1 (upstream docs are the contract)**: this plan builds on FR-1..FR-16, which are explicitly
  reusable as-is (unchanged by the architecture pivot), and on
  `docs/adr/2026-07-29-mistake-reason-category-enum-key.md`, whose string-key decision is
  technology-independent and is carried forward directly rather than re-litigated.
- **Principle 2 (tests before code)**: every module below is built test-first per
  `test-driven-development`. Backend: pytest tests for `services/mistake.py` and `routers/mistake.py`
  written before their implementations, against a test database session. Frontend: Angular component/unit
  tests for `data/`, `state/`, and `pages/` written before their implementations, using a fake
  `MistakeRepository`/HTTP layer. No task in a future `Tasks.md` is done until its test is written first
  and passes. No FR in this spec has a conflict with a constitution principle — no exception needed.
- **Principle 6 (docs are durable)**: this file replaces the prior `ImplementationPlan.md` in place
  (confirmed appropriate — the prior plan's own header states it targets an architecture no longer in
  effect and no code was ever written against it). `docs/specs/mistake-tracking/Tasks.md` still reflects
  the old plan and is now stale; it is left untouched here (out of this plan's scope) but will need
  regeneration via `/spec:tasks` before implementation starts.

## Approach

The architecture pivot (Angular + FastAPI + Neon PostgreSQL) narrows this feature's real design question
to two related things: how mistake records and their completeness are modeled relationally, and how
grouped-by-reason counts (FR-11, FR-12) get computed. The prior plan's core reasoning — read-time
computation over a flat record store, nothing denormalized — was explicitly storage-agnostic and is now
easier to execute, since Postgres is purpose-built for exactly this kind of filtered aggregate query.

**Approach A — One `mistakes` table; grouped counts via `GROUP BY` at read time (recommended).**
A single flat table holds every field FR-3 lists, plus `logged_at`. Grouped-by-reason counts (FR-11,
FR-12) and category drill-down (FR-13) are plain SQL: `SELECT reason_category, COUNT(*) FROM mistakes
WHERE logged_at BETWEEN :start AND :end GROUP BY reason_category ORDER BY COUNT(*) DESC`. Nothing about
"incomplete" or "count" is written anywhere except the source row itself.

**Approach B — Same table, plus a denormalized rollup table of per-period, per-category counts, updated
on every write.**
Adds a `mistake_reason_counts` table (period bucket, reason_category, count) maintained transactionally
alongside every insert. Recommended against: this reintroduces exactly the sync-drift risk the prior
(IndexedDB) plan deliberately avoided, for no real benefit — a personal mistake log realistically tops
out at a few thousand rows over the app's lifetime, and a `GROUP BY` over an indexed, date-filtered column
at that volume is effectively instant in Postgres. The only thing B buys is avoiding a `COUNT(*)` that
isn't expensive here, in exchange for a second table that must never drift from the first — a bad trade
for a solo-maintained project, and doubly so given Open Question 1 (how incomplete entries later get
edited) is still unresolved: any future edit path would have to remember to keep the rollup in sync too.

**Approach C — Normalize `reason_category` into its own lookup table** (`mistake_reason_categories`:
key, label), with `mistakes.reason_category` as a foreign key, counts still computed via `GROUP BY`/`JOIN`
at read time.
Rejected: the ADR already fixes the reason-category set as closed and out of scope to change (FR-4's nine
options; adding/removing/renaming is explicitly Out of Scope in the spec). A foreign-keyed lookup table
buys referential integrity and a place to store labels server-side — real benefits only if the set were
expected to grow or be admin-editable, which it isn't. A `CHECK`/application-level constraint against the
fixed nine keys (enforced in `schemas/mistake.py` via a `Literal`/enum type) gets the same safety without
an extra table, join, or migration to maintain for a set that will not change within this feature's scope.

**Recommendation: Approach A.** It matches the already-decided reasoning in
`docs/adr/2026-07-29-mistake-reason-category-enum-key.md` and the prior plan's Approach A, now backed by
a database built for exactly this query shape. No new ADR is written for this choice (see "ADR Decision"
below).

**Completeness is computed, never stored (requirement carried forward, non-negotiable in this plan).**
`is_incomplete` is derived at serialization time in `services/mistake.py` from the row's own current
values — `correct_answer IS NULL` or `reason_category == 'not_sure_other'` — and placed on the outbound
response schema. It is never written to a column, never cached, and is recomputed from live data on every
response. This is deliberate: Open Question 1 (how an incomplete entry later gets edited/completed) is
unresolved, and a computed value can never disagree with the row it describes regardless of how that
question is eventually answered — a stored flag could.

**Schema-level decisions this plan makes (distinct from the ADR, which only fixes the key representation,
not nullability or defaults):**
- `reason_category` is `NOT NULL` with a database default of `'not_sure_other'` rather than nullable —
  collapses "never chosen" and "explicitly not sure yet" into the same state, which is what FR-5 already
  treats as equivalent, and keeps the incompleteness check a two-branch expression instead of three.
- `correct_answer` is a single nullable text column, not a text column plus a separate "unknown" boolean.
  The wireframe's "I don't have the correct answer yet" checkbox and simply leaving the field blank have
  identical downstream meaning (FR-5, FR-7), so a second flag would only be able to disagree with the text
  content it describes — no information is lost by collapsing them.
- Primary key is a UUID (`gen_random_uuid()` default), consistent with a REST API not wanting to leak
  sequential row counts; a minor, easily-reversible implementation detail, not a forked decision.
- Per the single-learner simplification, `mistakes` has no `learner_id`/owner column — `require_learner`
  (owned by the access-protection epic's plan) gates the whole router instead.

### ADR Decision

No new ADR is written for the table/aggregation shape. The one real fork-in-the-road already has its ADR
(`2026-07-29-mistake-reason-category-enum-key.md` — string key vs. label vs. numeric id), and that
decision is unchanged by this pivot. The table-shape choice above (Approach A vs. B vs. C) is
straightforwardly reversible: adding a rollup table later is a purely additive migration that touches no
other epic's tables (no `learner_id`, no cross-epic foreign keys), and normalizing the category into a
lookup table later is likewise additive. Per the `implementation-planning` skill's own guidance, writing
an ADR for a trivially reversible choice adds process weight without benefit — this is recorded here, in
the plan, instead.

## File/Module Structure

### Backend (`backend/app/`) — imports `core/db.py` (`get_db`) and `core/security.py`
(`require_learner`), both owned by the access-protection epic's plan; not redefined here.

| Path | Responsibility | Implements (wireframe, if UI-facing) |
|---|---|---|
| `models/mistake.py` | SQLAlchemy `Mistake` ORM model: the `mistakes` table mapping only (columns, defaults, no query logic). | — (data model) |
| `schemas/mistake.py` | Pydantic request/response shapes: `MistakeCreate` (validates `reason_category` against the fixed 9-key set per the ADR), `MistakeRead` (includes the `is_incomplete` field populated by the service layer), `MistakeGroupedCategory`, `MistakeCategoryDetail`. | — (API contract) |
| `services/mistake.py` | Business logic only: create a mistake from validated input; list mistakes in a date range ordered by `logged_at` desc (FR-10); compute grouped counts via `GROUP BY` for a date range, sorted desc, all categories with count ≥ 1 included (FR-11, FR-12); fetch individual mistakes for one category + range (FR-13); the single `is_incomplete(row)` function used everywhere completeness is reported. | — (business logic) |
| `routers/mistake.py` | FastAPI router wiring `require_learner` + `get_db` to the service: `POST /api/mistakes`, `GET /api/mistakes?start&end`, `GET /api/mistakes/grouped?start&end`, `GET /api/mistakes/grouped/{reason_category}?start&end`. No business logic beyond request/response wiring. | — (API surface) |
| `alembic/versions/<rev>_create_mistakes_table.py` | This feature's own migration: creates the `mistakes` table with the columns/defaults/indexes above. | — (schema migration) |
| `tests/test_mistake_service.py` | Unit tests for `services/mistake.py`'s pure logic (`is_incomplete`, grouping, ordering) against a test DB session. | — (test) |
| `tests/test_mistake_router.py` | Integration tests for the four endpoints, including auth-gated access via `require_learner` and full round-trip persistence. | — (test) |

### Frontend (`src/app/mistakes/`) — imports `core/api/api-client.ts` (owned by the access-protection
epic's plan); internal shape mirrors `src/app/study-plan/` (`models/`, `data/`, `state/`, `pages/`).

| Path | Responsibility | Implements (wireframe, if UI-facing) |
|---|---|---|
| `models/mistake.model.ts` | `MistakeEntry` interface (matches `MistakeRead`, including `isIncomplete` as a field returned by the API, never computed client-side) and the fixed 9-key `ReasonCategory` union, per the ADR. | — (data model) |
| `models/review-period.model.ts` | `ReviewPeriod` type/options list (e.g. "this week") that the period selector renders from, rather than a hardcoded single literal. | — (data model) |
| `data/mistake.repository.ts` | Sole point of contact with `ApiClient` for this module: `create()`, `listChronological(range)`, `listGrouped(range)`, `getCategoryDetail(category, range)`. No business logic beyond the HTTP calls and response mapping. | — (data access) |
| `state/mistake-period.resolver.ts` | Pure function resolving a selected `ReviewPeriod` option into concrete `{start, end}` dates sent to the repository (FR-14). Isolated in its own file so Open Question 3 (rolling vs. calendar week) and Open Question 4 (custom ranges) are single-file changes later, and the backend API (which only ever sees `start`/`end`) never needs to change when they're resolved. | — (pure logic) |
| `state/mistake.facade.ts` | The only service the module's pages call into. Holds current view-mode, selected period, and loaded entries/grouped-results as signals; orchestrates repository calls and re-fetches on period/view-mode change (FR-15). | — (state) |
| `pages/log-entry-action/` | The contextual "Log Mistake" trigger embedded in a study/practice screen; reads current study-context state to pass inferable skill/source into the form (FR-1, FR-2). | `docs/ux/wireframes/mistake-logging-form.md` (entry-point note) |
| `pages/logging-form/` | The logging form screen: Sections A/B/C, "don't have correct answer yet" checkbox, reason single-select, Save/Close(X)/Cancel actions (FR-3, FR-4, FR-5, FR-6, FR-8, FR-9). | `docs/ux/wireframes/mistake-logging-form.md` |
| `pages/review-shell/` | The Mistake Review screen's shared chrome: header, period selector, List/Grouped view toggle; owns which view-mode and drill-down state (if any) is active and re-scopes on period change (FR-14, FR-15). | `docs/ux/wireframes/mistake-review.md` (shared chrome) |
| `pages/review-grouped/` | Renders the ranked reason-category list with counts for the current period, all categories with count ≥ 1 visible (FR-11, FR-12). | `docs/ux/wireframes/mistake-review.md` — Variant A |
| `pages/review-list/` | Renders the chronological list, most recent first, with date/skill/reason per row (FR-10). | `docs/ux/wireframes/mistake-review.md` — Variant B |
| `pages/review-category-detail/` | Renders the example list (own answer, correct answer or its absence, explanation) for one selected category (FR-13). | `docs/ux/wireframes/mistake-review.md` — Variant C |
| `mistakes.routes.ts` | Route definitions for the logging form and review shell. | — (routing) |

## Testing Strategy

Per constitution principle 2, every row below is a test written before its implementation exists.

| Requirement | Verified by |
|---|---|
| FR-1 | Frontend component test: `log-entry-action` renders and opens the logging form pre-tagged, tested against fixtures for each of the four skill contexts. |
| FR-2 | Frontend unit test: study-context → form-initial-values mapping puts inferable skill/source into the form while leaving them editable (no `readonly`/`disabled` on those fields). |
| FR-3 | Backend integration test: `POST /api/mistakes` with every documented field populated persists a row with all values (`test_mistake_router.py`); frontend component test: filling every field and saving calls `repository.create()` with the full payload. |
| FR-4 | Backend unit test: `MistakeCreate.reason_category` rejects any value outside the ADR's 9 keys; frontend unit test: the reason-category option list matches exactly the 9 fixed options, and a component test renders exactly those 9 as a single-select. |
| FR-5 | Backend integration test: `POST /api/mistakes` with `correct_answer` omitted and `reason_category` omitted (defaults to `not_sure_other`) returns 201; frontend component test: checking "don't have correct answer yet" and leaving reason unset allows Save with no validation error. |
| FR-6 | Backend integration test: `POST /api/mistakes` with only `skill` and `source` set returns 201 and the persisted row's `is_incomplete` is `true`; frontend component test: same minimal-field save path succeeds. |
| FR-7 | Backend unit test: `is_incomplete()` against a fixture matrix (missing correct answer / default reason / both / neither) in `test_mistake_service.py`; frontend component test: the retrievable list/review renders complete vs. incomplete entries distinctly, using the `isIncomplete` field the API returns (no client-side recomputation). |
| FR-8 | Frontend component test: triggering close `[X]` calls `repository.create()`/save with exactly the fields entered so far, not a fully validated shape. |
| FR-9 | Frontend component test: triggering "Cancel" makes no repository call for that draft — nothing is sent to the backend. |
| FR-10 | Backend integration test: `GET /api/mistakes?start&end` returns entries ordered by `logged_at` descending, scoped to the range; frontend component test: `review-list` renders date/skill/reason per row in that order. |
| FR-11 | Backend unit test: grouping logic in `services/mistake.py` produces correct per-category counts for a fixture set within a date range (`GROUP BY` correctness); frontend component test: `review-grouped` renders counts per category from the facade's signal. |
| FR-12 | Backend unit test: grouped results are ordered by count descending, and a fixture with a count-of-1 category asserts it is still present, not truncated to a top-N. |
| FR-13 | Backend integration test: `GET /api/mistakes/grouped/{reason_category}?start&end` returns exactly the individual mistakes behind that category/period, each with own answer, correct answer (or `null`), and explanation; frontend component test: `review-category-detail` renders that example list. |
| FR-14 | Frontend unit test: `mistake-period.resolver.ts` resolves a default period when no explicit selection has been made; frontend component test: `review-shell` opens with that default period selected and its data loaded. |
| FR-15 | Frontend component test: changing the period selector while either List or Grouped view is active triggers the facade to re-fetch and re-render that same view, with no separate reload action required. |
| FR-16 | Backend integration test: create a batch of complete and incomplete entries via `POST`, query them back via a fresh DB session/connection against the same Postgres instance, and confirm every row (complete and incomplete) is present — persistence is now Postgres's guarantee, verified end-to-end rather than against an in-memory fake. |

## Risks / Open Questions

- **[Spec Open Question 1 — unresolved, carried forward]** How an incomplete entry is later completed or
  edited (same logging form in an edit mode vs. a separate detail view) is not decided here, and per the
  spec's Out of Scope section is explicitly not this feature's concern yet. No update/PATCH endpoint is
  designed in this plan. The schema is deliberately shaped so either resolution slots in later without a
  migration: every field is independently nullable/updatable, and `is_incomplete` is computed live, so it
  is automatically correct the moment any future edit endpoint changes a row — nothing to reconcile.
- **[Spec Open Question 2 — unresolved, carried forward]** How an incomplete entry's missing fields should
  render in the grouped/list views (blank, visibly flagged, or excluded from counts) is not decided here.
  This plan's assumption for planning purposes only: an entry with a default (`not_sure_other`) reason is
  counted under that category's own bucket (it is itself one of the FR-4 fixed options, not a null state),
  and every API response carries `is_incomplete` so the eventual visual treatment is a frontend template
  change, not a data or query change. This does not foreclose a later decision to exclude incomplete
  entries from counts — that would be a one-line `WHERE` clause change in `services/mistake.py`.
- **Review-period decision (resolved 2026-07-29)**: "This week" is a fixed Monday-Sunday calendar
  week and is the default. The MVP exposes exactly "This week", "Last week", and "Last 30 days";
  arbitrary custom ranges remain out of scope. The calculation stays isolated in
  `state/mistake-period.resolver.ts`.
- **Parallel-epic dependency risk**: this plan assumes `backend/app/core/db.py` (`get_db`),
  `backend/app/core/security.py` (`require_learner`), and `src/app/core/api/api-client.ts` exist with the
  shapes described in the shared conventions. All three are being written by the access-protection epic's
  plan in parallel; if the landed shapes differ (e.g. a different `get_db` signature or client method
  names), only `routers/mistake.py` and `data/mistake.repository.ts` need adjustment — no other layer in
  this plan depends on their internals.
- **Alembic migration ordering**: multiple epics are each adding their own migration in parallel right
  now. This feature's `create_mistakes_table` migration will need its `down_revision` set against whatever
  the actual migration history looks like once merged, not assumed here — flagged so it isn't silently
  skipped at integration time.
- **"Log Mistake" host screens don't exist yet**: FR-1's four study/practice contexts (Reading, Listening,
  Writing, Speaking) are not part of this spec's wireframe set and aren't built yet. `pages/log-entry-action/`
  can be built and tested in isolation against fixture contexts, but wiring it into each real host screen
  depends on those screens' own implementation timing, outside this plan's control.
- **Data volume assumption**: Approach A assumes personal-scale data (realistically low thousands of rows
  over the app's lifetime). If that assumption is ever wrong, the mitigation is adding an index on
  `logged_at`/`reason_category` (already planned) or, only if truly needed later, revisiting Approach B —
  not a rewrite of the table shape.
- **`docs/specs/mistake-tracking/Tasks.md` is now stale** (written against the prior IndexedDB plan) and
  needs regeneration via `/spec:tasks` against this plan before implementation starts; not regenerated as
  part of this plan.

## Related ADRs
- `docs/adr/2026-07-29-mistake-reason-category-enum-key.md` (reason-category string-key representation —
  carried forward unchanged, now backed by a `mistakes.reason_category` column instead of an IndexedDB
  field)
- `docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md` (governing architecture this plan targets)
