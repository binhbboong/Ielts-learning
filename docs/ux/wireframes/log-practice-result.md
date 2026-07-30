# Wireframe: Log Practice Result
Supports journey: docs/ux/journeys/solo-ielts-learner-progress-tracking.md

## Purpose
Let the learner record a completed Reading/Listening practice session done outside the app in one short, low-friction sitting, and leave confident the result is saved and won't be lost (journey steps 2-7).

## Layout
```
+---------------------------------------------------------------+
| Header: Log Practice Result                    [ Cancel ]      |
+---------------------------------------------------------------+
| Section: Identity                                              |
|   Skill:   ( ) Reading   ( ) Listening                         |
|   Source:  [ e.g. Cambridge IELTS 17, Test 2, Passage 3      ] |
+---------------------------------------------------------------+
| Section: Result                                                |
|   Score (correct / total):  [ 27 ] / [ 40 ]                    |
|   Time taken:                [ 00:52 ]  (mm:ss or minutes)     |
+---------------------------------------------------------------+
| Section: Diagnosis                                             |
|   Missed question types (tap all that apply):                 |
|     [x] Matching Headings   [ ] True/False/Not Given            |
|     [ ] Sentence Completion [x] Multiple Choice                 |
|     [ ] Summary Completion  [ ] Matching Features                |
|     [ ] Map/Diagram Labeling [ ] Short Answer                    |
|   (list adapts to selected skill: Reading vs Listening types)   |
+---------------------------------------------------------------+
| Section: Note (optional)                                       |
|   [ Free-text: what made it hard / what to revisit ...        ]|
+---------------------------------------------------------------+
| Footer:                              [ Save Result ]           |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Skill selector (Reading / Listening) | Identifies which practice type this record belongs to; also drives which missed-question-type options are offered (journey step 3) | High |
| Source field | Keeps the record specific enough to be useful on later review, e.g. distinguishing recurring weak sources (journey step 3) | Medium |
| Score (correct/total) | Objective, comparable data point that feeds the Progress Trend view — core diagnostic value (journey step 4) | High |
| Time taken | Second objective data point, supports comparing pacing across sessions over time (journey step 4) | High |
| Missed question types (multi-select checklist) | Surfaces the specific weak spot rather than a raw score; this is the field the journey flags as highest drop-off risk (step 5), so it's presented as quick taps, not free recall/typing | High |
| Note (free text) | Captures context while fresh (why it was hard, what to revisit); explicitly optional so it never blocks saving (journey step 6) | Low |
| Save Result action | Primary commit action; must be instant/reliable so the learner trusts the effort is recorded (journey step 7, persona pain point) | High |
| Cancel / back action | Lets the learner exit without saving if they opened the form by mistake or want to abandon a bad entry | Low |
| Entry point (not shown here, precedes this screen) | Must be obvious from wherever the learner lands in-app, since friction here compounds step 1's already-present risk of skipping logging entirely (journey step 2) | High |

## States
- **Empty**: form on first open — no skill selected, score/time/note blank, no missed-question-types checked. Save is enabled regardless of missed-question-types/note selection (both may legitimately be empty), but disabled until Skill, Source, and Score/Total are filled, since those are the minimum viable record.
- **Loading**: not applicable to opening the form itself (it's a local, empty form with no fetch); applies only to the brief moment after tapping "Save Result," where the button shows a saving/disabled state for the duration of the local-storage write (should be near-instant given no backend).
- **Error**: local save fails (e.g. storage quota exceeded or write blocked) — show an explicit inline error near the Save action ("Couldn't save — try again") without clearing any typed field, so the learner never has to reconstruct score, missed types, or notes from memory a second time; Save remains retryable in place.
- **Populated (includes save confirmation)**: two sub-states of the same successful path —
  - *Filled, unsaved*: all entered values visible exactly as typed/selected, Save action enabled, nothing yet persisted.
  - *Saved confirmation*: immediately after a successful save, the form is replaced in place by a brief confirmation ("Result saved — Reading, 27/40") plus a clear next action (e.g. "Log Another" or return to entry point); this is the direct payoff of journey step 7 and the moment that reassures the learner the record persisted without needing to remember to save it themselves.

## Notes on ambiguity
- Exact missed-question-type taxonomy per skill (Reading vs Listening) is not defined in the journey or persona; the checklist above uses illustrative IELTS question-type names as placeholders pending a canonical list.
- Whether "time taken" is entered as mm:ss or a plain minute count is left as an implementation choice; either satisfies the journey's "objective data point" goal (step 4).
