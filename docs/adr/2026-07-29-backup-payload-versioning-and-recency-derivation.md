# ADR: Versioned Single-File Backup Payload Shape, with Last-Backup Recency Re-Derived from the Restored File

Date: 2026-07-29
Slug: backup-payload-versioning-and-recency-derivation
Status: Accepted
Related spec: docs/specs/data-backup-restore/Specification.md

## Context

The Data Portability & Backup/Restore feature (FR-1 through FR-17) is this client-only app's
entire durability story: per `docs/adr/2026-07-29-v1-no-backend-architecture.md`, there is no
server-side copy of learner data anywhere, so the shape of the exported JSON file is the only
long-term contract standing between a learner's data and permanent loss. Every other V1 feature
module (Study Plan, Vocabulary, Mistake Notebook, Practice & Progress) implicitly depends on
this shape being able to carry their data forward across app updates without a future schema
change silently breaking the ability to restore an old backup file. This is exactly the kind of
data-shape decision the implementation-planning process flags as costly to reverse once learners
start accumulating exported files on their own external storage (FR-2, Out of Scope: no
retained in-app history of past exports, so an old file may be a learner's *only* copy).

Separately, the spec (`docs/specs/data-backup-restore/Specification.md`, Open Questions) leaves
open whether the last-backup-recency indicator (FR-4, FR-6, FR-8) is its own value that must be
kept in sync, or something re-derived from a more durable source. This matters concretely at one
moment: immediately after a learner restores following a real data-loss event (FR-16, FR-17),
does the indicator correctly show that a valid backup exists, or does it wrongly read "no backup
yet" (FR-8) because the recency record itself was wiped along with everything else and never
reconstructed? Getting this wrong undermines the exact trust this feature exists to build, at the
single moment that trust matters most.

## Decision

**Payload shape and versioning.** A single export produces one flat JSON file with a top-level
`schemaVersion` (starting at `1`), a top-level `exportedAt` ISO-8601 timestamp, and a `data`
object containing all four categories named in FR-1 (`studyPlan`, `vocabulary`, `mistakes`,
`practiceResults`) in full — never partial or nested per-category versioning. `schemaVersion` is
a single integer for the whole file, not one per category, because in V1 all four categories are
introduced and evolve together; per-category versioning is deferred until a real need for
independent category evolution appears (see Consequences). Any future schema change increments
`schemaVersion` and is handled by an explicit migration step keyed off the old version number
before the payload is used — restoring a file with an unrecognized or unsupported
`schemaVersion` is treated as a validation failure (FR-10/FR-11), never a silent best-effort
restore.

**Last-backup recency is a stored value, explicitly re-derived from the restored file on every
restore.** The last-backup record (what FR-6's indicator reads) is its own small entry in the
Local Data Layer, written whenever an export succeeds (FR-4) — it is not recomputed from
scratch on every read, since nothing more durable than the Local Data Layer exists in a
client-only app to recompute it from during normal use. However, because the export payload
itself always carries its own `exportedAt` timestamp, a **restore operation explicitly rewrites
the last-backup record from the restored payload's `exportedAt`** as part of completing the
restore (FR-15/FR-16), rather than leaving it untouched or blank. This is a new planning-level
decision resolving the spec's previously open question, not a reinterpretation of the spec
itself: after a post-data-loss restore, the indicator will correctly show "last backup: N days
ago" (the age of the file just restored from) instead of "no backup yet" — because the backup
record round-trips through the export/restore cycle as part of the payload's own metadata,
surviving a total local-data wipe by virtue of living inside the very file that undoes it.

## Consequences

- Easier: one flat schema keeps export/validate/restore logic simple for a solo project's actual
  scope (four categories that move together); the recency fix is nearly free once `exportedAt` is
  already part of the payload, requiring only that RestoreService writes it back, not a new
  storage mechanism.
- Harder: if a future epic needs one data category to evolve on a different cadence than the
  others (e.g., a major Vocabulary schema change unrelated to Study Plan), a single whole-file
  `schemaVersion` means that change still bumps the version for everything, and any migration
  function must handle all four categories' shapes for that version even if only one changed.
- Forecloses (for now): per-category independent versioning and any backup format that omits its
  own timestamp metadata. Both remain reversible later — a future ADR could introduce
  per-category versions inside the same envelope — but every V1 export file is permanently a
  flat, single-versioned, self-timestamped JSON document, and restore logic must keep supporting
  `schemaVersion: 1` files indefinitely (or provide a migration) since learners may restore an
  old file at any future point per Out of Scope's "no in-app history of past exports."
- Risk accepted: because there is no external, more-durable source than the Local Data Layer to
  verify recency against, the recency indicator's correctness after restore depends entirely on
  RestoreService faithfully executing this re-derivation step every time — this must be covered
  by a dedicated automated test (see ImplementationPlan.md Testing Strategy), not left to manual
  verification, since a regression here would silently reintroduce the exact trust problem this
  ADR resolves.
