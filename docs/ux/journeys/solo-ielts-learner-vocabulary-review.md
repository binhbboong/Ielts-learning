# User Journey: Evening Vocabulary Review (Spaced Repetition)
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
It's evening and the learner sits down for their daily study session. Some vocabulary words are due for review today under the spaced-repetition schedule, and the learner works through them one at a time using self-check recall (recall the meaning before revealing it), then optionally logs one new word they picked up along the way.

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Opens the app for tonight's session and sees how many words are due | Dashboard / Today Overview | Pick up exactly where they left off with minimal friction, and see what's due without hunting for it (pain point: "review lapses without a system that surfaces exactly what's due") | Low — the due count is surfaced immediately on landing |
| 2 | Opens the vocabulary review flow and sees the size of today's due queue | Vocabulary Due List | Confirm the scope of tonight's review before committing time to it | Medium — after a missed day or two the due count can look large, and the session feels like a chore before it even starts, tempting the learner to defer it (undermining "on schedule via spaced repetition") |
| 3 | Starts the session; first due word is shown with only the word/topic, meaning hidden | Vocabulary Review Session — Recall Prompt | Self-test active recall rather than passively re-reading the answer | Low |
| 4 | Tries to recall the meaning mentally, then reveals the answer | Vocabulary Review Session — Answer Revealed | Check their own recall against the actual meaning/example | Low |
| 5 | Marks the outcome honestly: remembered or forgot | Vocabulary Review Session — Self-Assessment control | Log the genuine outcome so the schedule adapts correctly, rather than fudging it to finish faster | Medium — forgetting several words in a row is discouraging and creates a temptation to mark "remembered" dishonestly just to move on, which quietly breaks the spaced-repetition schedule it depends on |
| 6 | App reschedules the word to its next interval and advances to the next due word automatically | Vocabulary Review Session (queue advances) | Trust the interval logic (1/3/7/14/30-day pattern) without manually recalculating anything | Low |
| 7 | Repeats the recall → reveal → self-assess loop for each remaining due word | Vocabulary Review Session | Clear the entire due queue in one sitting, in one focused, low-cognitive-load flow | Medium — a study session can be interrupted (tiredness after a full workday, an evening interruption), leaving the queue partly done; the flow needs to resume cleanly rather than losing progress |
| 8 | Reviews the last due word and sees a clear end-of-session signal | Review Complete Summary | Get a concrete closure signal that today's vocabulary obligation is fully met | Low |
| 9 | (secondary) Notices a new word worth keeping and opens the add-word form, ideally without leaving the review context | Add Vocabulary Word screen | Capture new vocabulary in the moment before forgetting it, so it enters future review cycles | Low-medium — if adding a word requires abandoning the review flow entirely, the learner may decide to "do it later" and never come back to it |
| 10 | (secondary) Fills in word, meaning, example, and topic, then saves it | Add Vocabulary Word screen — save confirmation | Get the new word onto the spaced-repetition schedule (starting at the 1-day interval) with no extra setup | Low |

## Emotional Arc
Mild reluctance/inertia at the very start if the due queue looks large (step 2) — this is the main "chore" moment the persona's willpower-dependence pain point is meant to solve. Engagement rises during the recall → reveal loop, which feels like quick, low-friction progress. The lowest point is mid-session if several words are forgotten in a row (step 5) — a real risk of discouragement that could tempt the learner to either quit early or misreport results. Confidence rebuilds as the due count visibly shrinks with each word, and the arc peaks with a clear sense of relief/accomplishment at the "all reviewed" confirmation (step 8) — a deliberately designed moment of closure, since this is the tangible signal that retention isn't being left to memory or willpower alone. Adding a new word afterward (steps 9-10) is a small, low-stakes moment of satisfaction, not a tense one.

## Success Criteria
- The persona clears every word due that day in a single sitting (steps 1-8, realistically well under 10 minutes for a typical daily queue), without needing to remember or manually figure out what's due, and without the session feeling effortful enough to skip — directly supporting G-3 and the ≥80%-of-due-vocabulary-reviewed-on-schedule metric.
- If a new word is captured mid-session (steps 9-10), it is saved with all four fields (word, meaning, example, topic) and enters the review schedule immediately, in under 30 seconds, without derailing the in-progress review queue.

## Candidate Screens
- Dashboard / Today Overview
- Vocabulary Due List
- Vocabulary Review Session
- Review Complete Summary
- Add Vocabulary Word
