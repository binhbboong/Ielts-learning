# Tasks: Data Portability & Backup/Restore

> **Superseded — do not implement.** The server-side architecture replaced this IndexedDB
> backup/restore backlog. Its maintained successor is
> `docs/specs/data-portability/Tasks.md`, which is fully implemented.
Plan: docs/specs/data-backup-restore/ImplementationPlan.md
Spec: docs/specs/data-backup-restore/Specification.md
ADR: docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md

All tasks follow Constitution principle 2 (tests-first/TDD): for every task, write the failing
test(s) from the Definition of Done before writing any implementation code. "Definition of done"
below always means "the referenced tests exist, are green, and would fail if the behavior were
removed or implemented wrong" — never manual inspection.

## Task-1 — Define the versioned BackupPayload shape and serialization
- Status: Superseded — do not implement
- Depends on: none
- Goal: Define the `BackupPayload` model (`schemaVersion: 1`, `exportedAt` ISO timestamp, and a
  `data` object holding all four categories: `studyPlan`, `vocabulary`, `mistakes`,
  `practiceResults`) per the ADR, plus a pure `createBackupPayload(data)` function that stamps
  `schemaVersion` and `exportedAt` and embeds the four categories unchanged. This is the shared
  contract every other task in this backlog is built on (export, validation, and restore all
  read/write this exact shape).
  **Cross-feature dependency risk:** this task assumes the Study Plan, Vocabulary, Mistake
  Notebook, and Practice & Progress feature modules already have stable data models to serialize
  into `data.studyPlan` / `data.vocabulary` / `data.mistakes` / `data.practiceResults`. If any of
  those models is still in flux when this task starts, either stub a minimal fixture shape and
  revisit before Task-2, or block this task until the owning feature's model is stable — do not
  silently assume they are ready.
- Files touched: src/app/features/backup-restore/models/backup-payload.ts
- Definition of done: unit tests pass proving `createBackupPayload()` given fixture data for all
  four categories returns an object with `schemaVersion === 1`, a valid `exportedAt` timestamp,
  and a `data` object containing all four categories with none omitted or altered. Supports
  FR-1, FR-2 (full verification of those FRs happens end-to-end in Task-4).

## Task-2 — Local Data Layer: read all categories for export
- Status: Superseded — do not implement
- Depends on: Task-1
- Goal: Add `exportAllCategories()` to the Local Data Layer service, returning the current
  on-device contents of all four categories in the shape `BackupPayload.data` expects, without
  mutating anything.
  **Cross-feature dependency risk:** requires each feature module's existing read method
  (study plan, vocabulary, mistakes, practice results) to be callable and stable; flag and block
  on any module whose read path isn't ready rather than stubbing silently.
- Files touched: src/app/core/local-data-layer/local-data-layer.service.ts
- Definition of done: unit test pass proving `exportAllCategories()` called against fixture
  storage returns all four categories matching the fixtures exactly, with no category missing or
  transformed. Supports FR-1 (full verification in Task-4).

## Task-3 — Last-backup-record store
- Status: Superseded — do not implement
- Depends on: none
- Goal: Implement `last-backup-record.store.ts`: a small Local Data Layer entry that stores one
  timestamp, with a read API that distinctly reports "no value ever written" versus "a timestamp
  value," and a write API that overwrites the stored value.
- Files touched: src/app/core/local-data-layer/last-backup-record.store.ts
- Definition of done: unit tests pass proving (a) reading before any write returns the distinct
  "no value" result, (b) writing a timestamp then reading returns exactly that timestamp, and
  (c) a second write overwrites the first. Supports FR-4, FR-8 (full behavioral verification in
  Task-4 and Task-6).

## Task-4 — Export action, success confirmation, and last-backup-record update
- Status: Superseded — do not implement
- Depends on: Task-1, Task-2, Task-3
- Goal: Implement `ExportService.export()`: gather all four categories via
  `exportAllCategories()`, build a `BackupPayload` via `createBackupPayload()`, trigger the file
  download, and — only on success — update `last-backup-record.store` to the new export's
  timestamp. Implement the `backup-restore.page`'s Export-Confirmation state, which must show a
  specific filename/timestamp and save-location text (not a generic success message), and must
  expose exactly one "Export All Data" action with no per-category/selective export controls.
- Files touched: src/app/features/backup-restore/export.service.ts,
  src/app/features/backup-restore/backup-restore.page.ts (+.html)
- Definition of done: tests pass proving (1) `export()` with fixture data across all four
  categories produces one payload containing every category (FR-1); (2) the page renders exactly
  one export action with no selective/partial export UI (FR-2); (3) after a successful export the
  page shows a specific, distinguishable filename/timestamp and save-location text (FR-3); (4) on
  success, `last-backup-record.store` is updated to the new export's timestamp immediately (FR-4).

## Task-5 — Export-failure handling
- Status: Superseded — do not implement
- Depends on: Task-4
- Goal: Handle a failed export attempt in `ExportService`/`backup-restore.page`: show a failure
  message visibly distinct from the success confirmation, leave `last-backup-record.store`
  completely unchanged, and leave the export action immediately retriggerable with no extra step.
- Files touched: src/app/features/backup-restore/export.service.ts,
  src/app/features/backup-restore/backup-restore.page.ts (+.html)
- Definition of done: unit/component test passes proving a simulated export failure (a) renders a
  failure state distinct from the success state, (b) leaves `last-backup-record.store` at its
  prior value (verified against a pre-set fixture value), and (c) the export action can be
  retriggered immediately without navigation or reset. Covers FR-5.

## Task-6 — Dashboard backup-status indicator
- Status: Superseded — do not implement
- Depends on: Task-3, Task-4
- Goal: Implement `backup-status.widget` on the dashboard shell: renders last-backup recency
  read from `last-backup-record.store` directly on the main landing view (no navigation
  required), renders a distinct "No backup yet" state when the store has no value, and exposes a
  "Back Up Now" action that invokes `ExportService.export()` directly.
- Files touched: src/app/shell/backup-status.widget.ts (+.html)
- Definition of done: component tests pass proving (1) the widget renders on the dashboard shell
  itself without navigating into a dedicated area, reading `last-backup-record.store` (FR-6); (2)
  clicking "Back Up Now" invokes `ExportService.export()` directly with no intermediate
  navigation (FR-7); (3) with no last-backup record ever written, the widget renders "No backup
  yet," asserted as a distinct render path from any elapsed-time or blank output (FR-8).

## Task-7 — Import file validation (must precede any overwrite confirmation)
- Status: Superseded — do not implement
- Depends on: Task-1
- Goal: Implement `import-validator.service.ts` as a pure function: given raw file text, parse
  JSON and check it is a complete, recognizable `BackupPayload` of a supported `schemaVersion`
  (all four categories present with correct shape), returning either a validated payload or one
  specific rejection reason. No side effects; never writes data. Wire `backup-restore.page`'s
  Import control to invoke the file picker and pass the selected file into this validator, and to
  render a clear, specific rejection message on failure. This is one of the feature's two
  highest-risk behaviors (per the plan): a bad file must never reach the overwrite-confirmation
  step under any circumstance.
- Files touched: src/app/features/backup-restore/import-validator.service.ts,
  src/app/features/backup-restore/backup-restore.page.ts (+.html)
- Definition of done: tests pass proving (1) selecting a file invokes the file picker and passes
  the selected file into `import-validator.service` (FR-9); (2) a table of fixtures — malformed
  JSON, missing category, unsupported `schemaVersion`, wrong per-category shape — each produce a
  specific rejection reason and are asserted, via a spy/instrumentation on the
  overwrite-confirmation trigger path, to never reach it (test must fail if any fixture reaches
  the confirmation step) (FR-11); (3) an integration test asserts the confirmation-dialog trigger
  path is unreachable at any point before `import-validator.service` has resolved, for both valid
  and invalid fixtures (FR-10).

## Task-8 — Overwrite confirmation and cancel
- Status: Superseded — do not implement
- Depends on: Task-7
- Goal: Implement `restore-confirmation.dialog`: once (and only once) a selected file has passed
  validation, present an explicit confirmation stating plainly that proceeding will overwrite all
  existing device data. The Confirm action must require a deliberate click (never fire on open,
  default focus, or Enter-key default submission). The Cancel action must be equally clear and
  easy to take, and must leave all existing data completely unchanged, returning the learner to a
  retry-ready state.
- Files touched: src/app/features/backup-restore/restore-confirmation.dialog.ts (+.html)
- Definition of done: component tests pass proving (1) given a validated payload, the dialog opens
  and states the overwrite warning (FR-12); (2) the Confirm action does not fire on dialog open,
  default focus, or Enter-key default submission, and only fires on an explicit click (FR-13); (3)
  clicking Cancel closes the dialog, asserts (via spy) that no restore/overwrite call is ever
  invoked, and leaves the page in a state ready to retry the restore (FR-14).

## Task-9 — Restore-and-replace operation
- Status: Superseded — do not implement
- Depends on: Task-1, Task-8
- Goal: Add `overwriteAllCategories()` to the Local Data Layer service and implement
  `RestoreService.restore()`: given an already-validated payload (post-confirmation only),
  atomically overwrite all four data categories via `overwriteAllCategories()`, with no partial
  or silent restore of only some categories.
- Files touched: src/app/features/backup-restore/restore.service.ts,
  src/app/core/local-data-layer/local-data-layer.service.ts
- Definition of done: unit test passes proving `RestoreService.restore()` given a validated
  fixture payload results in `overwriteAllCategories()` being called with all four categories
  present and unaltered, and that on-device storage subsequently matches the fixture payload's
  `data` exactly for all four categories, none partial or omitted. Covers FR-15.

## Task-10 — Post-restore recency re-derivation from the restored file's own exportedAt
- Status: Superseded — do not implement
- Depends on: Task-3, Task-9
- Goal: Resolve the ADR's specific fix for the spec's previously open question. Extend
  `RestoreService.restore()` so that, as part of completing a restore, it explicitly rewrites
  `last-backup-record.store` from the restored payload's own `exportedAt` — never leaving it
  untouched, blank, or requiring a separate step. This is the feature's other highest-risk
  behavior (per the plan/ADR) and gets its own dedicated test distinct from Task-9's data-overwrite
  test.
- Files touched: src/app/features/backup-restore/restore.service.ts,
  src/app/core/local-data-layer/last-backup-record.store.ts
- Definition of done: unit test passes proving that given a validated payload with
  `exportedAt = X`, after `RestoreService.restore()` completes, `last-backup-record.store` reads
  back exactly `X` — and a companion component test proves `backup-status.widget` (Task-6),
  read immediately after this restore, renders "last backup: <age of X>" and never "No backup
  yet." The test must be written so it fails if the re-derivation step is skipped or the record is
  left at its pre-restore (wiped/absent) value. Resolves the Open Question in
  docs/specs/data-backup-restore/Specification.md and verifies the decision recorded in
  docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md.

## Task-11 — Post-restore reflection across learner-facing views
- Status: Superseded — do not implement
- Depends on: Task-9, Task-10
- Goal: Ensure that immediately after `RestoreService.restore()` completes, the learner's normal
  views — at minimum the main dashboard and at least one other data-bearing module view (e.g.
  Vocabulary) — reflect the restored data without any further learner action (e.g., manual
  refresh or navigation). This task covers the read side (views reacting to the Local Data
  Layer's new contents); it does not re-touch restore's write logic from Task-9/Task-10.
- Files touched: src/app/shell/ (dashboard views), relevant existing feature module view
  components (read-only wiring, no new write logic)
- Definition of done: integration test passes proving that after `RestoreService.restore()`
  completes with a fixture payload, both the dashboard view and at least one other module view
  (e.g. Vocabulary) display data matching the restored payload without any additional learner
  action or manual refresh. Covers FR-16.

## Task-12 — Post-data-loss empty state with direct restore path
- Status: Superseded — do not implement
- Depends on: Task-2, Task-8
- Goal: Implement `dashboard-empty-state.component`: when the Local Data Layer reports no data for
  any module (i.e., a real data-loss event, not a Loading or Error condition), render a distinct,
  expected empty state — never an unexplained blank screen or an error — with a direct
  "Restore from Backup" action that navigates into `backup-restore.page`.
- Files touched: src/app/shell/dashboard-empty-state.component.ts (+.html)
- Definition of done: component test passes proving (1) when the Local Data Layer reports no data
  for any module, the dashboard shell renders `dashboard-empty-state`, distinctly from its
  Loading and Error states; (2) that state exposes a "Restore from Backup" action which, when
  activated, navigates into `backup-restore.page`. Covers FR-17.
