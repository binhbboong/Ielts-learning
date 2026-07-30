# ADR: Data Export Is a Single Versioned JSON Document, Assembled via a Per-Epic Export Contract

Date: 2026-07-29
Slug: data-portability-export-contract
Status: Accepted
Related spec: docs/specs/data-portability/Specification.md

## Context

The Data Portability epic (FR-1 through FR-9) must let the learner produce one complete,
self-readable copy of all their data — spanning study plan/task history, vocabulary, mistake
log, practice results, and Writing/Speaking submissions with AI feedback — on demand, at any
time. None of those other epics' database tables exist in code yet; they are being planned in
parallel right now. This epic's implementation therefore has to commit today to (a) how the
export is assembled across epics whose schemas aren't written yet, and (b) what shape the
resulting file takes — both decisions other, not-yet-written code will be built against, and
both are expensive to reverse once learners start holding exported files and other epics start
implementing against the contract. That combination — a data shape other code depends on, plus
real-world artifacts (exported files) that will outlive any one implementation — is exactly the
implementation-planning skill's ADR trigger.

Two sub-decisions are in scope: how assembly is structured (addressed at the approach level in
the Implementation Plan; the registry/contract choice is restated here because the file shape
depends on it), and what the resulting file itself looks like.

## Decision

1. **Assembly is via a per-epic contract, not centralized queries or introspection.** Every
   epic exposes `export_learner_data(db: Session) -> dict` from its own `services/<epic>.py`,
   returning its own data in a category-tagged, JSON-serializable shape it considers a faithful
   self-readable representation. The Data Portability epic maintains a registry
   (`EXPORT_SOURCES`) of these functions and calls each one to assemble the full export. (Full
   reasoning and rejected alternatives — direct cross-epic queries, generic schema
   introspection — are in the Implementation Plan's Approach section; this ADR records the
   decision, not the trade-off analysis.)

2. **The export is one JSON document, not multiple files, and it is explicitly versioned.**
   Structure:
   ```
   {
     "export_format_version": 1,
     "produced_at": "<ISO-8601 timestamp>",
     "categories": ["study_plan", "vocabulary", "mistakes", "practice_results",
                     "writing_submissions", "speaking_submissions"],
     "data": {
       "study_plan": { ... whatever study-plan-execution's export_learner_data() returns ... },
       "vocabulary": { ... },
       "mistakes": { ... },
       "practice_results": { ... },
       "writing_submissions": { ... },
       "speaking_submissions": { ... }
     }
   }
   ```
   - **One document, not one file per category:** FR-1/FR-2 require every category present in
     full, every time, with none omittable — a single document makes "the export" one artifact
     the learner keeps, rather than a set of files that could be partially copied, partially
     lost, or partially shared, which would undermine FR-2's completeness guarantee at the
     point of use even if the export itself was complete at creation.
   - **`export_format_version` is a top-level integer, incremented whenever the document's
     shape changes.** This is what makes the format's evolution reversible even though the file
     itself is not: old exported files remain readable as "version 1" forever; a future reader
     (human or tool) can branch on the version field instead of guessing. This is the concrete
     mechanism that keeps a costly-to-reverse decision (the shape) from becoming a permanently
     frozen one (the ability to improve the shape later).
   - **JSON, not CSV/ZIP-of-CSVs or a database dump.** JSON is human-readable in a text editor,
     universally parseable by "generally available tools" (FR-3) without this application, and
     naturally represents the nested/relational shape of submissions-with-feedback without
     inventing a multi-file join convention. A future enhancement could offer a ZIP containing
     this JSON plus raw audio files for Speaking submissions if audio blobs turn out not to
     belong inline in JSON (deferred — no Speaking epic exists yet to confirm audio storage
     shape); this ADR only commits to JSON as the document format, not to excluding binary
     attachments forever.
   - **AI feedback is inlined as plain fields inside each submission's exported record**
     (scores, strengths, weaknesses, corrections as ordinary JSON values), not as a separate
     category or a provider-specific structured object — per this plan's resolution of the
     AI-portability open question, the goal is a permanent readable record, not a
     re-gradable input.

## Consequences

- **Easier:** every other epic has one unambiguous function signature and category key to
  implement against; the Data Portability epic's own code never needs to change when another
  epic's internal schema changes, only when that epic's `export_learner_data()` output changes
  (and even then, only that epic's registry entry, not the assembler); a future importer (if
  ever built) has a versioned, self-describing format to branch on instead of guessing.
- **Harder:** every epic must remember to add and register its export function — a coordination
  cost across parallel plans that the Implementation Plan's testing strategy mitigates with a
  registry-completeness test, but does not eliminate; if an epic ships without adding its export
  function, FR-2 quietly fails for that category until caught.
- **Forecloses (for now, reversibly):** a per-category-file or streaming/paginated export
  format — reasonable if data volume ever becomes large enough that one JSON document is
  unwieldy, but not a documented concern today given a single learner's data volume; revisit by
  incrementing `export_format_version` and superseding this ADR if that need materializes.
- **Does not decide:** whether Speaking submission audio is stored/exported as inline
  base64, a linked external reference, or excluded — deferred to whichever epic defines
  Speaking submission storage, since that data doesn't exist yet.
