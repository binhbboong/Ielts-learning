# Specification: Data Portability & Backup/Restore

> **Superseded.** This spec's premise (no server-side copy exists, so manual export/import is the learner's only safety net against total data loss) assumed the client-only, IndexedDB-based architecture. That architecture was superseded by `docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`, which puts the learner's data in a server-side Postgres database as the system of record. See the successor spec: `docs/specs/data-portability/Specification.md` (PRD Epic-5, "Data Portability & Export"). Kept here for history — do not implement against this version.

Related UX: docs/ux/prototypes/data-backup-restore-flow.md

## Status
Draft

## Overview
This feature is the learner's entire durability and portability guarantee for a tool that
keeps no server-side copy of their data (per the accepted client-only architecture decision).
It lets the solo learner, at any time they choose, produce one complete export of everything
they've built up over the 180-day plan — study plan/task history, vocabulary, mistake log, and
practice results — and later restore that same data into the app after any event that wipes
their device's local data, with a verifiable, zero-loss result. Without it, choosing a
no-backend tool for full data ownership would carry an unacceptable risk of silent, permanent
loss; this feature is what makes that trade-off safe.

The feature covers three connected capabilities: exporting all learner data in a single
deliberate action with concrete proof the export is real and current; keeping the learner
aware, from their main landing view, of how long it has been since that proof was last
produced; and restoring from a previously exported file, with the selected file validated for
correctness before the learner is ever asked to confirm an overwrite, and a clear, low-anxiety
way to back out of that overwrite if they hesitate. It also covers the moment a real data-loss
event is discovered — the app must present that moment as a recoverable, expected state, not
an unexplained blank slate.

## User Scenarios
- As a solo IELTS learner, I want to export the entirety of my learning data in a single
  action, so that I always have one complete, current backup and never have to track which
  parts of my data are or aren't covered.
- As a solo IELTS learner, I want concrete proof that an export succeeded — something
  identifiable and specific, not just a generic success message — so that I can actually trust
  the backup exists rather than hoping it worked.
- As a solo IELTS learner, I want to see, right from my main landing view, how long it's been
  since my last backup, so that I'm reminded before neglect turns into real risk.
- As a solo IELTS learner, I want a file I try to restore to be checked and rejected upfront if
  it's invalid or corrupted, before I'm ever asked to confirm anything, so that a bad file can
  never trick me into approving an overwrite I wouldn't have wanted.
- As a solo IELTS learner, I want to be clearly warned that restoring will overwrite my
  existing data, with an equally easy way to cancel, so that I can proceed deliberately or back
  out safely without any fear of an accidental, irreversible mistake.
- As a solo IELTS learner, I want the restored data to visibly and immediately show up as my
  real study plan, vocabulary, mistakes, and practice results, so that I have tangible proof the
  whole export-and-restore cycle actually worked and nothing was lost.
- As a solo IELTS learner, I want a clear way back to restoring my data if I open the app and
  find it empty after a real data-loss event, so that I know right away this is recoverable and
  not a permanent loss.

## Functional Requirements

### Exporting learner data
- FR-1: The system MUST let the learner initiate a single action that produces one complete
  export covering all of the learner's data: study plan/task history, vocabulary, mistake log,
  and practice results.
- FR-2: The system MUST NOT offer any partial, selective, or category-by-category export —
  every export produced by this feature MUST include all data categories named in FR-1 in
  full.
- FR-3: Upon a successful export, the system MUST present confirmation that identifies the
  export with a specific, distinguishable name or timestamp and states where it was saved, so
  the learner has concrete, verifiable evidence the backup exists and is current — not a
  generic success message alone.
- FR-4: Upon a successful export, the system MUST immediately update the learner-visible record
  of when the last backup occurred to reflect that export.
- FR-5: If an export attempt does not complete successfully, the system MUST present a failure
  message distinct from the success confirmation, MUST leave the previously recorded last-backup
  information unchanged, and MUST let the learner retry the export without any extra step.

### Backup awareness
- FR-6: The system MUST show an indicator of how long it has been since the last successful
  export directly on the learner's main landing view, visible without navigating into any
  dedicated export/restore area.
- FR-7: The main landing view's backup indicator MUST provide a direct action that starts an
  export from that view, without first requiring navigation elsewhere.
- FR-8: Before any export has ever been produced on a given device, the system MUST state that
  no backup exists yet, distinctly from stating any specific elapsed time.

### Restoring learner data
- FR-9: The system MUST let the learner select a previously exported file to restore from.
- FR-10: The system MUST validate a selected file before presenting any overwrite confirmation
  to the learner. Validation MUST confirm the file is a complete, recognizable export produced
  by this feature.
- FR-11: If a selected file fails validation, the system MUST reject it with a clear, specific
  message explaining that it could not be used, and MUST NOT proceed to the overwrite
  confirmation step under any circumstance.
- FR-12: Only once a selected file has passed validation, the system MUST present an explicit
  confirmation step stating plainly that proceeding will overwrite all data currently on the
  device.
- FR-13: The confirmation step MUST require a deliberate, explicit confirming action from the
  learner before any overwrite occurs; it MUST NOT be triggered automatically, by a default
  action, or by an action that is easy to select accidentally.
- FR-14: The confirmation step MUST offer a cancel action that is equally clear and equally
  easy to take as confirming, and choosing it MUST leave all existing data completely
  unchanged, returning the learner to a state where they can retry the restore later.
- FR-15: Upon explicit confirmation, the system MUST replace the device's existing data with
  the complete contents of the validated file, covering every data category named in FR-1, with
  no partial or silent restore of only some of it.
- FR-16: Immediately after a restore completes, the system MUST reflect the restored data
  across the learner's normal views (at minimum the main landing view) as directly observable
  proof that the restore succeeded, without requiring the learner to take any further action.

### Recovering from data loss
- FR-17: When the learner opens the app and no learner data is found on the device, the system
  MUST present this as a distinct, expected state — not an unexplained blank screen or an error
  — and MUST provide a direct path from that state into the restore action described above.

## Out of Scope
- Encrypting, password-protecting, or otherwise restricting access to the exported data.
- Automatic, scheduled, or background backups of any kind — every export is a deliberate,
  learner-initiated action, never one the system performs on its own.
- Uploading, transmitting, or storing the exported data anywhere off the learner's own device as
  part of this feature — where the learner keeps the exported file afterward is entirely their
  own choice and responsibility, outside this feature's control.
- Multi-device sync or any real-time replication of data between devices.
- Partial, selective, or incremental export or restore of only some data categories.
- Merging, reconciling, or combining existing device data with an imported file — a restore
  always fully replaces existing data with the file's contents, never blends the two.
- Any in-app viewer or editor for inspecting or modifying the contents of an export file outside
  of the export and restore actions themselves.
- Recovering data that was never captured in a prior export — this feature protects only what
  was included in a backup the learner actually produced beforehand.
- Retaining or managing a history of multiple past export files within the app; each export
  stands alone.

## Open Questions
- [NEEDS CLARIFICATION: Immediately after the learner restores data following a real data-loss
  event, does the last-backup-recency indicator (FR-4/FR-6) correctly reflect that a valid
  backup still exists externally, or does it read "no backup yet" (FR-8) simply because that
  recency record is itself local data that was wiped along with everything else and has not yet
  been re-derived from the just-completed restore? Getting this wrong would show a contradictory
  or alarming signal — "no backup yet" — moments after the learner just successfully restored
  from one, undermining the exact trust this feature exists to build. This needs a decision on
  whether/how the last-backup record is reconstructed as part of a successful restore.]

## Acceptance Criteria
- [ ] Triggering the export action produces one export containing all four data categories
  (study plan/task history, vocabulary, mistake log, practice results) with none omitted, and
  no selective/partial export option exists (FR-1, FR-2).
- [ ] A successful export's confirmation names a specific, distinguishable export identifier or
  timestamp and states where it was saved (FR-3).
- [ ] A successful export immediately updates the last-backup information the learner can see
  (FR-4).
- [ ] A failed export shows a message distinct from success, leaves prior last-backup
  information unchanged, and allows an immediate retry (FR-5).
- [ ] The main landing view shows last-backup recency without navigating into a dedicated
  export/restore area (FR-6), with a direct action there to start an export (FR-7).
- [ ] Before any export has ever occurred on a device, the indicator states no backup exists
  yet rather than showing a fabricated or blank time value (FR-8).
- [ ] Selecting a file for restore always runs validation before any overwrite confirmation is
  shown, with no path that skips validation (FR-9, FR-10).
- [ ] An invalid or corrupted file is rejected with a clear, specific message and never reaches
  the overwrite-confirmation step (FR-11).
- [ ] A file that passes validation triggers an explicit confirmation stating that existing data
  will be overwritten (FR-12).
- [ ] Proceeding past that confirmation requires a deliberate confirming action that cannot be
  triggered by default or by accident (FR-13), and an equally clear cancel action leaves all
  existing data unchanged (FR-14).
- [ ] Confirming a restore fully replaces all four data categories with the validated file's
  contents, with no category left partially restored or untouched (FR-15).
- [ ] Immediately after a restore completes, the main landing view (and other normal views)
  reflect the restored data without any further action from the learner (FR-16).
- [ ] Opening the app with no learner data found presents a distinct, non-error empty state that
  offers a direct path into the restore action (FR-17).
