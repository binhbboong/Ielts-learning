# ADR: Mistake-Reason Category Persisted as a Stable String Key, Not Free Text

Date: 2026-07-29
Slug: mistake-reason-category-enum-key
Status: Accepted
Related spec: docs/specs/mistake-tracking/Specification.md

## Context

FR-4 fixes the mistake-reason category to exactly nine options (e.g. "Didn't know the vocabulary,"
"Missed a paraphrase," ... "Not sure yet / other"). Two different parts of the Mistake Notebook module
depend on whatever representation is chosen for this value: the logging form writes it, and the
grouped-by-reason review (FR-11, FR-12, FR-13) reads it back and uses it as the grouping/join key for
counting and drill-down. Records are persisted indefinitely in IndexedDB (FR-16) with no backend and no
migration tooling implied by the architecture — whatever gets written today is what every future review
session groups against, potentially years later.

The open design choice is: store the exact display label as the persisted value, store an opaque
numeric/auto-incrementing id, or store a stable string key decoupled from the label. This matters because
it is a data-model choice other code (the grouping/counting logic) directly depends on, and because
correcting it after real data has been written would require a migration script touching every existing
record — there is no server-side data layer to run that migration from, only whatever the client app
itself provides.

## Decision

Each `MistakeEntry` persists its reason category as a stable, English, snake_case string key (e.g.
`missing_vocab`, `missed_paraphrase`, `misread_question`, `missing_information`, `outside_knowledge`,
`ran_out_of_time`, `carelessness`, `wrong_grammar`, `not_sure_other`), decoupled from its user-facing
display label. A single lookup table maps key -> label for rendering in the logging form and both review
views. The grouping/counting logic (`logic/mistake-grouping.ts`) groups by this key, never by the label
text.

Adding, removing, or renaming categories beyond the FR-4 set is out of this feature's scope per the
spec's Out of Scope section, and this decision does not attempt to design for that. It only fixes how
the currently-closed set is represented once persisted.

## Consequences

- **Easier**: display wording can be tweaked (typo fixes, rephrasing) without touching stored data or
  silently splitting a category's historical count across two label strings. Grouping/counting is a
  simple key-based reduce with no fuzzy string matching.
- **Harder**: if the category set itself ever changes (explicitly out of scope today, per the spec), any
  rename of an existing key would need a one-time migration over existing IndexedDB records, run from
  within the client app itself, since there is no backend to run it centrally.
- **Forecloses**: persisting the raw display label directly as the stored value — that path is not
  taken, since a future wording change would otherwise silently fragment historical grouping counts
  between the old and new label text with no way to reconcile them.
