# ADR: "Forgot" Resets a Word's Review Interval to the 1-Day Step

Date: 2026-07-29
Slug: vocab-forgot-resets-interval
Status: Accepted
Related spec: docs/specs/vocabulary-review/Specification.md

## Context

The Vocabulary & Spaced Repetition Review spec (FR-18) fully defines what happens on a
"remembered" assessment: the word progresses to the next step in the fixed 1/3/7/14/30-day
ladder. Neither the spec, the source wireframes
(`docs/ux/wireframes/vocabulary-review-session.md`), nor the prototype
(`docs/ux/prototypes/vocabulary-review-flow.md`) ever states what happens to a word's
interval when it is marked "forgot" instead. This was correctly left as an open question in
the spec rather than guessed at during UX/spec work, but it is a data-model decision other
code depends on directly: `SpacedRepetitionService`'s reschedule function (used by
`ReviewSessionService` on every assessment) needs one concrete rule to implement and test
against, and the due-queue size on any future day is a direct function of this rule. It also
bears on Vision goal G-3 (retention should not depend on the learner's memory or willpower
alone, measured by the ≥80%-of-due-vocabulary-reviewed-on-schedule metric) and on the
Vocabulary module's data model named in `docs/architecture/Architecture.md`. Three candidate
rules exist:

1. **Reset to the 1-day step** (interval index back to 0), same starting point as a brand-new
   word.
2. **Step back one level** in the ladder (e.g., forgot at the 30-day step moves to the 14-day
   step, not all the way back to 1 day).
3. **Leave the interval unchanged**, re-testing at the same interval on the next attempt.

## Decision

On a "forgot" assessment, the word's interval resets to the 1-day step (the same interval
index used for a brand-new word, per FR-4), regardless of which step it had progressed to
before the lapse. The next due date is set to "today + 1 day."

Reasoning:
- **Retention-safety first.** Vision G-3 is a retention guarantee, not a scheduling-efficiency
  guarantee. A "forgot" means the word is not currently retained, no matter how far along the
  ladder it had climbed; the reset rule re-tests it soonest, which is the conservative choice
  under uncertainty. "Step back one level" is materially riskier at the far end of the ladder:
  forgetting a word at the 30-day step would still leave 14 days before the next check,
  during which the word remains unretained but reads as "on schedule" — directly undermining
  the metric this feature is measured against. "Unchanged" is the same problem in the worst
  case (a forgotten word could stay parked at a 30-day interval indefinitely if forgotten
  repeatedly at that step).
- **Consistency with an existing rule.** FR-4 already establishes "new word starts at the
  1-day interval" as a rule the codebase implements and tests. Reusing that exact rule for
  "forgot" (rather than introducing a second, different reset target) means
  `SpacedRepetitionService` has one reset behavior, not two, which is simpler to implement,
  test, and reason about.
- **Convention.** This is the common, defensible convention in simple (non-adaptive) spaced-
  repetition schemes — the spec's Out of Scope section explicitly excludes adaptive/per-word
  difficulty tuning (e.g., Leitner-style "back to box 1" restarts), so a more nuanced
  step-back rule would be inconsistent with the fixed-ladder design this feature already
  commits to.

## Consequences

- **Easier:** `SpacedRepetitionService`'s reschedule function has exactly two outcomes to
  implement and test — "remembered" advances one step (floor at the last step, 30 days);
  "forgot" resets to step 0 (1 day) — with no per-step conditional logic. The same "reset to
  1-day" code path used for FR-4 (new word) can be reused for the "forgot" case.
- **Harder / accepted trade-off:** a word that lapses after reaching a long interval (e.g., 30
  days) restarts the full climb from 1 day, which can feel like a large step back to the
  learner and will tend to inflate near-term due-queue size after a lapse, compared to the
  "step back one level" alternative. This is accepted as the safer default for a retention
  guarantee; it can be revisited with its own ADR if real usage shows the reset is too harsh
  (e.g., by moving to a step-back rule) — that would be a schedule-algorithm change, which the
  spec's Out of Scope section already flags as excluded from this feature and would need to
  go through its own spec/ADR update, not a silent tweak.
- **Forecloses (for V1):** any per-word adaptive difficulty tuning is still out of scope per
  the spec; this decision does not reopen that door, it only fixes the fixed-ladder's lapse
  behavior.
