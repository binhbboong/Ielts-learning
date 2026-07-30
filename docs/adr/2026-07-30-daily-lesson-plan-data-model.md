# ADR: Daily Lesson Plan data model — per-day/per-skill focus table, no owned status

Date: 2026-07-30
Slug: daily-lesson-plan-data-model
Status: Accepted
Related spec: docs/specs/daily-lesson-plan/Specification.md

## Context

The PRD revision that introduced continuous, AI-generated daily lessons supersedes the prior
`study-plan-execution` epic, whose schema (`docs/adr/2026-07-29-study-plan-relational-task-store.md`:
a flat `tasks` table keyed by `day_number` with a pre-loaded `title`/`description`, plus a
singleton `plan_state` row holding `current_day_number`/`total_days`) assumed a fixed 180-day,
pre-authored checklist. That shape does not fit the new model: there is no fixed `total_days`,
no pre-loaded task text (content is generated per skill per day), and "day" is now a calendar
date rather than a sequential counter the learner advances through explicitly.

The new Daily Personalized Lesson Plan feature (PRD Epic-1) needs its own data model, and that
model needs to answer a specific design question: does it own a copy of each skill's
Ready/Generating/Done/Failed status (FR-4), or does it own only the personalization decision
and derive status by reading each skill's own table? Reading Practice (Epic-9), Listening
Practice (Epic-10), and the existing Writing/Speaking submission tables already are (or will
be) each skill's own source of truth for its own generation/completion state — this decision
determines whether that state gets duplicated.

## Decision

Two new tables, replacing `tasks`/`plan_state` (which are dropped once this feature ships —
see Consequences):

```
daily_focus
  id                  PK
  day                 Date, indexed
  skill               enum: reading | listening | writing | speaking
  focus_kind          enum: mistake | vocabulary | default
  focus_reference     text, nullable  -- human-readable description of the targeted
                                         mistake pattern or vocabulary word, e.g.
                                         "the word 'nevertheless'" (FR-6). Not a foreign
                                         key to mistake_log/vocabulary_words — see Rule 2.
  created_at          timestamptz
  UNIQUE (day, skill)
```

No second table for status. Rules that make this shape hold up as Epic-9/10 are built by
different, non-communicating planning passes:

1. **`daily_focus` is written exactly once per (day, skill) and never updated after creation**
   (FR-3, FR-9/FR-14 in the downstream specs). The unique constraint on `(day, skill)` is what
   makes "generate exactly once, reuse on every view" enforceable at the database level, not
   just by application discipline.
2. **`focus_reference` is a denormalized, human-readable string, not a foreign key.** FR-10
   requires that a later edit or deletion of the source mistake/vocabulary item must never
   retroactively change or invalidate an already-generated day's content. A foreign key would
   either cascade-delete or dangle; a snapshot string sidesteps the question entirely. The
   *selection* logic (which mistake/word to target) still reads live from the Mistake Notebook
   and Vocabulary tables at generation time — only the chosen result is frozen into
   `daily_focus`.
3. **This table owns no status column.** Whether a given (day, skill) is Ready/Generating/
   Done/Failed (FR-4) is derived, not stored here — the Daily Lesson Plan module's read path
   queries Reading Practice's/Listening Practice's/the writing-submissions/speaking-submissions
   table for the row matching that (day, skill) and maps its own state to the shared
   Ready/Generating/Done/Failed vocabulary. This means Epic-9/10's own plans are free to design
   whatever internal status representation fits their generation pipeline (e.g. Listening's
   multi-step script/audio states from `docs/specs/listening-practice/Specification.md` FR-12/
   FR-13) without ever needing to keep a second table in sync — there is exactly one place each
   skill's true state lives.
4. **"Day" is a calendar `Date`, not a sequential counter.** There is no `plan_state`-equivalent
   singleton and no `total_days` — FR-8 (no fixed end date) is satisfied by construction: any
   date is a valid key, indefinitely.
5. **Carry-over (FR-11/FR-12) requires no special modeling.** Because `daily_focus` rows are
   permanent, immutable, keyed by their own day, and never deleted when a new day begins, a
   not-yet-Done skill from an earlier day is simply a `daily_focus` row whose corresponding
   skill-table entry hasn't reached Done — no separate "carried over" flag needed. The read
   path that assembles the overview screen queries for the current day's rows *plus* any
   earlier day's rows still not Done, and labels each by its own `day` value (satisfying FR-12's
   "visibly distinguish" requirement directly from data already present).

## Consequences

- **Easier**: Reading Practice, Listening Practice, and the existing Writing/Speaking modules
  each keep full ownership of their own status model — no cross-epic write coordination, no
  risk of the aggregator's cached status drifting from the real state. Adding a fifth "skill"
  later would mean one more read-path branch, not a schema migration on this table.
- **Harder**: the overview read path issues one query per skill per rendered day (today plus
  any carried-over days) rather than a single-table read — acceptable at single-learner scale,
  called out explicitly so it isn't silently assumed to be a single `SELECT`.
- **Forecloses**: storing task title/description/estimated-minutes directly (the old `tasks`
  shape) — all learner-facing content now lives in each skill's own generated-content table,
  never in `daily_focus`.
- **Supersedes** `docs/adr/2026-07-29-study-plan-relational-task-store.md` and the storage
  aspect of `docs/adr/2026-07-29-study-plan-flat-task-store.md`. The existing `tasks`/
  `plan_state` tables and the `study_plan` backend/frontend modules built against them are
  dropped as part of this epic's task breakdown, not kept alongside the new tables — per the
  PRD's supersede note, this is a rework, not an addition.
