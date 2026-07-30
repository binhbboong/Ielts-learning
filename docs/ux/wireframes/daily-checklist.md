# Wireframe: Today's Plan / Daily Checklist
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-checklist.md

## Purpose
Let the learner see the current day's assigned tasks, work through them (mark done/skipped, add notes, tweak details), and explicitly close out the day once every task is resolved.

## Layout
```
+---------------------------------------------------------------+
| Header: Day 12 of 180              Progress: 2 / 6 tasks done  |
+---------------------------------------------------------------+
| Nav: [Today] [History] [Vocabulary] [Mistakes] [Progress] ...  |
+---------------------------------------------------------------+
| Main: Task List (current day)                                  |
|   [x] Vocabulary   - Work topic, 20 words        (Completed)   |
|   [ ] Grammar      - Present Perfect              (Not Started)|
|   [ ] Listening    - 6 Minute English             (Not Started)|
|   [-] Reading      - One passage                  (Skipped)    |
|   [ ] Speaking     - Describe your job            (Not Started)|
|   [ ] Review       - 15 words due                 (Not Started)|
|   (each row: status control + skill tag + title + note icon)   |
+---------------------------------------------------------------+
| Footer: [ Move to Next Day ]  <- disabled, with reason shown    |
|         "3 tasks still Not Started"                            |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Day indicator ("Day 12 of 180") | Orient the learner in the overall 180-day plan (FR-2) | High |
| Progress count ("2/6 tasks done") | Immediate, low-effort read on today's status (FR-9) | High |
| Task list | Core content — every task assigned to the current day (FR-1, FR-2) | High |
| Per-task status control (Not Started / Completed / Skipped) | Primary action of the whole screen (FR-3) | High |
| Per-task skill tag (Grammar, Vocabulary, etc.) | Lets the learner scan by skill at a glance (FR-1) | Medium |
| Per-task note indicator/entry point | Surfaces that a note exists, and opens Task detail to add/edit one (FR-4) | Medium |
| Task row → Task detail entry point | Route to edit description/estimated time and notes (FR-4, FR-5) | Medium |
| "Move to Next Day" action | Gate that closes today and advances the plan (FR-6, FR-8) | High |
| Blocked-reason message | Explains why the action is disabled when tasks remain unresolved (FR-7) — the journey flagged unclear feedback here as a high drop-off risk | High |
| Nav entry to History | Route to the read-only previous-days view (FR-10) | Medium |

## States
- **Empty**: current day has zero assigned tasks (edge case in the pre-loaded plan) — show "No tasks scheduled for today" and allow "Move to Next Day" immediately, since there's nothing to resolve.
- **Loading**: brief placeholder/skeleton rows while the current day's plan and task statuses are read from local storage on screen entry.
- **Error**: local data failed to load (e.g. storage blocked or corrupted) — show an explicit message distinguishing "nothing to show" from "something went wrong," since there is no server to silently retry against; point the learner toward restoring from a backup (Epic-5) if available.
- **Populated**: the happy path shown in the layout above — full task list with per-task status, progress count accurate, "Move to Next Day" enabled only once every task is Completed or Skipped.
- **Move-to-next-day blocked** (interaction state, not a page state): learner attempts the action while tasks remain Not Started — action stays visible but disabled, with the blocked-reason message naming which/how many tasks are still unresolved (FR-7), rather than failing silently.
