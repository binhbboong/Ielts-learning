# ADR: Missed Question-Type Taxonomy is a Fixed, Hardcoded List Per Skill

Date: 2026-07-29
Slug: missed-question-type-taxonomy
Status: Accepted
Related spec: docs/specs/progress-tracking/Specification.md

## Context

Epic-4 (Practice Result Tracking & Progress Visibility) requires a "missed question type" value
on every logged practice result (FR-2), and the Progress Trend view's ranked breakdown region
(FR-7) is computed directly from those same per-record values, always rendered together with the
score trend. The Specification, the prototype, and both relevant wireframes
(`log-practice-result.md`, `progress-trend.md`) all explicitly leave the exact taxonomy content
undefined — only illustrative placeholder names (e.g. "Matching Headings," "True/False/Not
Given") are shown, marked as pending a canonical list.

Whatever shape this taxonomy takes gets written into every `PracticeResult` record from day one
and read back by the trend breakdown computation (`practice-trend.service.ts`). That makes the
*shape* of the taxonomy — not yet its specific content — a real data-model decision: other code
(the breakdown ranking logic, the log form's checklist UI, any future export/import in Epic-5)
will depend on however missed-question-type values are represented and validated. This is
explicitly a separate concept from Epic-3's Mistake Notebook module, which tracks its own
independent "mistake-reason" taxonomy for a different purpose (categorizing individual mistakes,
not tallying missed question types across practice sessions) — the two must not be conflated
into one shared taxonomy.

## Decision

The missed-question-type taxonomy is a fixed, hardcoded, per-skill list (one list for Reading,
one for Listening), defined once as a source-level constant that both the logging checklist
(FR-2) and the trend breakdown ranking (FR-7) reference — not a free-text field, not a
user-extensible/dynamic list, and not shared with or derived from Epic-3's mistake-reason
taxonomy. Each `PracticeResult` record stores missed types as values drawn from this fixed list.
The taxonomy content was resolved on 2026-07-29 using the official IELTS Academic test-format
lists: 11 Reading types and 6 Listening types. Stored records use stable machine keys; the API
serves those keys with official human-readable labels so display wording can evolve without
rewriting historical records.

## Consequences

- Easier: a closed, known set of values makes the FR-7 ranked breakdown a simple group-and-count
  operation with no normalization or free-text parsing; the log form's checklist UI (multi-select
  taps, per the wireframe) is a direct, low-risk render of a static list; validation of stored
  values is trivial (must be a member of the skill's list).
- Harder: adding, renaming, or removing a question type later requires updating the constant and
  deciding what happens to historic records that reference an old value (a small migration or
  a "legacy label" fallback), rather than being a value the learner could just start typing.
- Forecloses: a free-text or fully user-defined missed-question-type field without later adding
  explicit migration/versioning support for the taxonomy constant.
- Explicitly does not affect: Epic-3's Mistake Notebook module, which keeps its own separate
  mistake-reason taxonomy for a different concept; no code or data model is shared between the
  two.
