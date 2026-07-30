# Specification: Vocabulary & Spaced Repetition Review
Related UX: docs/ux/prototypes/vocabulary-review-flow.md

## Status
Draft

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
- FR-10: When no words are due, the system MUST present this as a neutral, positive state (the
  learner is on schedule) rather than an empty or broken-looking screen, and MUST NOT offer a
  "start review" action when there is nothing to review.
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
- AI-generated or AI-suggested vocabulary (words the learner did not enter themselves).
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
- [ ] With zero words due, no "start review" action is offered and the state reads as a positive
  milestone (FR-10).
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
