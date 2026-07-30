# Implementation Plan: Data Portability & Export
Spec: docs/specs/data-portability/Specification.md

## Sequencing Dependency (read first)

This epic's export is only as complete as the set of tables that exist to read from. Every
other epic (study-plan-execution, vocabulary-review, mistake-tracking, progress-tracking, and
the future writing/speaking submission epics) owns its own SQLAlchemy models, and those models
do not exist in code yet — they are being planned in parallel right now. This plan can be
written and its skeleton built today (the export endpoint, the aggregation service, the
envelope/confirmation shape, the auth gate, the failure/retry path), but **the aggregation step
that actually walks every epic's data cannot be finished, and FR-1/FR-2/FR-8 cannot be fully
verified, until every other epic's models and migrations exist.** Treat "add this epic's
`export_learner_data()` to the aggregator" as a follow-up task each other epic's implementation
must complete as part of landing its own models (see Approach A below) — not something this
epic's own backlog can close alone. `/spec:tasks` for this epic should mark the
full-coverage acceptance criterion as blocked-on (not merely "todo") the other seven epics'
model code landing.

## Approach

The question this plan has to answer is architectural, not just "which endpoint": **how does one
export assemble data that is owned by seven other epics' own modules, without this epic having
to be rewritten every time another epic's schema changes?**

**Approach A — Per-epic `export_learner_data()` contract, this epic aggregates (recommended).**
Every epic's `backend/app/services/<epic>.py` exposes one function with a fixed signature —
`export_learner_data(db: Session) -> dict` (no learner-id parameter needed per the
single-learner simplification; it simply returns all of that epic's rows in whatever plain,
JSON-serializable shape that epic's own author considers a faithful, self-readable
representation of its data) and one required field on that dict's shape: a hardcoded
`category` key naming which of the FR-1 export categories it fills. This epic's
`backend/app/services/data_portability.py` holds a **registry** — a plain list of the known
epic export functions, imported and appended to as each epic's module lands
(`EXPORT_SOURCES: list[Callable[[Session], dict]] = [study_plan.export_learner_data,
vocabulary.export_learner_data, ...]`). The export service calls every function in the
registry, merges the results into one document keyed by category, wraps it in the envelope
(FR-6's metadata), and returns/serializes it. Each epic owns the *shape* of its own exported
data; this epic owns only assembly, the envelope, and the delivery mechanism.

**Approach B — This epic queries every other epic's models directly.** The export service
imports every other epic's SQLAlchemy model classes itself and writes its own `SELECT *`-style
query plus its own serialization logic for each one, all inside this epic's own module.
Centralizes all export logic in one place (easy to read the whole export in one file today),
but couples this epic's code to the exact column names and relationships of every other epic's
schema. Every time another epic adds a column, renames a field, or introduces a new related
table, this epic's code silently goes stale (a column added elsewhere is invisible here unless
someone remembers to update this epic too) — which directly risks FR-2 ("no category silently
omitted") the moment any other epic evolves after this one ships. Given seven other epics are
mid-design right now and will keep changing, this coupling is a real, near-term maintenance
cost, not a theoretical one.

**Approach C — Generic schema-introspection (walk all registered SQLAlchemy models
automatically via `Base.registry` / `Base.metadata.tables`).** Requires no per-epic code at
all — every model ever registered on the shared `Base` gets dumped automatically. Attractive for
FR-2 (structurally impossible to "forget" a table), but it exports raw table/column shapes,
not a shape any epic has reviewed as "the readable representation of my data" (FR-3's
self-readability bar). It also has no way to distinguish learner-facing data from any future
internal/system table (e.g., a migrations-bookkeeping table, or a future non-exportable
operational table) without yet another per-model opt-in/opt-out flag — which reintroduces a
per-epic contract anyway, just an implicit one instead of an explicit function. It also
produces awkward key naming (raw table names) instead of the FR-1 category names the spec
actually names.

**Recommendation: Approach A.** It keeps "what does my data look like when exported"
co-located with the epic that owns and best understands that data's shape and meaning
(consistent with every other per-epic layering convention already used across this codebase —
each epic owns its own `models/services/schemas/routers`). The trade-off, stated plainly: A
requires every other epic's plan/implementation to remember to add and maintain its
`export_learner_data()` function and register it — a coordination cost B and C avoid. This plan
accepts that cost deliberately: it is the same "own your own layer" discipline already used for
everything else in this codebase, it keeps this epic's own code simple and stable regardless of
how other epics' schemas evolve, and the coordination point (the registry list) is a single,
highly visible line per epic — easy to code-review, unlike B's silent-staleness failure mode.
This plan's own testing strategy (below) includes a check that fails loudly if an epic's
function is missing from the registry or returns something outside the expected shape, so the
coordination cost is caught by CI, not discovered by a learner's incomplete export.

## Open Questions — Resolved

**Import/restore: out of scope for this version (export-only).** The PRD's Epic-5 scope
statement is "export... at any time... a complement to durable server-side storage" — it never
says "and load it back in." Vision goal G-5's "get their data back" is satisfied by the learner
holding a complete, self-readable file; nothing in the PRD or Vision requires this application
(or any successor) to be able to re-ingest that file. The old superseded `data-backup-restore`
spec's restore capability existed to recover from *local browser data loss* — a premise that no
longer applies now that Neon Postgres, not the browser, is the system of record (this is exactly
the staleness the fullstack-vercel-claude-architecture ADR already flagged for that old ADR).
Building import speculatively now would mean designing and maintaining an ingestion path with no
current consumer and no confirmed future requirement. If a real need appears later (e.g., a
self-hosted successor app that needs to import this export format), that becomes its own future
epic with its own spec — this plan does not preclude it, the export format is plain, versioned
JSON (see ADR) precisely so a future importer would have something predictable to parse.

**AI-portability: including full AI feedback content as exported data is sufficient.** The
learner's goal per the spec's user scenarios is a "permanent readable record of what they were
told" — scores, strengths, weaknesses, corrections — not the ability to resubmit that content for
re-evaluation by a different AI provider. Nothing in FR-1 through FR-9 or the Vision's G-5
success criterion asks for the export to be re-interpretable *as input* to another AI system;
G-5's concern is not losing access to feedback already given if the AI provider changes, which
plain exported text fully satisfies. Structuring the export so a different AI provider could
programmatically resume grading from it would be speculative scope with no named consumer.

## File/Module Structure

No UI-facing wireframe exists yet for this epic under the new architecture (the old
`data-backup-restore-flow.md` prototype was built for the superseded IndexedDB/restore premise
per the spec's header note and must not be assumed correct here) — the single Angular page below
is planned from FR-1/FR-6/FR-7 directly and should be treated as provisional until a wireframe
is produced; it is deliberately the simplest possible screen (one button, one status region) so
that gap is low-risk.

| Path | Responsibility |
|------|-----------------|
| `backend/app/services/data_portability.py` | Holds `EXPORT_SOURCES` (the registry of every epic's `export_learner_data()` function) and `assemble_export(db) -> ExportDocument`, which calls each source, merges results by category, and builds the envelope (export id, produced-at timestamp, format version, category list). |
| `backend/app/schemas/data_portability.py` | Defines the `ExportDocument` Pydantic response shape (envelope fields + one key per FR-1 category) and the `ExportFailure` error shape (FR-7). |
| `backend/app/routers/data_portability.py` | Exposes `POST /api/data-portability/export`, depends on `require_learner` (FR-9), calls `assemble_export`, returns the document as a downloadable JSON file with a `Content-Disposition` header; maps any assembly exception to the FR-7 failure response instead of a raw 500. |
| `backend/app/services/<epic>.py` (one `export_learner_data()` function added to each of the other seven epics' own existing service module, owned by each epic's own plan/PR, not by this file) | Returns that epic's own rows as a plain JSON-serializable dict tagged with its FR-1 category name — the contract this epic's registry depends on. Listed here for traceability only; implementation belongs to each owning epic. |
| `src/app/core/api/api-client.ts` (existing, shared — no change expected beyond a generic POST/download helper if one doesn't already exist) | Used as-is to call the export endpoint and trigger a browser download of the response body. |
| `src/app/data-portability/models/export-result.model.ts` | Defines the frontend `ExportConfirmation`/`ExportFailure` types mirrored from the backend schema — types only, no logic. |
| `src/app/data-portability/data/data-portability.repository.ts` | Sole point of contact with `api-client` for this module: calls the export endpoint and returns either a downloadable blob + confirmation metadata, or a typed failure. |
| `src/app/data-portability/pages/export/export.component.ts` | Renders the single "Export my data" action, the FR-6 success confirmation (timestamp + completeness statement) or FR-7 failure message with an immediate retry control. No wireframe exists yet (see note above) — this is the minimal structure implied directly by FR-6/FR-7, to be reconciled with a wireframe if/when one is produced. |
| `src/app/data-portability/data-portability.routes.ts` | Declares this module's single route for mounting into the App Shell nav. |

## Testing Strategy

Every row is written test-first per constitution principle 2: the failing test is written from
the FR before the corresponding code exists. Rows marked "(blocked)" cannot be made to pass for
real until the dependent epic's model/service code exists per the Sequencing Dependency above;
until then they are written against a stub `export_learner_data()` fixture so the test itself
(and the aggregation contract it verifies) exists ahead of the dependency landing.

| Requirement | Verified by |
|---|---|
| FR-1 (single action, all data categories covered) | `data_portability.py` router test: calling the endpoint with a registry of stub `export_learner_data()` functions (one per FR-1 category) asserts the response contains every category key. Full real-data version (blocked) re-runs once every epic's real function is registered. |
| FR-2 (no partial/selective export; nothing silently omitted) | `assemble_export` unit test: asserts every function currently in `EXPORT_SOURCES` is called exactly once and its result appears in the output — a registry entry that is present but whose result goes missing from the merged document fails the test. A second test asserts the router exposes no query/body parameter that could select a subset of categories. |
| FR-3 (self-readable, generally-available-tools format) | Contract test: assert the response `Content-Type` is `application/json` (or the chosen format, see ADR) and that `json.loads()` (or equivalent) round-trips the raw response body without any application-specific decoder. |
| FR-4 (immediately available to keep, no further action) | Router test: asserts a single successful call returns the full document body in that same response (not a link, a job id, or a "check back later" pattern requiring a second step). |
| FR-5 (on demand, any time, no frequency limit) | Router test: two consecutive export calls in the same test both succeed with 200 and independently-correct bodies; asserts no rate-limit/cooldown logic exists in the route. |
| FR-6 (success confirmation states when + complete) | Schema test on `ExportDocument`: asserts `produced_at` (timestamp) and a completeness indicator (e.g., category count matching `EXPORT_SOURCES` length) are required, non-optional fields. Frontend `export.component` test: renders the timestamp and a "complete" statement distinct from a generic "Success" string. |
| FR-7 (distinct failure message, retry with no data loss) | Router test: forcing one registered export function to raise produces a distinct FR-7-shaped error response, not a 200 and not an unhandled 500. Frontend `export.component` test: on a failure response, a retry control is shown and invoking it re-calls the endpoint with no prior state carried over (no partial file, no disabled button). |
| FR-8 (never another learner's data) | Given the single-learner simplification, there structurally is no other learner's data in the database — verified by a repository-level test asserting `assemble_export` issues no query filtered by or parameterized on any caller-supplied identity, and by an integration test asserting the endpoint takes no learner-identifying input from the request at all (identity comes only from the `require_learner` session, never from a request field). |
| FR-9 (reject unauthenticated export requests) | Router test: calling the endpoint without a valid session (whatever `require_learner` enforces) returns 401/403 and produces no export document. |

## Constitution Check

- **Tests-first (principle 2):** every row above is a test written before its implementation;
  no exception requested.
- **Small, reviewable units (principle 4):** the registry pattern in Approach A lets each other
  epic land its `export_learner_data()` addition as its own small, independently reviewable
  change rather than one large cross-epic PR.
- **Docs are durable (principle 6):** this plan and its ADR (below) are the source of truth for
  the export contract every other epic must implement against; `/spec:tasks` for those other
  epics should reference `data_portability.export_learner_data` as a named follow-up, not
  silently duplicate the shape decision.
- **Upstream docs are the contract (principle 1):** if any FR here is later found to conflict
  with `Architecture.md`'s "Data Export module" description, `Architecture.md` is the upstream
  document and must be reconciled, not silently diverged from — no such conflict was found during
  this planning pass.

## ADR

The export **file format/shape** (versioned vs. unversioned, one document vs. several, the
per-category contract every other epic must satisfy) is a costly-to-reverse data-shape decision
per the implementation-planning skill's trigger: learners may hold onto old export files for
years, other epics' code will be written against the `export_learner_data()` contract, and a
future importer (if one is ever built) would need to parse whatever is decided now. This
warrants an ADR — see
`docs/adr/2026-07-29-data-portability-export-contract.md`.
