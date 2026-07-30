# Tasks: Data Portability & Export
Plan: docs/specs/data-portability/ImplementationPlan.md

## Task-1 — Export-source registry mechanism
- [x] Status: Done
- Depends on: none (assumes `backend/app/core/db.py` already exists per the access-protection
  epic, for the `Session` type only — not otherwise used by this task)
- Goal: Build the `EXPORT_SOURCES` registry structure in `backend/app/services/data_portability.py`
  per the ADR's per-epic contract: a plain list of `Callable[[Session], dict]` entries that other
  epics' `export_learner_data()` functions get appended to. This task builds and tests the
  mechanism itself — entirely against fixture/fake `export_learner_data()`-shaped functions
  standing in for the seven other epics' not-yet-built implementations. No real epic module is
  imported here.
- Files touched: `backend/app/services/data_portability.py`,
  `backend/tests/services/test_data_portability_registry.py`
- Definition of done: tests pass proving (a) a fixture `export_learner_data(db)` function appended
  to `EXPORT_SOURCES` is present in the registry and callable, (b) two or more fixture functions
  can coexist in the registry independently (adding one doesn't disturb another's entry), and
  (c) the registry is iterable/inspectable by the merge step Task-2 depends on. This is
  foundational plumbing (per the ADR's Approach A contract) with no learner-facing behavior of its
  own yet, so it is not itself checkable against a specific FR — it exists so Task-2 can verify
  FR-1 and FR-2 against a real, populated registry instead of an ad hoc list.

## Task-2 — Merge/assembly into one versioned export document
- [x] Status: Done
- Depends on: Task-1
- Goal: Define the `ExportDocument` and `ExportFailure` Pydantic schemas per the ADR's envelope
  shape (`export_format_version` integer, `produced_at` timestamp, `categories` list, `data` dict
  keyed by category), and implement `assemble_export(db: Session) -> ExportDocument` in
  `backend/app/services/data_portability.py`: calls every function currently in `EXPORT_SOURCES`,
  merges each result under its own category key into one document, and populates the envelope
  fields. Still tested entirely against Task-1's fixture sources — no real epic data yet.
- Files touched: `backend/app/schemas/data_portability.py`,
  `backend/app/services/data_portability.py`,
  `backend/tests/services/test_data_portability_assembly.py`,
  `backend/tests/schemas/test_data_portability_schema.py`
- Definition of done: tests pass proving: `assemble_export()` run against two or more registered
  fixture sources returns one document whose `data` contains every fixture category, and whose
  `categories` list names exactly those categories (FR-1, mechanism-level — full real-data
  coverage is Task-7); `ExportDocument` requires `produced_at` and a completeness indicator
  (e.g. category count) as non-optional fields, and `export_format_version` serializes as a
  top-level integer per the ADR (schema-level half of FR-6 — the endpoint returning these values
  to a caller is verified in Task-5).

## Task-3 — Completeness verification (no silent drops)
- [x] Status: Done
- Depends on: Task-2
- Goal: Harden `assemble_export` so a registered source's output can never silently vanish from
  the merged document: assert every `EXPORT_SOURCES` entry is invoked exactly once and its result
  reaches the final `data` dict, and raise an explicit assembly error — never swallow or skip —
  when a registered function returns a malformed shape (missing category key, non-dict result, or
  a category name colliding with another registered source's).
- Files touched: `backend/app/services/data_portability.py`,
  `backend/tests/services/test_data_portability_completeness.py`
- Definition of done: tests pass proving: (1) a fixture source registered but whose result is
  deliberately made to not reach the merged document causes assembly to fail loudly rather than
  produce a shorter-than-expected export — the specific regression the guard exists to catch
  (FR-2, "none silently omitted"); (2) a fixture source returning a dict without the required
  category key raises an explicit assembly error instead of being silently dropped; (3) no
  parameter exists anywhere in `assemble_export`'s signature that could select a subset of
  registered sources or categories (FR-2, "no partial/selective export" — structural check,
  reconfirmed at the endpoint surface in Task-5).

## Task-4 — Access boundary: authenticated-only / own-data-only (FR-8, FR-9)
- [x] Status: Done
- Depends on: Task-2 (needs `assemble_export` to exist to assert its call signature); assumes
  `backend/app/core/security.py`'s `require_learner` dependency already exists per the
  access-protection epic — used directly here, not rebuilt or faked, since (unlike the other
  seven epics' models) it is a Task-1-equivalent prerequisite assumed to be real code by the time
  this task runs.
- Goal: Guarantee, at the service layer, that `assemble_export` can structurally never leak
  another identity's data — it accepts no caller-supplied learner/user-id parameter anywhere in
  its call path, consistent with the single-learner simplification the ADR and plan describe —
  and prove the `require_learner` auth-gating dependency this epic's router (Task-5) will use
  actually rejects unauthenticated callers, without yet building that router.
- Files touched: `backend/app/services/data_portability.py`,
  `backend/tests/services/test_data_portability_access_boundary.py`
- Definition of done: tests pass proving: `assemble_export`'s signature takes only a `Session`
  argument — no identity/learner-id parameter exists anywhere it could be supplied by a caller
  (FR-8, structural guarantee; re-verified against real multi-account data in Task-7); a minimal
  test route wrapped in `require_learner` rejects a request with no valid session cookie and
  admits one with a valid session issued by the real `require_learner`/session mechanism (FR-9).

## Task-5 — Export endpoint + confirmation response (FR-6) and failure handling (FR-7)
- [x] Status: Done
- Depends on: Task-3, Task-4
- Goal: Implement `POST /api/data-portability/export` in
  `backend/app/routers/data_portability.py`: gated by `require_learner` (Task-4), calls
  `assemble_export` (Task-2/Task-3), and returns the `ExportDocument` body directly in the same
  response (not a link or job id) with a `Content-Disposition` header for download; any exception
  raised during assembly is caught and mapped to a distinct `ExportFailure` response instead of an
  unhandled 500. Still tested against Task-1's fixture `EXPORT_SOURCES` entries.
- Files touched: `backend/app/routers/data_portability.py`,
  `backend/app/schemas/data_portability.py` (`ExportFailure`, if not already added in Task-2),
  `backend/tests/routers/test_data_portability_router.py`
- Definition of done: tests pass proving: a call with no valid session cookie returns 401 and no
  export document is produced (FR-9, endpoint-level); an authenticated call against fixture
  `EXPORT_SOURCES` returns 200 with every fixture category present, `produced_at` set, and a
  completeness indicator populated (FR-1, FR-6); the response `Content-Type` is `application/json`
  and the raw body round-trips through a plain `json.loads()` with no application-specific decoder
  (FR-3); the full document is returned inline in that same response, not a second step (FR-4);
  two consecutive authenticated calls in the same test both independently succeed with no
  rate-limit/cooldown triggered (FR-5); forcing one fixture export function to raise produces a
  distinct FR-7-shaped failure response — not a 200, not an unhandled 500 — and an immediate
  retried call succeeds with no leftover state from the failed attempt (FR-7); no query or body
  parameter accepted by the route can select a subset of categories (FR-2, endpoint-level
  confirmation of Task-3's guarantee).

## Task-6 — Frontend trigger + confirmation UI
- [x] Status: Done
- Depends on: Task-5
- Goal: Build the single "Export my data" screen against the real endpoint contract from Task-5:
  frontend types mirroring the backend schema, a repository as the sole point of contact with
  `api-client` for the export endpoint, and an `export.component` rendering the trigger action,
  the FR-6 success confirmation (timestamp plus an explicit completeness statement, distinct from
  a generic "Success" message), and the FR-7 failure message with an immediate retry control that
  carries no leftover state from the failed attempt. No wireframe exists yet for this screen (per
  the plan's note) — this is the minimal structure implied directly by FR-6/FR-7.
- Files touched: `src/app/data-portability/models/export-result.model.ts`,
  `src/app/data-portability/data/data-portability.repository.ts`,
  `src/app/data-portability/pages/export/export.component.ts` (+ template/spec),
  `src/app/data-portability/data-portability.routes.ts`
- Definition of done: tests pass proving: given a mocked successful repository response, the
  component renders the `produced_at` timestamp and a completeness statement visibly distinct
  from a generic success message (FR-6); given a mocked failure response, the component renders a
  message distinct from the success state and shows a retry control, and invoking retry re-calls
  the repository with no prior failure state carried over — no button stuck disabled, no partial
  data shown (FR-7); triggering export twice in a row (two mocked successful calls) both succeed
  with nothing in the UI blocking the second attempt (FR-5, UI-level); a repository unit test
  confirms it calls the export endpoint via `api-client` and returns either a typed confirmation or
  a typed failure, never an unhandled thrown error.

## Task-7 — Cross-epic integration: real `export_learner_data()` from every other epic
- [x] Status: Done — all real learner-data epics now register concrete exporters
- Depends on: Task-5 (this epic's own assembly/endpoint mechanism must be complete). Externally
  blocked on: study-plan-execution, vocabulary-review, mistake-tracking, progress-tracking,
  writing-coach, speaking-coach, and any other epic contributing an FR-1 category, each
  registering its real `export_learner_data()` in `EXPORT_SOURCES` per the ADR contract.
- Goal: Replace the fixture entries Tasks 1-5 tested against with the real registered functions
  from every other epic once they exist, and re-run the spec's own full acceptance criteria
  against real learner data: every FR-1 category present with real rows, FR-2 completeness holding
  with real sources, and FR-8's "never another learner's data" verified across at least two
  distinct learner accounts, exactly as the spec's acceptance criteria require.
  **Sequencing risk, stated explicitly:** this task cannot be started, let alone closed, until all
  seven other epics' models/services exist and each registers its own `export_learner_data()` —
  those epics are still being planned/built in parallel as of this writing, so this task's actual
  start date is unknown and outside this backlog's control. It must not be scheduled as if it
  follows Task-6 immediately, and it must not be marked done by re-running it against fixtures —
  that is what Tasks 1-5 already do and already pass.
- Files touched: `backend/app/services/data_portability.py` (adding each real epic's
  `export_learner_data` import to `EXPORT_SOURCES` — no other logic changes expected),
  `backend/tests/integration/test_data_portability_full_export.py`
- Definition of done: tests pass, seeded with real (non-fixture) data for two distinct learner
  accounts, proving: an export triggered as learner A contains every FR-1 category populated from
  real persisted tables and contains zero rows belonging to learner B, and the same holds in
  reverse for learner B (FR-8, full acceptance-criterion coverage — Task-4 only proved this
  structurally); every category named in FR-1 is present with actual persisted data, not a stub
  (FR-1, FR-2 — the full-coverage acceptance criterion left explicitly blocked by the
  Implementation Plan's Sequencing Dependency section, now closed).
