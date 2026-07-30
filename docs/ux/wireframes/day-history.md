# Wireframe: Day History
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-checklist.md

## Purpose
Let the learner browse any previous day's task list and each task's final status, read-only, without risk of altering past history.

## Layout
```
+---------------------------------------------------------------+
| Header: History                                                 |
+---------------------------------------------------------------+
| Day selector:  [Day 1] [Day 2] ... [Day 10] [Day 11]            |
|                (current Day 12 not shown here — see Today's Plan)|
+---------------------------------------------------------------+
| Main: Day 11 — final task list                    🔒 read-only  |
|   [x] Vocabulary  - Work topic, 20 words        (Completed)     |
|   [-] Grammar     - Past Simple                 (Skipped)       |
|   [x] Listening   - 6 Minute English            (Completed)     |
|   [x] Reading     - One passage                 (Completed)     |
|   (each row: skill tag + title + final status + note, if any)  |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Day selector (Day 1 .. current-1) | Lets the learner navigate to any completed day (FR-10) | High |
| Selected day's task list with final status | Core content — what actually happened that day | High |
| Read-only indicator | Communicates clearly that nothing here can be edited, avoiding a false expectation of correcting past entries (ties to Specification's open question on history mutability) | Medium |
| Per-task note (read-only, if present) | Lets the learner recall context they wrote down that day | Medium |

## States
- **Empty**: learner is still on Day 1 with no completed days yet — show "No history yet — finish today to start building it" instead of an empty list with no explanation.
- **Loading**: brief placeholder while the list of past days (or the selected day's detail) loads from local storage.
- **Error**: local data failed to load — same treatment as the Today's Plan screen: distinguish "nothing here" from "something went wrong," and point toward restoring from a backup (Epic-5) if available.
- **Populated**: day selector plus the selected day's read-only task list, as sketched above.
