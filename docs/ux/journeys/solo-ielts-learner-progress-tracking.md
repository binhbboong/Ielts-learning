# User Journey: Logging Practice Results & Reviewing the Progress Trend
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
The learner has just finished a Reading or Listening practice session using material outside the app (a book, a website, an audio track) and wants to log the result before the details fade. Separately — not necessarily the same sitting — they open the app specifically to check whether their scores are actually trending up. This journey walks both halves of the loop, since checking the trend is the payoff that makes logging worthwhile (Vision goal G-4). Grounded in PRD Epic-4 (Practice Result Tracking & Progress Visibility); no dedicated Specification.md exists yet for this epic.

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Finishes a Reading/Listening practice session done outside the app, decides to log it | External material (book/website/audio) — pre-app | Capture a real result before the details (score, missed items) fade from memory | Medium — the actual studying is already "done," so logging can feel like unrewarded extra admin and get skipped entirely, silently losing the data point |
| 2 | Opens the app and starts a new practice result entry | Log Practice Result screen | Get straight to logging without hunting for where to do it | Low-medium — if the entry point isn't obvious, friction here compounds step 1's risk of just not bothering |
| 3 | Selects the skill (Reading or Listening) and names the source | Log Practice Result screen (skill/source fields) | Keep the record specific enough to be useful when reviewed later | Low |
| 4 | Enters the score (number correct out of total) and time taken | Log Practice Result screen (score/time fields) | Record an objective, comparable data point rather than a vague impression | Low |
| 5 | Tags which question types were missed | Log Practice Result screen (missed question types field) | Surface the specific weak spot, not just a raw score | Medium — recalling exact question types after the fact takes effort; skipping this field is tempting and quietly guts the diagnostic value (persona goal: catch recurring mistakes before they become habits) |
| 6 | Adds an optional free-text note | Log Practice Result screen (note field) | Capture context (why it was hard, what to revisit) while it's fresh | Low — optional, so skipping doesn't block saving |
| 7 | Saves the result | Log Practice Result screen -> confirmation | Trust the effort is recorded and won't be lost | Low, provided save is instant and reliable (persona pain point: progress must persist without needing to remember to save) |
| 8 | On a later visit, opens the app specifically to check progress | Progress Trend view | See whether Reading/Listening is actually improving, not just guess | Medium — if this view isn't easy to find/return to, the "check-in" habit itself lapses and the whole point of logging goes unrealized |
| 9 | Reviews average score and trend direction across recent sessions | Progress Trend view (score trend chart) | Get an objective, feeling-independent signal of momentum (Vision G-4) | High — a flat or declining trend, shown without constructive framing, can read as discouraging failure rather than useful signal, making the learner less likely to log the next session |
| 10 | Reviews which question types are missed most often across sessions | Progress Trend view (missed-question-type breakdown) | Identify a specific weak area to prioritize in the next study session | Low — this is the constructive payoff intended to offset step 9's risk, turning a flat score into an actionable "focus on X next" |

## Emotional Arc
Starts with the quiet satisfaction of having actually done the practice → dips into mild reluctance at step 1-2, since logging is "extra" after the real work is already finished → steadies through efficient, low-friction data entry (steps 3-7) → relief at the confirmed save → on the later return, anticipation (sometimes anxiety) opening the trend view → risk of a discouragement dip at step 9 if the trend is flat or down and isn't framed constructively → should resolve into clarity and direction at step 10, where a specific weak area gives the learner something concrete to act on rather than just a verdict. Step 10 is the true payoff for Vision G-4 and should land as motivating, not deflating.

## Success Criteria
- The learner logs a completed Reading/Listening result (skill, source, score, time taken, missed question types, note) in a single short sitting immediately after finishing practice, with the record confirmed saved — without needing to reconstruct forgotten details later.
- Within the first 8 weeks, after logging 4+ practice sessions, the learner can open the Progress Trend view and, without any calculation of their own, see the average score trend (up/stable/down) and which question types are missed most often — directly satisfying the Vision success metric for G-4, without falling back on the pain point of "no clear signal over time on whether Reading/Listening skills are actually improving."

## Candidate Screens
- Log Practice Result screen (skill, source, score, time, missed question types, note)
- Result saved confirmation state
- Practice Log / history list (past logged results)
- Progress Trend view (average score + trend direction over time)
- Missed question-type breakdown view
