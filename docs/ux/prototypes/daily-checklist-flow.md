# Prototype: Daily Study Checklist Flow
Journey: docs/ux/journeys/solo-ielts-learner-daily-checklist.md

## Screen Sequence
1. docs/ux/wireframes/daily-checklist.md — triggered by: learner opens the app (default landing screen)
2. docs/ux/wireframes/task-detail.md — triggered by: learner selects a task row on the Daily Checklist screen
3. docs/ux/wireframes/daily-checklist.md — triggered by: Save or Cancel on Task Detail (returns updated or unchanged)
4. docs/ux/wireframes/day-history.md — triggered by: learner selects "History" from the nav on the Daily Checklist screen (side branch — not required to reach the journey's success criteria)

## Transitions
| From | Trigger | To |
|---|---|---|
| (app entry) | Learner opens the app | Daily Checklist, populated with the current day |
| Daily Checklist | Learner selects a task row | Task Detail (for that task) |
| Daily Checklist | Learner sets a task's status directly on its row (without opening Task Detail) | Daily Checklist, same screen — status and progress count update in place |
| Task Detail | Learner taps Save | Daily Checklist, with the task's updated status/description/time/note reflected |
| Task Detail | Learner taps Cancel/Close | Daily Checklist, unchanged |
| Daily Checklist | Learner taps "Move to Next Day" while at least one task is Not Started | Daily Checklist, blocked state — reason shown naming the unresolved task(s) |
| Daily Checklist | Learner taps "Move to Next Day" once every task is Completed or Skipped | Daily Checklist, re-rendered for Day N+1 as the new current day |
| Daily Checklist | Learner selects "History" in the nav | Day History, defaulted to the most recently completed day |
| Day History | Learner selects a different day in the day selector | Day History, same screen — read-only task list for the newly selected day |
| Day History | Learner selects "Today" in the nav | Daily Checklist |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow. Journey steps 1-2 (open, view today's tasks) → Daily Checklist; steps 3-5 (do the work, mark status, add a note) → Daily Checklist + Task Detail; step 6 (repeat) → the loop between those two screens; step 7 (attempt move to next day) → Daily Checklist blocked/allowed transition; step 8 (Day N+1 becomes current) → Daily Checklist re-render.
- [x] Every transition has a clear, unambiguous trigger — see table above; no "eventually gets to" steps.
- [ ] No screen exists in this flow without a stated purpose from the journey — **partially met**: Day History has a clear purpose from the Specification (FR-10) and its own wireframe, but the source journey never actually walks a step through it (it was listed only as a candidate screen). Not a blocker, but flagged below rather than silently treated as fully covered.
- [x] Open UX questions are listed below, not silently resolved.

## Open Questions
- [NEEDS CLARIFICATION: Is reviewing Day History expected to be part of *this* journey's success path, or is it a supporting feature reached outside the "close out today" scenario? No journey step currently walks through it — if it matters for success criteria, the journey may need a follow-up step added.]
- [NEEDS CLARIFICATION: carried over from Specification.md FR-12 — if past-day task status/notes ever become editable, Day History's read-only-only flow would need a new transition (e.g. an edit trigger), which this prototype does not currently define.]
