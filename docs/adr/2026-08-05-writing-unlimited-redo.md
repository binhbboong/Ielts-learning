# ADR: Writing allows unlimited same-day redo, with clearer retry UX

Date: 2026-08-05
Slug: writing-unlimited-redo
Status: Accepted
Related spec: docs/specs/writing-coach/Specification.md

## Context

Writing already permits multiple submissions per day at the data layer: `WritingSubmission`
has no per-day uniqueness constraint, and the daily-lesson-plan checkpoint (FR-15 of
`docs/specs/daily-lesson-plan/Specification.md`) already passes a day's Writing checkpoint if
*any* submission that day meets the learner's minimum band — a best-of-attempts model. But the
daily overview's UI does not expose this: once a submission exists, the entry's action is
labeled "Review" and routes to a blank submission form with no indication of the prior
attempt's result, so a learner has no visible reason to believe writing again is possible or
useful.

## Decision

Treat a day's Writing prompt as repeatable by design, and make that visible:

- The daily overview's action for a Writing entry with an existing same-day submission is
  relabeled to make a retry discoverable (e.g. "Try again"), not implied read-only.
- Returning to submit Writing for a day that already has a submission shows that day's most
  recent submission's overall band and headline feedback before presenting the (same prompt,
  blank response) form to write again.
- No cap is introduced on the number of same-day attempts.

## Consequences

No backend/schema change is required — the data model and checkpoint logic already support
this. The frontend needs to fetch the latest same-day submission before rendering the writing
form. Accepting unlimited attempts means accepting a proportional increase in AI evaluation
calls per learner per day; this is intentional (an improve-your-band loop), not something this
decision caps — a usage limit remains a separate, not-yet-decided question (see
`docs/specs/writing-coach/Specification.md`'s Open Questions).
