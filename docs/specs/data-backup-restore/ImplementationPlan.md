# Implementation Plan: Data Portability & Backup/Restore
Spec: docs/specs/data-backup-restore/Specification.md

## Approach

Three approaches were considered for how this feature is structured *within* the already-decided
client-only architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`,
`docs/architecture/Architecture.md`'s "Backup/Restore module" and "Local Data Layer"). All three
assume Angular + IndexedDB/LocalStorage as given; none reconsider that.

**Approach A — Flat, single-versioned payload; structural validation; recency re-derived from the
restored file's own timestamp (chosen).** One export produces one JSON file: a top-level
`schemaVersion` integer, a top-level `exportedAt` timestamp, and a `data` object holding all four
categories in full (FR-1/FR-2). Import validation is a pure function that parses the file, checks
`schemaVersion` is supported, and checks every required category/field is present with the right
shape — all before any confirmation UI is shown (FR-10/FR-11). The last-backup-recency record is
its own stored value (read by FR-6's indicator), written on every successful export (FR-4), and
**explicitly rewritten from the restored payload's own `exportedAt` as part of completing a
restore** — so it round-trips through the very file that recovers from a total local-data wipe.
This resolves the spec's open question; see `docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md`.

**Approach B — Per-category independent versioning.** Each of the four categories carries its own
`schemaVersion` inside one export envelope, allowing one category's shape to evolve without
bumping a global version. Rejected for now: all four categories are introduced together in V1 and
have no independent evolution need yet; this adds real validation and migration complexity (four
version-dispatch paths instead of one) for a solo project with no evidence it's needed. Revisit if
a future epic forces one category's shape to change independently of the others.

**Approach C — Payload plus embedded checksum/manifest for integrity verification.** Adds a hash
of the `data` block to detect corruption beyond structural mismatch. Rejected: JSON parse failure
and structural/shape validation already catch the realistic failure modes named in FR-10/FR-11
("complete, recognizable export... produced by this feature"); a checksum defends against subtle
bit-level corruption that a solo learner's own file-handling (moving a JSON file to a USB drive or
cloud folder) is unlikely to produce silently, and adds a moving part (hashing on export,
re-hashing on validate) with no FR asking for cryptographic integrity guarantees. Out of Scope
already excludes encryption/access-restriction, which this would sit adjacent to in spirit.

**Trade-offs of the chosen approach:** simplest to build and test correctly for the feature's
actual scope; the price is that any future schema change bumps one version number for the whole
file and any migration function must account for all four categories at once, and old
(`schemaVersion: 1`) files must be supported indefinitely since Out of Scope rules out retaining
in-app export history as a substitute.

## File/Module Structure
| Path | Responsibility | Implements (wireframe/prototype, if UI-facing) |
|------|-----------------|-----------------|
| src/app/features/backup-restore/backup-restore.page.ts (+.html) | Renders the Backup & Restore screen and switches between its Populated/Empty/Loading/Error/Export-Confirmation states; delegates all export/import/restore logic to the services below | docs/ux/wireframes/backup-restore.md |
| src/app/features/backup-restore/restore-confirmation.dialog.ts (+.html) | Renders the overwrite-warning confirmation dialog with equally weighted, non-default Confirm/Cancel actions | docs/ux/wireframes/backup-restore.md (Restore-Confirmation state) |
| src/app/features/backup-restore/export.service.ts | Orchestrates an export: requests all four categories from the Local Data Layer, wraps them in a versioned `BackupPayload`, triggers the file download, and on success only updates the last-backup record | (non-UI) |
| src/app/features/backup-restore/import-validator.service.ts | Pure validation: given raw file text, parses JSON and checks it is a complete, recognizable `BackupPayload` of a supported `schemaVersion`, returning either a validated payload or one specific rejection reason; has no side effects and never writes data | (non-UI) |
| src/app/features/backup-restore/restore.service.ts | Orchestrates a confirmed restore: given an already-validated payload, atomically overwrites all four categories via the Local Data Layer and rewrites the last-backup record from the payload's own `exportedAt` | (non-UI) |
| src/app/features/backup-restore/models/backup-payload.ts | Defines the versioned `BackupPayload` interface (`schemaVersion`, `exportedAt`, per-category shapes) shared by export, validator, and restore | (non-UI) |
| src/app/shell/backup-status.widget.ts (+.html) | Renders the dashboard's "Last backup: N days ago" / "No backup yet" indicator and its inline "Back Up Now" action, reading only the last-backup record | docs/ux/wireframes/dashboard-overview.md (Backup Status banner) |
| src/app/shell/dashboard-empty-state.component.ts (+.html) | Renders the post-data-loss empty dashboard state, distinguishing it from Loading/Error, with a direct "Restore from Backup" entry point into the Backup & Restore screen | docs/ux/wireframes/dashboard-overview.md (Empty state) |
| src/app/core/local-data-layer/local-data-layer.service.ts (extended) | Adds `exportAllCategories()` / `overwriteAllCategories()` methods so the Backup/Restore module never touches IndexedDB/LocalStorage directly; existing per-feature-module read/write methods unchanged | (non-UI) |
| src/app/core/local-data-layer/last-backup-record.store.ts | Owns reading/writing the single last-backup timestamp record; written by `export.service.ts` on success, rewritten by `restore.service.ts` from the restored payload's `exportedAt`, and read by `backup-status.widget.ts` | (non-UI) |

## Testing Strategy
| Requirement | Verified by |
|---|---|
| FR-1 | Unit test: `ExportService.export()` with fixture data across all four categories produces one `BackupPayload` containing every category, none omitted |
| FR-2 | Component test: `backup-restore.page` renders exactly one "Export All Data" action with no per-category/selective export controls |
| FR-3 | Component test: after a successful export, the page's Export-Confirmation state shows a specific filename, timestamp, and save-location text |
| FR-4 | Unit test: on `ExportService` success, `last-backup-record.store` is updated to the new export's timestamp immediately |
| FR-5 | Unit test: simulated export failure yields a failure state distinct from success, `last-backup-record.store` is left unchanged, and the export action remains immediately retriggerable |
| FR-6 | Component test: `backup-status.widget` renders on the dashboard shell itself (no navigation required), reading `last-backup-record.store` |
| FR-7 | Component test: clicking "Back Up Now" on `backup-status.widget` invokes `ExportService.export()` directly, without an intermediate navigation step |
| FR-8 | Unit test: with no last-backup record ever written, `backup-status.widget` renders "No backup yet", asserted distinct from any elapsed-time or blank rendering |
| FR-9 | Component test: `backup-restore.page`'s Import control invokes the file picker and passes the selected file into `import-validator.service` |
| FR-10 | Integration test: `backup-restore.page` never opens `restore-confirmation.dialog` except after `import-validator.service` has returned a validated payload — asserted via a spy that the dialog trigger path is unreachable before validation resolves |
| FR-11 | Unit test table: fixtures for malformed JSON, missing category, unsupported `schemaVersion`, and wrong per-category shape each produce a specific rejection reason from `import-validator.service`, and a corresponding component test confirms none of them ever reach `restore-confirmation.dialog` |
| FR-12 | Component test: given a validated payload, `backup-restore.page` opens `restore-confirmation.dialog` stating the overwrite warning |
| FR-13 | Component test: `restore-confirmation.dialog`'s Confirm action requires an explicit user click; asserted not to fire on dialog open, default focus, or Enter-key default submission |
| FR-14 | Component test: clicking Cancel closes the dialog, `RestoreService.restore()` is never invoked (spy assertion), and the page returns to its Populated state ready for retry |
| FR-15 | Unit test: `RestoreService.restore()` given a validated payload calls `overwriteAllCategories()` with all four categories present in the fixture payload, asserting none is partial or omitted |
| FR-16 | Integration test: after `RestoreService.restore()` completes, both `dashboard-empty-state`/dashboard populated view and at least one other module view (e.g. Vocabulary) reflect the restored data without further learner action |
| FR-17 | Component test: the dashboard shell renders `dashboard-empty-state` (not Loading/Error) when the Local Data Layer reports no data for any module, and that state exposes a "Restore from Backup" action navigating into `backup-restore.page` |
| Open Question resolution (post-restore recency correctness) | Unit test: given a validated payload with `exportedAt = X`, `RestoreService.restore()` causes `last-backup-record.store` to reflect "last backup at X" — never "no backup yet" — verifying the re-derivation decision in `docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md` |

All of the above are written test-first per Constitution principle 2 (tests before code) and the
`test-driven-development` skill: each service/component above gets its failing test(s) written
from this table before any implementation code is written, for every behavior change.

## Risks / Open Questions
- The spec's original open question (last-backup recency after a post-data-loss restore) is
  resolved by this plan via `docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md`
  — restore rewrites the last-backup record from the restored file's own `exportedAt`. This is a
  new planning-level decision, not a silent reinterpretation of the spec; flagging it here so it
  can be vetoed before implementation starts.
- Schema evolution beyond `schemaVersion: 1` is not designed in detail here — only the version
  field and the principle "unsupported version is a validation failure" are locked in. The actual
  migration mechanism (e.g., a per-version migration function chain) will need its own design
  when a V2 schema change is first needed; deferring this is a deliberate YAGNI call, not an
  oversight, but it is a real gap if a category's shape changes before that design exists.
- The prototype (`docs/ux/prototypes/data-backup-restore-flow.md`) itself flags three unresolved
  UX questions this plan does not resolve: (1) whether the Backup & Restore screen needs distinct
  copy when arrived at via the post-data-loss empty state versus a plain first-run "never backed
  up" case, (2) whether "Restore from Backup" on the dashboard empty state lands on the Backup &
  Restore screen first or jumps straight to the native file picker, and (3) whether an explicit
  import-validation-failure branch needs its own documented step in the prototype's happy path.
  This plan assumes, respectively: (1) no distinct copy variant in V1 — same Empty-state text
  either way; (2) the two-step version (land on screen, then click Import/Restore), matching the
  prototype's own stated assumption; (3) FR-11's rejection behavior is implemented regardless of
  whether the prototype's happy-path diagram shows it. These are implementation-level defaults,
  not UX sign-off — worth confirming with the prototype's owner before this ships.
- No automated test can fully substitute for a real device-loss rehearsal (clearing actual browser
  storage and restoring from a real exported file) — recommend at least one manual end-to-end dry
  run of the full export -> data-wipe -> restore cycle before considering this feature release-ready,
  since the integration tests above run against the same test harness's storage, not a genuinely
  fresh browser profile.

## Related ADRs
- docs/adr/2026-07-29-v1-no-backend-architecture.md
- docs/adr/2026-07-29-backup-payload-versioning-and-recency-derivation.md
