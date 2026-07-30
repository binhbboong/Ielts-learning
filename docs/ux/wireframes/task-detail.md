# Wireframe: Task Detail
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-checklist.md

## Purpose
Let the learner view and edit everything about one task — its status, description, estimated time, and note — reached from a task row on the Today's Plan / Daily Checklist screen.

## Layout
```
+---------------------------------------------------------------+
| Header: Task Detail — Grammar: Present Perfect       [Close]   |
+---------------------------------------------------------------+
| Main:                                                          |
|   Skill: Grammar                          (read-only)          |
|                                                                  |
|   Status:  ( ) Not Started  ( ) Completed  ( ) Skipped          |
|                                                                  |
|   Description:                                                  |
|   [ editable text -------------------------------------- ]     |
|                                                                  |
|   Estimated time:  [ 30 ] minutes         (editable)            |
|                                                                  |
|   Note:                                                          |
|   [ editable text area, multi-line ---------------------- ]     |
+---------------------------------------------------------------+
| Footer: [ Save ]   [ Cancel ]                                    |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Skill tag (read-only) | Orients the learner to which skill this task belongs to | Medium |
| Status selector (Not Started / Completed / Skipped) | Same control as the checklist row — lets status be changed from here too (FR-3) | High |
| Description field | Edit the task's own description when the pre-loaded plan doesn't quite fit (FR-5) | High |
| Estimated time field | Edit the task's own time estimate (FR-5) | Medium |
| Note field | Add/edit free-text context for later review (FR-4) | High |
| Save action | Commit changes back to the task | High |
| Cancel/Close action | Discard unsaved edits and return to the checklist | Medium |

## States
- **Empty**: task has no note yet — note field shows placeholder text (e.g. "No note yet") rather than looking broken or pre-filled with junk.
- **Loading**: brief placeholder while the task's current data loads from local storage.
- **Error**: a save fails (e.g. local storage write blocked) — show an inline error next to Save and keep the learner's edits on screen rather than discarding them, since there's no server to silently retry against.
- **Populated**: form pre-filled with the task's current skill, status, description, estimated time, and note, as sketched above.
