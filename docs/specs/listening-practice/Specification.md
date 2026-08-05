# Specification: AI-Generated Listening Practice & Auto-Scoring
Related UX: docs/ux/prototypes/daily-lesson-flow.md, docs/ux/wireframes/listening-exercise.md, docs/ux/wireframes/mistake-quick-add.md

## Revision 2 — Multi-section, real question-type catalog, scaled by band tier

Decision: `docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md`. Supersedes the prior
Out-of-Scope exclusions of non-multiple-choice question types and more than one script per day.

- FR-16: The system MUST generate Listening content structured into a phase-tier-appropriate
  number of sections (beginner = 1, standard = 2, advanced = 4), each with its own script, audio,
  and context type (social_conversation, monologue, educational_discussion, academic_lecture)
  matching the real exam's four-section progression — superseding FR-1's "one Listening script."
- FR-17: Each section's questions MUST be typed per this catalog: Multiple Choice, Form/Note/
  Table Completion, Matching, Plan/Map/Diagram Labelling (a letter-labelled textual description
  in lieu of an image). Beginner tier is limited to Multiple Choice + simple Note Completion;
  standard tier adds Matching + Table Completion; advanced tier includes the full catalog.
- FR-18: A question of a completion type MUST record one or more accepted-answer strings at
  generation time instead of a fixed option list, preserving FR-3's AI-call-free scoring
  guarantee.
- FR-19: A question grouped with others under shared instructions MUST carry those instructions
  for display above the group.
- FR-20: Total question count and target time MUST scale with tier — beginner ~6-8 questions /
  ~10-20 min, standard ~20 questions across 2 sections / ~20 min, advanced 40 questions across 4
  sections / ~30-40 min — driving the Listening minutes allocated by Epic-1 for that day.
- FR-21: Free-text (completion) answers MUST be scored by case-insensitive, whitespace-normalized
  comparison against the recorded accepted-answer strings, with no additional AI call.
- FR-22: The learner's active tier for a given day's Listening generation MUST be derived from
  the same phase mapping used for Reading/Writing/Speaking prompt complexity.
- FR-23: Standard and advanced tier Listening MUST display a non-blocking countdown timer per
  section based on FR-20's target time; it MUST NOT auto-submit or lock the exercise at zero
  (beginner tier shows no timer).
- FR-24: Each section MUST have its own independently playable/replayable audio (unlimited replay,
  unchanged from FR-4) rather than a single player for the whole day's exercise.

## Status
Draft

## Overview
This feature generates a Listening script and a set of multiple-choice comprehension questions
targeted at the day's Listening personalization focus (supplied by the Daily Personalized
Lesson Plan, PRD Epic-1), converts the script into audio the learner can play, and scores the
learner's answers immediately and objectively once submitted — the same auto-scoring property
as Reading Practice (Epic-9). Each result feeds the learner's progress trend (Epic-4) and
offers the same one-action Mistake Notebook logging path as Epic-9.

This feature did not exist before the PRD revision that introduced it, for the same reason as
Epic-9: Listening practice was previously assumed to happen outside the app. It additionally
introduces a capability the product has not needed before — converting generated text into
playable audio — which the user journey (`docs/ux/journeys/solo-ielts-learner-daily-lesson.md`)
flags as the single highest-risk new interaction in the daily lesson flow: if audio fails to
load or play, the learner is fully blocked on this skill for the day.

It corresponds to PRD Epic-10 and traces to Vision goals G-1, G-2, and G-5.

## User Scenarios
- As the learner, I want a Listening script with audio ready for me each day, so I never have
  to find my own Listening material.
- As the learner, I want to play, pause, and replay the audio as many times as I want while
  answering, since this is practice, not an exam simulation.
- As the learner, I want to know immediately how many questions I got right, without waiting.
- As the learner, I want to read the transcript after I've submitted, to review what I
  actually heard.
- As the learner, if the audio itself fails to load, I want that failure to be obvious and
  retryable right where the player is, not a confusing dead end.

## Functional Requirements
- FR-1: The system MUST generate one Listening script (a short spoken-style passage) and a set
  of multiple-choice comprehension questions targeted at the day's Listening personalization
  focus supplied by the Daily Personalized Lesson Plan feature (Epic-1).
- FR-2: The system MUST convert the generated script into playable audio before the exercise is
  marked Ready on the daily overview (Epic-1 FR-4) — a script without playable audio is not a
  usable exercise.
- FR-3: Each generated question MUST have exactly one correct answer recorded at generation
  time, so scoring never requires an additional AI call.
- FR-4: The learner MUST be able to play, pause, and replay the audio an unlimited number of
  times before submitting answers.
- FR-5: The transcript MUST NOT be visible to the learner before they submit their answers, so
  it cannot substitute for actually listening.
- FR-6: The learner MUST be able to answer all questions and submit them in a single action.
- FR-7: On submission, the system MUST score the learner's answers immediately, without any
  additional AI call, and display for each question whether the learner's answer was correct
  and, if not, the correct answer — matching Epic-9's result presentation.
- FR-8: The system MUST display an overall score (correct count out of total) alongside the
  per-question review.
- FR-9: After submission, the system MUST reveal the full script transcript for the learner to
  review.
- FR-10: For each incorrect answer, the system MUST offer the same one-action Mistake Notebook
  logging path as Epic-9 FR-7.
- FR-11: Each Listening result MUST be recorded so it contributes to the learner's progress
  trend (Epic-4).
- FR-12: If script/question generation succeeds but audio conversion fails, the system MUST
  report a failure state scoped to the audio player specifically (not a generic full-exercise
  failure), and retrying MUST reuse the already-generated script rather than regenerating it
  from scratch, so a successful script generation is never discarded just because audio
  conversion failed afterward.
- FR-13: If script/question generation itself fails (before audio conversion is attempted), the
  system MUST report a distinct failure state and support retry using the same personalization
  focus, consistent with Epic-1's retry contract.
- FR-14: Once generated for a given day, a Listening script, its audio, and its questions MUST
  NOT change — re-opening the exercise before submission MUST present the same script/audio/
  questions, and after submission MUST show the same result.
- FR-15: The learner's data export (Epic-5) MUST include the actual generated audio file for
  each day's Listening exercise, not only the script text — consistent with Epic-5's guarantee
  that the learner is never locked into this application's AI/Text-to-Speech vendor.

## Out of Scope
- Question types other than multiple-choice — same simplification as Epic-9.
- A countdown timer, a play-once restriction, or other exam-condition constraints — this is a
  practice tool, not a mock-test simulator; replay is deliberately unlimited (see
  `docs/ux/prototypes/daily-lesson-flow.md`'s Decisions Record).
- More than one Listening script per calendar day.
- Multiple speaker voices, accents, or dialogue-specific audio staging beyond a single
  generated voice reading the script — a V1 simplification; not excluded permanently, just not
  designed here.
- Manual creation/import of a Listening script or audio file by the learner.

## Open Questions
None — resolved with the user: the export includes the actual audio file (FR-15).

## Acceptance Criteria
- [ ] A Listening script and questions are generated, and audio is playable, before the
      exercise is marked Ready on the daily overview (FR-1, FR-2).
- [ ] The audio can be played, paused, and replayed without limit before submission (FR-4).
- [ ] The transcript is not visible before submission and becomes visible immediately after
      (FR-5, FR-9).
- [ ] Submitting answers produces an immediate score and per-question correct/incorrect
      breakdown (FR-7, FR-8).
- [ ] Each incorrect answer offers the same pre-filled Mistake Notebook action as Reading
      Practice (FR-10).
- [ ] A completed Listening result appears in the learner's progress trend view (FR-11).
- [ ] Forcing an audio-conversion failure (with script generation succeeding) shows a
      player-scoped failure state, and retry does not re-request script generation (FR-12) —
      verified by confirming the retried request only re-attempts audio conversion.
- [ ] Forcing a script-generation failure shows a distinct failure state with working retry
      using the same personalization focus (FR-13).
- [ ] Re-opening a completed day's Listening exercise shows the identical script, audio, and
      result as originally generated/submitted (FR-14).
- [ ] An exported data file includes the actual audio file for a completed day's Listening
      exercise, not just its transcript text (FR-15).
