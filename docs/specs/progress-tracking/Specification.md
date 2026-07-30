# Specification: Practice Result Tracking & Progress Visibility
Related UX: docs/ux/prototypes/progress-tracking-flow.md

## Status
Draft

## Overview
This feature lets a self-directed IELTS learner record the results of Reading and Listening
practice sessions completed outside the app (a book, a website, an audio track), and later
review how those results trend over time. It covers two halves of one loop: capturing a result
in a single low-friction sitting right after practice, and — on a separate, later visit —
reviewing an aggregated view of average score, trend direction, and the specific question
types missed most often, so the learner has an objective signal of progress rather than a
feeling. This is PRD Epic-4 and directly serves Vision goal G-4 (making skill progress visible
over time so momentum and weak areas can be seen rather than felt).

The persona's defining pain point is not knowing whether practice is actually paying off, and
not trusting that a logged result actually persisted. Both halves of this feature exist to
close that gap: logging must be fast enough and reliable enough that the learner never loses a
data point, and the trend review must always pair a raw score signal with a constructive,
actionable next step so a flat or declining period reads as useful diagnostic information
rather than discouragement. Writing and Speaking result tracking, and any comparison across
multiple learners, are explicitly out of scope for this feature.

## User Scenarios
- As a solo IELTS learner, I want to record a Reading or Listening practice result (skill,
  source, score, time taken) right after finishing, so that the details don't fade before I
  capture them.
- As a solo IELTS learner, I want to optionally note which question types I missed and add a
  free-text note without being forced to fill them in, so that logging stays fast even when I
  don't remember every detail.
- As a solo IELTS learner, I want unambiguous confirmation that my result was saved, so that I
  never have to wonder whether my progress was actually recorded.
- As a solo IELTS learner, I want a failed save to keep everything I typed, so that I never have
  to reconstruct a result from memory a second time.
- As a solo IELTS learner, I want to see my average score and trend direction over a recent
  period, so that I know whether my Reading/Listening is actually improving.
- As a solo IELTS learner, I want the trend view to always show me which question types I miss
  most often alongside the score trend, so that a flat or declining trend still tells me exactly
  what to work on next instead of just feeling like failure.
- As a solo IELTS learner, I want a clear signal when I haven't logged enough sessions yet for a
  meaningful trend, so that I understand I need to keep logging rather than assume the feature is
  broken or empty.
- As a solo IELTS learner, I want to browse the raw chronological list of everything I've
  logged, so that I can look up or double-check a specific past session.

## Functional Requirements
- FR-1: The system MUST allow the learner to record a practice result, and MUST require, at
  minimum, the skill (Reading or Listening), the source, the score (number correct out of a
  total), and the time taken before the record can be saved.
- FR-2: The system MUST allow the learner to optionally tag one or more missed question types
  and optionally add a free-text note when recording a result, and MUST NOT require either field
  to be filled in order to save.
- FR-3: If an attempt to save a practice result fails, the system MUST retain every value the
  learner entered or selected, present an explicit indication that the save failed, and allow the
  learner to retry saving without re-entering any data.
- FR-4: If an attempt to save a practice result succeeds, the system MUST present an explicit
  confirmation state distinct from the entry form, stating that the result was recorded (at
  minimum reflecting the skill and score just saved), rather than returning silently to a prior
  screen or leaving the form as-is.
- FR-5: From the save confirmation state, the system MUST let the learner either begin logging
  another result or return to where they started, without losing the confirmation of the result
  just saved.
- FR-6: The system MUST let the learner abandon an in-progress, unsaved entry at any point
  without recording it.
- FR-7: The system MUST provide a progress trend view that, for a selected skill and a selected
  recent time period, always presents the average score and trend direction (up, stable, or down)
  together with a ranked breakdown of the question types missed most often across the same
  sessions, as a single combined view — the system MUST NOT present the score trend without the
  missed-question-type breakdown shown alongside it in the same view, regardless of whether the
  trend is up, stable, or down.
- FR-8: When fewer than 4 practice sessions have been logged for the selected skill and period,
  the system MUST NOT present a score trend as though it were a meaningful signal; instead it
  MUST indicate how many sessions have been logged so far and how many more are needed to reach
  the 4-session threshold, while still surfacing any missed-question-type information available
  from the sessions logged so far.
- FR-9: When zero practice sessions have ever been logged, the progress trend view MUST present
  a message directing the learner to log a practice result, rather than an empty or blank trend
  display.
- FR-10: The system MUST let the learner filter the progress trend view by skill (Reading,
  Listening, or Both) and by a recent time period, and re-present both the score trend and the
  missed-question-type breakdown for the newly selected filter.
- FR-11: The system MUST let the learner manually refresh the progress trend view to reflect the
  most recently logged results.
- FR-12: The system MUST distinguish, within the progress trend view, between "not enough
  sessions logged yet" (fewer than 4, including zero) and a genuine failure to load existing
  results, using wording that makes clear which situation applies.
- FR-13: The system MUST provide a way for the learner to browse the complete chronological list
  of every previously logged practice result, showing at minimum the date, skill, source, score,
  and time taken per entry, with missed question types and any note shown as secondary detail per
  entry. [NEEDS CLARIFICATION: should this capability be treated as a core/required requirement
  of Epic-4, or as an optional supporting capability lower in priority than the progress trend
  view, for the purpose of future prioritization? No journey step walks through it; the
  prototype explicitly marks it a side branch, not part of the success path.]
- FR-14: The system MUST let the learner filter the chronological practice result list by skill
  and change its sort order between newest-first and oldest-first.
- FR-15: When no practice results have ever been logged, the chronological list MUST present a
  message indicating nothing has been logged yet, together with a direct path to log a result.
- FR-16: The system MUST distinguish, within the chronological practice result list, between
  "nothing logged yet" and a genuine failure to load existing results, using wording that makes
  clear which situation applies.

## Out of Scope
- Recording or scoring Writing or Speaking practice sessions (PRD Epic-6, deferred to a later
  version).
- Comparing progress across multiple learners or any shared/social view of results.
- Editing or deleting a previously saved practice result — no journey step, wireframe, or
  prototype transition establishes this capability; it is not addressed by this specification.
- Restoring practice results from a backup after data loss (covered separately by PRD Epic-5).
- The specific visual design of the score-trend chart/graph (colors, axis styling, chart type) —
  the wireframe leaves this undecided and it is a design/implementation concern, not a
  requirement of this feature.
- Any goal-setting, target-score comparison, or predicted-band-score functionality — not
  established by the journey, wireframes, or prototype for this epic.

## Open Questions
- [NEEDS CLARIFICATION: The taxonomy of missed question types per skill (Reading vs. Listening)
  is not defined by the journey, wireframes, or prototype — only illustrative placeholder names
  exist. This taxonomy is shared functional data between logging (FR-2) and the trend breakdown
  (FR-7) and should be resolved once, consistently, rather than guessed here.]
- [NEEDS CLARIFICATION: Should browsing the chronological practice result list (FR-13-16) be
  treated as a core/required part of Epic-4, or as an optional supporting capability of lower
  priority than the progress trend view? See FR-13.]
- [NEEDS CLARIFICATION: What exact mechanism lets the learner start a new practice result entry
  (a persistent "Log Result" action, a navigation item, or a dedicated landing screen)? No
  wireframe defines the app's shared entry chrome outside the Log Practice Result screen itself.]
- [NEEDS CLARIFICATION: When the progress trend view shows a partial missed-question-type
  breakdown below the 4-session threshold (FR-8), should it link out to the chronological
  practice result list for the underlying raw entries, or are the two views intentionally kept
  independent with no cross-navigation?]

## Acceptance Criteria
- [ ] A practice result cannot be saved unless skill, source, score, and time taken are all
      provided (FR-1).
- [ ] A practice result can be saved with missed question types and note both left blank (FR-2).
- [ ] After a simulated save failure, every previously entered field value is still present and
      the save can be retried without re-entering data (FR-3).
- [ ] After a successful save, an explicit confirmation state is shown naming the skill and score
      just saved (FR-4).
- [ ] From the confirmation state, the learner can start a new entry or return to their prior
      context (FR-5).
- [ ] An in-progress entry can be abandoned without creating a saved record (FR-6).
- [ ] For a skill/period with 4 or more logged sessions, the trend view shows average score,
      trend direction, and the missed-question-type breakdown together in the same view (FR-7).
- [ ] For a skill/period with fewer than 4 logged sessions, no score trend is presented as
      meaningful; a count toward the 4-session threshold is shown instead, alongside any
      available missed-question-type data (FR-8).
- [ ] With zero sessions ever logged, the trend view shows a message directing the learner to log
      a result, not an empty chart (FR-9).
- [ ] Changing the skill filter or period on the trend view updates both the score trend and the
      missed-question-type breakdown together (FR-10).
- [ ] Refreshing the trend view reflects a result logged since the view was opened (FR-11).
- [ ] The trend view's "not enough sessions" wording is visibly distinct from its "failed to
      load" wording (FR-12).
- [ ] The chronological practice result list shows date, skill, source, score, and time taken per
      entry, with missed question types and note as secondary detail (FR-13).
- [ ] The chronological list can be filtered by skill and re-sorted between newest-first and
      oldest-first (FR-14).
- [ ] With no results ever logged, the chronological list shows a "nothing logged yet" message
      with a path to log a result (FR-15).
- [ ] The chronological list's "nothing logged yet" wording is visibly distinct from its "failed
      to load" wording (FR-16).
