# Wireframe: Vocabulary Review Session
Supports journey: docs/ux/journeys/solo-ielts-learner-vocabulary-review.md (steps 3-8)

## Purpose
Walk the learner through today's due words one at a time — recall the meaning before it's revealed, honestly self-assess, let the app reschedule and advance automatically — and deliver an unambiguous closure signal once the queue is cleared.

## Layout
```
+---------------------------------------------------------------+
| Header: Vocabulary Review          Word 4 of 12 due  [====----] |
|         Day 47 of 180                                           |
+---------------------------------------------------------------+
| Nav: [Today] [Vocabulary] [Mistakes] [Progress] ...              |
+---------------------------------------------------------------+
| Main: Recall Card (one word at a time)                          |
|                                                                  |
|    Topic: [Work]                                                |
|                                                                  |
|         RESILIENT                                               |
|                                                                  |
|    (meaning hidden — recall it before revealing)                |
|                                                                  |
|         [ Reveal Answer ]                                       |
|                                                                  |
|    -- once revealed --                                          |
|    Meaning: able to recover quickly from difficulties           |
|    Example: "The team stayed resilient after the setback."      |
|                                                                  |
|    Be honest — this decides your next review date:              |
|         [ Forgot ]              [ Remembered ]                  |
|                                                                  |
+---------------------------------------------------------------+
| Footer: + Add a word I just noticed  (opens inline, no exit)     |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Queue progress indicator ("Word 4 of 12", progress bar) | Shows the queue visibly shrinking — the main driver of the mid-session confidence rebuild in the emotional arc (steps 6-7) | High |
| Word/topic display, meaning hidden | The Recall Prompt itself — forces active recall instead of passive re-reading (step 3) | High |
| "Reveal Answer" control | Learner-paced switch from self-test to check — keeps recall honest by not showing the answer automatically (step 3→4) | High |
| Revealed meaning + example | What the learner checks their own recall against (step 4, Answer Revealed) | High |
| Self-assessment control (Forgot / Remembered) | The single decision that drives the spaced-repetition reschedule; framed as "be honest" to counter the dishonest-shortcut risk named in the journey (step 5) | High |
| Auto-advance to next word | Removes any manual step from the interval logic so the learner just trusts it (step 6) | High |
| Immediate per-word save (behavior, not a visible control) | Persists each assessment the instant it's made, before advancing — so an interruption never loses an already-completed word (step 7 risk) | High |
| Day/plan context ("Day 47 of 180") | Light orientation in the overall 180-day plan without competing with the recall card | Low |
| "Add a word I just noticed" (footer) | Captures a new word without abandoning the in-progress session, addressing the related drop-off risk in step 9 of the journey | Low |
| Section nav | Wayfinding to other areas of the app | Low |

## States
- **Empty**: learner opens this screen with zero words due (e.g., already cleared today's queue, or arrived here directly with nothing scheduled) — no recall card is shown; instead an explicit "Nothing due right now" message with a route back to the Dashboard / Vocabulary Due List. Distinct from "Session complete" below, which is a state you arrive at *by finishing*, not by finding nothing to do.
- **Loading**: brief placeholder while the due queue and word data are read from local storage on entry. If a prior session was left mid-queue (interruption), this is where it's detected: the screen resumes silently at the exact next unreviewed word — no "start over," no re-showing words already assessed. This is the direct mitigation for the step 7 interruption/resume risk.
- **Error**: local read/write failed (storage blocked, corrupted schedule data) — the due queue or reschedule state can't be trusted, so no recall card is shown speculatively. Message explicitly distinguishes "nothing due" from "something went wrong," and points toward restoring from a backup (Epic-5), since there is no server to silently retry against.
- **Populated**: the core loop shown in Layout above — Recall Prompt → Answer Revealed → Self-Assessment → auto-advance, repeating per due word, progress indicator ticking up after each one. Every Forgot/Remembered choice is saved immediately, before the next word loads.
- **Session complete**: triggered the instant the last due word is assessed and the queue empties (step 8) — the main content area swaps the recall card for a Review Complete Summary sub-view:
  ```
  +---------------------------------------------------------------+
  | Main: Review Complete                                          |
  |                                                                  |
  |    All 12 words due today — reviewed.                           |
  |                                                                  |
  |    Remembered: 9      Forgot: 3                                  |
  |    Next review dates updated automatically.                     |
  |                                                                  |
  |    [ Back to Today ]        [ + Add a word ]                    |
  +---------------------------------------------------------------+
  ```
  This is the emotional-arc peak of the journey, so it must read as a deliberate, unmistakable "done" — explicit count reviewed, a remembered/forgot breakdown (closing the loop on the honesty ask from step 5), and confirmation the schedule was updated — rather than the screen just quietly emptying out.
