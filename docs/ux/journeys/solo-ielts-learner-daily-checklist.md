# User Journey: Daily Study Checklist Execution
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
It's evening after a full day of work. The learner opens the app to do that day's IELTS study session — they want to see what's assigned for today (Day N of their 180-day plan) and work through it, without needing to consult any external planner. Grounded in `docs/specs/study-plan-execution/Specification.md`.

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Opens the app | Today's Plan screen | Quickly see what's expected today, with zero setup | Low, unless prior progress fails to load — would break trust in the tool immediately |
| 2 | Reviews Day N's task list and statuses | Today's Plan screen | Understand the full scope of tonight's session before starting | Medium — if the list feels long/overwhelming after a tiring workday, the learner may disengage before starting anything |
| 3 | Does the actual study work for a task (e.g. a Reading passage), then returns to the app | Today's Plan screen + external material | Make real progress on the skill, not just check a box | Medium — the learner may finish the work but forget to come back and log it, silently losing credit for effort actually made |
| 4 | Marks the task Completed or Skipped | Today's Plan screen (task item control) | Keep the day's progress count accurate | Low if marking is a single quick action per task |
| 5 | Optionally adds a note to a task | Task detail view | Capture context (why it was hard, what to revisit) while it's fresh | Low — optional, so skipping it doesn't block progress |
| 6 | Repeats steps 3-5 for each remaining task | Today's Plan screen | Get through all of today's assigned work | High — as fatigue builds late in the session, the learner may mark remaining tasks Skipped just to "get through," which quietly undermines the plan's value without the app ever showing that as a problem |
| 7 | Attempts "move to next day" | Today's Plan screen (day-advance action) | Close out today and confirm tomorrow is ready to go | Medium-high — if blocked because a task is still Not Started, unclear feedback here reads as the app being broken rather than a deliberate check |
| 8 | Sees Day N+1 become current | Today's Plan screen (post-transition state) | Feel that tonight's session counted, and see the next day is ready | This is the payoff step — a flat or unclear transition here weakens the daily-return habit the whole feature exists to build |

## Emotional Arc
Starts neutral-to-slightly-reluctant (another study session after work) → steadies through task-by-task execution → risks a frustration spike late in the session if several tasks remain and fatigue sets in (step 6), or if the day-advance action blocks without a clear reason (step 7) → should land on a genuine sense of completion and momentum at step 8, since that payoff is what reinforces the learner coming back tomorrow (Vision goal G-1).

## Success Criteria
- The learner reviews today's plan, works through and marks every task Completed or Skipped, and successfully advances to the next day — all within one sitting, with no confusion about why "move to next day" did or didn't succeed.
- The learner returns the next day and finds Day N+1 waiting as the current day, exactly where they left off, with zero setup — directly serving Vision goal G-1 (executing the plan daily without an external scheduling tool).

## Candidate Screens
- Today's Plan / Daily Checklist screen
- Task detail view (edit description/estimated time, add/edit note)
- Blocked "move to next day" state (feedback on remaining Not Started tasks)
- Day History / previous days (read-only) view
