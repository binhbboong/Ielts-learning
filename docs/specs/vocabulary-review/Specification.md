# Specification: Vocabulary & Spaced Repetition Review
Related UX: docs/ux/prototypes/vocabulary-review-flow.md

## Revision 4 — Post-review quiz (checkpoint)

Decision: `docs/adr/2026-08-03-daily-checkpoint-gating.md`.

- FR-36: After a day's review session (FR-13–FR-24, self-assessed recall/reveal/assess) reaches
  the review-complete state, the system MUST offer a quiz step covering every word reviewed that
  session (due words and backfilled words alike, FR-31).
- FR-37: Each quiz question MUST show one reviewed word and four shuffled meaning options: the
  word's own correct meaning plus three distractors. Distractors MUST be drawn from the
  learner's other owned words at the same CEFR level where at least three exist; when fewer than
  three same-level words exist, the system MUST fall back to other words reviewed that session,
  and MUST NOT block or error when the learner's vocabulary is too small for four full options —
  it uses as many distinct distractors as are available.
- FR-38: The learner MUST select exactly one option per question before advancing; the system
  MUST NOT reveal correctness before a selection is made.
- FR-39: The system MUST auto-grade the quiz (no self-assessment) and compute a
  `correct / total` score once every question is answered.
- FR-40: The quiz result MUST be persisted per (learner, day) and MUST NOT be retaken once
  submitted for that day — matching the once-per-day nature of the review session itself
  (`docs/adr/2026-08-03-vocabulary-daily-minimum.md`'s once-per-day backfill gate).
- FR-41: The quiz score MUST be exposed (via the vocabulary API) for `daily-lesson-plan`'s
  checkpoint evaluation to read — this feature does not itself decide pass/fail thresholds
  (owned by `daily-lesson-plan`, FR-15) or gate anything; it only produces and persists the score.

## Revision 3 — Daily 20-word minimum

Decision: `docs/adr/2026-08-03-vocabulary-daily-minimum.md`.

- FR-31: Each day's review session MUST target a minimum of 20 words: due words first (existing
  behavior, unchanged), backfilled with additional curated, level-appropriate recommended words
  (per FR-27) up to a total of 20 when the due count is below 20.
- FR-32: A backfilled word MUST be persisted to the learner's vocabulary (source
  `daily_backfill`) and included in that day's review queue at creation time — not merely
  displayed as a suggestion requiring a separate manual "add" action.
- FR-33: When fewer than 20 unowned recommended words remain for the learner's current band, the
  system MUST use as many as are available and MUST communicate the shortfall, rather than
  blocking session start or silently presenting fewer than 20 without explanation.
- FR-34: The due-review entry point (before starting a session) MUST show, alongside the due
  count (FR-8), how many additional words will be backfilled to reach today's 20-word target,
  and MUST indicate when a shortfall (FR-33) means today's target cannot be fully reached.
- FR-35: The review-complete state (FR-20) MUST additionally report how many of the words
  reviewed in that session were new backfilled words (distinct from due words), so the learner
  can see today's practice was not just previously-seen review.

## Revision 2 — Level-aware IELTS Academic vocabulary

- FR-25: The system MUST derive the learner's vocabulary level from the authenticated
  learner's study profile, current week, phase, and target band.
- FR-26: The vocabulary page MUST show the current IELTS band and corresponding CEFR level.
- FR-27: The system MUST recommend curated IELTS Academic words for that level, including
  meaning, example sentence, and topic.
- FR-28: Words already present in the learner's vocabulary MUST NOT be recommended again.
- FR-29: A recommended word MUST be addable directly to spaced repetition and retain its
  target band, CEFR level, and recommendation source.
- FR-30: Recommendations and saved words MUST remain isolated by learner account.

## Status
Approved — revision 4 (post-review quiz)

## Overview
This feature lets the solo learner capture new vocabulary words as they encounter them and
review existing words on a spaced-repetition schedule that surfaces exactly what's due each
day, with no external tool or manual tracking required. It covers three connected
capabilities: adding a word so it enters the review schedule, seeing an at-a-glance summary of
today's due queue before committing to it, and working through that queue one word at a time
using self-tested recall (recall the meaning, reveal it, honestly self-assess) so the app can
reschedule each word appropriately.

The feature exists to satisfy PRD Epic-2 and Vision goal G-3: retention should not depend on
the learner's memory or willpower alone. Its success is measured externally by the
≥80%-of-due-vocabulary-reviewed-on-schedule metric, and internally by whether a full day's
queue can be cleared in one uninterrupted, low-friction sitting — and can be resumed cleanly
if it isn't.

## User Scenarios
- As a solo IELTS learner, I want to capture a new word (its word and meaning, optionally an
  example and topic) in under 30 seconds, so that vocabulary I encounter in the moment isn't
  lost before it enters my review schedule.
- As a solo IELTS learner, I want to see how many words are due today and a sense of why that
  number is what it is before I start reviewing, so that I can commit to the session without
  the queue size itself feeling like a reason to defer it.
- As a solo IELTS learner, I want to recall each due word's meaning myself before it's revealed,
  so that I'm practicing active recall rather than passively re-reading answers.
- As a solo IELTS learner, I want to honestly mark whether I remembered or forgot each word, so
  that the review schedule adapts to my actual retention rather than a flattering guess.
- As a solo IELTS learner, I want the app to reschedule each word automatically and advance to
  the next one without any manual step, so that I can trust the schedule instead of tracking
  intervals myself.
- As a solo IELTS learner, I want an unambiguous "done" signal once I've reviewed every word due
  today, so that I know today's vocabulary obligation is fully met.
- As a solo IELTS learner, I want an interrupted review session to resume exactly where I left
  off — not restart and not lose words I already assessed — so that a real-life interruption
  (tiredness, closing the browser) doesn't cost me progress or force we to redo work.
- As a solo IELTS learner, I want to add a word I just noticed without leaving my in-progress
  review session, so that I don't have to choose between capturing it now and finishing my
  review.

## Functional Requirements

### Capturing vocabulary
- FR-1: The system MUST let the learner add a new vocabulary word by providing, at minimum, the
  word itself and its meaning.
- FR-2: The system MUST allow the learner to optionally provide an example sentence and a topic
  when adding a word, and MUST NOT require either field to save the word.
- FR-3: The system MUST prevent saving a new word until both the word and meaning fields are
  non-empty.
- FR-4: The system MUST place a newly saved word into the spaced-repetition schedule starting at
  the 1-day review interval.
- FR-5: The system MUST confirm to the learner that the word was saved and has entered the
  review schedule.
- FR-6: When adding a word fails to save, the system MUST preserve everything the learner had
  typed (no field is cleared or reset) and MUST let the learner retry the save without
  re-entering any data.
- FR-7: The system MUST let the learner add a new word from within an in-progress review
  session without ending or losing progress in that session, and MUST return the learner to the
  exact word and queue position they were at before adding the word, whether they save the new
  word or cancel/close the add-word action.

### Viewing what's due
- FR-8: The system MUST show the learner, before starting a review session, how many words are
  due for review as of the current day.
- FR-9: The system MUST show the learner a breakdown of the due count (e.g., by review interval
  or topic) alongside the raw number, so the number is never presented without context.
- FR-10: When no words are due AND no backfill words are available to reach today's 20-word
  target (FR-31, FR-33) — i.e. there is genuinely nothing left to review or learn today — the
  system MUST present this as a neutral, positive state (the learner is on schedule) rather than
  an empty or broken-looking screen, and MUST NOT offer a "start review" action. When no words
  are due but backfill words are available, the system MUST still offer "start review" — zero
  due no longer implies nothing to do once FR-31's floor is in effect.
- FR-11: When the due count cannot be determined (e.g., a local data read failure), the system
  MUST NOT display a fabricated or zero count, and MUST clearly communicate that the count
  could not be loaded, distinct from there genuinely being nothing due.
- FR-12: The system MUST let the learner add a new word regardless of whether any words are
  currently due for review.

### Reviewing due words
- FR-13: The system MUST present due words to the learner one at a time, with the word's meaning
  hidden until the learner explicitly reveals it.
- FR-14: The system MUST let the learner reveal a word's meaning and example (if one exists) on
  their own action, rather than showing it automatically or on a timer.
- FR-15: Once a word's meaning is revealed, the system MUST require the learner to self-assess
  the outcome as either "forgot" or "remembered" before proceeding to the next word.
- FR-16: The system MUST save the learner's self-assessment for a word immediately upon
  selection, before advancing to the next word, so that an interruption immediately afterward
  does not lose that assessment.
- FR-17: The system MUST automatically advance to the next due word immediately after an
  assessment is saved, without requiring any additional action from the learner.
- FR-18: When a word is marked "remembered," the system MUST reschedule that word to progress to
  its next interval in the sequence (1/3/7/14/30 days), so consecutive successful reviews space
  out over time.
- FR-19: When the last due word in the queue is assessed, the system MUST transition immediately
  to an explicit review-complete state rather than leaving the queue silently empty.
- FR-20: The review-complete state MUST report, at minimum, the total number of words reviewed
  in the session and the count marked "forgot" versus "remembered."
- FR-21: The review-complete state MUST confirm to the learner that review dates were updated as
  a result of the session.
- FR-22: If a review session is interrupted before the due queue is emptied (e.g., the learner
  leaves or closes the app), the system MUST resume that session, the next time it is opened, at
  the exact next unreviewed word in the same queue — not restart the queue and not re-present
  words already assessed in that session.
- FR-23: When the learner opens the review flow with zero words due, the system MUST show an
  explicit "nothing due" state rather than any recall content, and MUST distinguish this from
  the review-complete state that follows finishing a queue.
- FR-24: When due-word or schedule data cannot be read reliably (e.g., local storage failure),
  the system MUST NOT present any word for review, and MUST communicate that something went
  wrong, distinct from there being nothing due.

## Out of Scope
- Audio pronunciation of vocabulary words.
- Free-form AI-generated vocabulary (e.g. an LLM inventing words on the fly). Recommended and
  backfilled words (FR-25–FR-30, FR-31–FR-35) come from a fixed, hand-curated per-band word bank,
  not model generation — see `docs/adr/2026-08-03-vocabulary-daily-minimum.md`'s Decision point 2
  for why that tradeoff was made and what it forecloses for now.
- Multi-language support beyond the learner's own single target language pair.
- Editing or deleting a previously saved vocabulary word (this feature covers adding and
  reviewing only).
- Any review-scheduling algorithm variation beyond the stated 1/3/7/14/30-day interval
  progression (e.g., adaptive or per-word-difficulty interval tuning).
- Multi-device sync or sharing of vocabulary data (per PRD/Vision, no server-hosted sync in this
  version).
- Reviewing or capturing vocabulary for skills other than the word/meaning/example/topic model
  described here (e.g., no separate grammar-point or phrase-pattern review).
- Any change to the due-count or streak elements as they appear on the Dashboard/Today Overview
  screen beyond the due-count value itself — the rest of that shared screen belongs to other
  epics' specifications.

## Resolved Decisions
- A "forgot" assessment resets the word to the 1-day interval, per
  `docs/adr/2026-07-29-vocab-forgot-resets-interval.md`.
- After saving or canceling Add Word from the Due List or Review Complete state, the learner
  remains on that exact host screen. A successful save closes the panel and shows an inline
  confirmation on the host screen; cancel simply closes it.
- The MVP has no due-queue cap. Every word with `next_due_date <= today` is counted and included
  in the session snapshot.
- **Daily 20-word minimum (resolved 2026-08-03).** Per
  `docs/adr/2026-08-03-vocabulary-daily-minimum.md`: due words are never capped (previous
  decision, unchanged) but are now floored — if fewer than 20 are due, the session is backfilled
  with curated recommended words up to 20 total, or as many as remain available for the
  learner's band. Backfilled words are due today (not the usual 1-day-later start), since they
  enter the queue to be reviewed immediately.

## Acceptance Criteria
- [ ] A word can be saved with only word and meaning filled in; example and topic can be left
  blank (FR-1, FR-2, FR-3).
- [ ] Attempting to save a word with an empty word or meaning field is blocked (FR-3).
- [ ] A newly saved word appears in the due queue at the 1-day interval (FR-4).
- [ ] Saving a word produces a visible confirmation, and a failed save preserves all typed field
  values and allows retry without re-entry (FR-5, FR-6).
- [ ] Adding a word from within an active review session returns the learner to the same word
  and queue position afterward, whether saved or canceled (FR-7).
- [ ] The due-review entry point shows a due count with a supporting breakdown before any review
  begins (FR-8, FR-9).
- [ ] With zero words due and zero backfill words available, no "start review" action is offered
  and the state reads as a positive milestone; with zero words due but backfill words available,
  "start review" is still offered (FR-10).
- [ ] When the due count fails to load, the screen shows neither a zero nor a fabricated number,
  and states the load failed (FR-11).
- [ ] "Add a new word" is reachable both when words are due and when none are due (FR-12).
- [ ] Each due word is shown with its meaning hidden until the learner reveals it, and the
  meaning is never shown before that explicit action (FR-13, FR-14).
- [ ] After reveal, the learner must choose "forgot" or "remembered" before the next word
  appears (FR-15).
- [ ] The chosen assessment is saved before the next word loads, and the queue advances
  automatically with no extra action (FR-16, FR-17).
- [ ] A word marked "remembered" moves to the next interval in the 1/3/7/14/30-day sequence
  (FR-18).
- [ ] Finishing the last due word transitions immediately to a review-complete state showing a
  total reviewed count, a forgot/remembered breakdown, and confirmation that review dates were
  updated (FR-19, FR-20, FR-21).
- [ ] Closing the app mid-queue and reopening the review flow resumes at the exact next
  unreviewed word, with prior assessments in that session intact (FR-22).
- [ ] Opening the review flow with nothing due shows a distinct "nothing due" state, not the
  review-complete state and not a recall card (FR-23).
- [ ] A local data read failure during review presents an explicit error state and never shows a
  word for review under that condition (FR-24).
- [ ] With fewer than 20 words due, starting a session backfills curated recommended words up to
  a total of 20, persisted as owned words due today (FR-31, FR-32).
- [ ] With fewer than 20 unowned recommended words left for the learner's band, the session uses
  what's available and the shortfall is communicated, not hidden or blocked (FR-33).
- [ ] The due-review entry point shows how many words will be backfilled to reach today's target,
  including a shortfall indicator when applicable (FR-34).
- [ ] The review-complete state additionally reports how many reviewed words were new backfilled
  words (FR-35).
- [ ] Reaching review-complete offers a quiz covering every reviewed word, 4 shuffled options
  each, correctness hidden until a selection is made (FR-36–FR-38).
- [ ] The quiz auto-grades to a `correct/total` score, persists once per day, and cannot be
  retaken that day (FR-39, FR-40).
- [ ] The quiz score is readable via the API for `daily-lesson-plan`'s checkpoint to consume
  (FR-41).
