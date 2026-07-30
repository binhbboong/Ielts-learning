# Specification: 180-Day Study Plan & Daily Execution
Related UX: none (no wireframe/prototype exists for this slug)

> **Superseded.** This spec's premise (a fixed 180-day plan of learner-authored/pre-loaded checklist items, with no generated lesson content) assumed the "self-directed progress tracker" product framing. That framing was superseded by the Vision revision described in `docs/business/Vision.md` (revision 3), which reframes the product around AI-generated, continuously-personalized daily lessons across all four skills. See the successor spec: `docs/specs/daily-lesson-plan/Specification.md` (PRD Epic-1, "Daily Personalized Lesson Plan"). Kept here for history — do not implement against this version. The implementation already built against this spec (the `study-plan` Angular module and `app/routers/study_plan.py` backend) remains in place and functioning; whether/how it gets adapted vs. replaced is a decision for the successor spec's `/spec:plan`, not this document.

## Status
Draft

## Overview
A learner following a 180-day IELTS self-study plan needs to know, at any moment, which day they're on and exactly what to do today — without consulting an external scheduler. This feature gives them a pre-loaded day-by-day plan (each day made up of tasks tagged by skill: Grammar, Vocabulary, Listening, Reading, Speaking, Writing, Review), a way to work through and mark today's tasks, light editing of a task's own details when the pre-loaded plan doesn't quite fit, and explicit control over when they move on to the next day. It corresponds to PRD Epic-1 (`docs/business/PRD.md`) and traces to Vision goal G-1.

## User Scenarios
- As a learner, I want to see which day of my 180-day plan I'm on and what tasks are assigned for today, so I can execute my study session without an external planner.
- As a learner, I want to mark each of today's tasks as completed or skipped, so my daily progress is accurately tracked.
- As a learner, I want to add a note to a task, so I can record context (e.g. why it was hard, what I noticed) for later review.
- As a learner, I want to adjust a task's description or estimated time when the pre-loaded plan doesn't quite fit my pace, so the plan stays realistic for me.
- As a learner, I want to move on to the next day only when I explicitly choose to, so I'm never auto-advanced past work I haven't finished or reviewed.
- As a learner, I want to look back at previous days' tasks and their final status, so I can review my history.

## Functional Requirements
- FR-1: The system MUST come pre-loaded with a 180-day study plan in which every day has one or more tasks, each tagged with exactly one skill (Grammar, Vocabulary, Listening, Reading, Speaking, Writing, or Review).
- FR-2: The system MUST display, for the current day, the full list of tasks assigned to that day along with each task's status (Not Started, Completed, or Skipped).
- FR-3: The system MUST allow the learner to set a task's status to Completed or Skipped, and to revert either back to Not Started.
- FR-4: The system MUST allow the learner to add or edit a free-text note on any individual task.
- FR-5: The system MUST allow the learner to edit a task's description and estimated time.
- FR-6: The system MUST NOT automatically change which day is "current" — the current day advances only when the learner performs an explicit "move to next day" action.
- FR-7: The system MUST block the "move to next day" action, with clear feedback, while any task on the current day is still in Not Started status.
- FR-8: The system MUST allow "move to next day" to succeed once every task on the current day is Completed or Skipped, at which point the next day in the plan becomes the current day.
- FR-9: The system MUST display a completed-vs-total task count for the current day (e.g., "2/6") that updates immediately whenever a task's status changes.
- FR-10: The system MUST allow the learner to view any previous day's task list and each task's final status, in read-only form.
- FR-11: The system MUST persist all plan and task state (status, notes, edited description/time, current day) across sessions, so a browser restart or app reload does not lose progress.
- FR-12: [NEEDS CLARIFICATION: Should a past day's task ever be re-editable (status, note) after the learner has moved beyond it, e.g. to correct a mis-marked task — or is history strictly immutable once the day is no longer current?]

## Out of Scope
- Any aggregation from other epics on this feature's screen — study streak, vocabulary due-today count, weakest-skill indicator, and recent Reading/Listening scores belong to their own epics' specs (Epic-2, Epic-3, Epic-4) and are not part of this feature.
- Learner-authored plans: the 180-day plan's day/task structure is pre-loaded; adding an entirely new day or a new task slot beyond what's pre-loaded is out of scope (editing an existing task's own description/time, per FR-5, is in scope).
- AI-generated or dynamically-adjusted plan content of any kind.
- Multi-user or shared plans.
- Backup, export, or import of this feature's data — that is Epic-5's responsibility.
- Notifications or reminders about the current day's tasks.

## Open Questions
- [NEEDS CLARIFICATION: see FR-12 — mutability of past-day task status/notes after the day is no longer current.]

## Acceptance Criteria
- [ ] On load, the learner sees the current day's task list with each task's correct skill tag and status.
- [ ] The learner can set a task's status to Completed, to Skipped, and back to Not Started.
- [ ] The learner can add and edit a note on a task.
- [ ] The learner can edit a task's description and estimated time.
- [ ] "Move to next day" is blocked, with clear feedback, while any current-day task is Not Started.
- [ ] "Move to next day" succeeds once every current-day task is Completed or Skipped, and the displayed current day advances.
- [ ] The completed/total count for the current day is correct immediately after every status change.
- [ ] Previous days' task lists and final statuses remain viewable, read-only, after the day advances.
- [ ] All plan/task state (status, notes, edits, current day) survives a full browser/app restart.
