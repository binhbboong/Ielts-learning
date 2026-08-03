# Tasks: Daily Personalized Lesson Plan
Plan: docs/specs/daily-lesson-plan/ImplementationPlan.md

## Revision-4 Task-18 — Scheduled pre-generation job
- [x] Status: Done
- Depends on: Revision-3 Task-15 (effective-day/`get_effective_day`)
- Goal: `pregenerate_upcoming_days` (effective day + 1, reusing `ensure_today_generated`'s
  existing per-skill idempotency) and `pregenerate_for_all_learners` (iterates `StudyProfile`
  rows only — never creates one; isolates each learner's failure in its own try/except so one
  outage doesn't block the rest of the batch). New `GET /api/cron/pregenerate-lessons`, guarded
  by `verify_cron_secret` (compares `Authorization: Bearer <CRON_SECRET>` against the configured
  secret; rejects when unset or mismatched). Wired into `backend/vercel.json`'s `crons` array at
  `0 1 * * *` (01:00 UTC = 08:00 `Asia/Ho_Chi_Minh`).
- Files touched: `backend/app/services/daily_lesson_plan.py`,
  `backend/app/routers/cron.py`, `backend/app/main.py`, `backend/app/core/config.py`,
  `backend/app/schemas/daily_lesson_plan.py`, `backend/vercel.json`, `backend/.env.example`,
  `backend/app/services/daily_lesson_plan_test.py`, `backend/tests/test_cron_router.py`.
- Definition of done: `test_pregenerate_upcoming_days_generates_effective_day_and_the_next`,
  `test_pregenerate_upcoming_days_skips_already_generated_content`,
  `test_pregenerate_for_all_learners_only_processes_existing_profiles`,
  `test_pregenerate_for_all_learners_continues_after_one_learner_fails`, and all 3
  `test_cron_router.py` auth/success cases pass. Covers FR-19 through FR-22.

## Revision-3 Task-15 — All-4-skills-daily + checkpoint evaluation + effective-day gating
- [x] Status: Done
- Depends on: vocabulary-review Revision-4 Task-24 (quiz mode, checkpoint input)
- Goal: Replace the 2-skill weekday rotation (`_DAILY_ROTATION`) with all 4 skills generating
  every effective day (`ALL_SKILLS`, `_PRIMARY_SKILL_BY_WEEKDAY` for minute weighting only);
  add `evaluate_skill_checkpoint`/`evaluate_checkpoint` (Reading/Listening ≥80%, Writing/Speaking
  ≥`minimum_skill_band`, vocab quiz ≥80%); add `get_effective_day` (scans from `start_date`,
  capped at real `today`, no persisted pointer) and wire `get_overview`/`ensure_today_generated`
  to operate on it instead of literal `today`.
- Files touched: `backend/app/services/daily_lesson_plan.py`,
  `backend/app/schemas/daily_lesson_plan.py`, `backend/app/routers/daily_lesson_plan.py`,
  `backend/app/services/daily_lesson_plan_test.py`, `backend/tests/test_daily_lesson_plan_router.py`.
- Definition of done: `test_ensure_today_generated_creates_all_four_skills_on_first_call`,
  `test_effective_day_does_not_advance_past_an_incomplete_checkpoint`,
  `test_effective_day_advances_once_checkpoint_fully_passed`,
  `test_evaluate_checkpoint_reports_per_skill_and_vocabulary_quiz_pass`,
  `test_evaluate_checkpoint_fails_writing_below_minimum_skill_band` all pass. Covers FR-13
  through FR-18.

## Revision-3 Task-16 — Frontend: checkpoint progress + catch-up banner on Daily Overview
- [x] Status: Done
- Depends on: Task-15
- Goal: Surface `effectiveDay`/`checkpoint` from the overview response — a 5-item checkpoint
  list (4 skills + vocab quiz, passed/unpassed), a passed-count summary, and a catch-up banner
  when `effectiveDay !== today`.
- Files touched: `src/app/daily-lesson/models/daily-focus.model.ts`,
  `src/app/daily-lesson/data/daily-lesson.repository.ts`,
  `src/app/daily-lesson/pages/daily-overview/*`.
- Definition of done: `daily-lesson.repository.spec.ts` and `daily-overview.component.spec.ts`
  pass with the new fields populated.

## Revision-3 Task-17 — Tab bar redesign
- [x] Status: Done
- Depends on: none
- Goal: Remove the dead `/history` link and the standalone Writing/Speaking Coach nav entries
  (reachable via today's skill cards instead); add `routerLinkActive` highlighting; move Export
  to a secondary position beside the auth controls.
- Files touched: `src/app/app.html`, `src/app/app.ts`, `src/app/app.css`.
- Definition of done: `app.spec.ts` (nav visibility/logout tests) still passes; manual visual
  check via `ng build`.

## Revision-2 Task-11 — Learner identity and registration
- [x] Status: Done
- Depends on: none
- Goal: Add users, email/password registration, user-bound signed sessions, and preserve the
  existing learner as a legacy account.
- Definition of done: auth tests cover duplicate registration, login, logout, and session user.

## Revision-2 Task-12 — Per-user learning data isolation
- [x] Status: Done
- Depends on: Task-11
- Goal: Add ownership to every learner aggregate and scope all APIs/services/exports.
- Definition of done: two-user tests prove no cross-account data access.

## Revision-2 Task-13 — IELTS Academic study profile and 24-week allocator
- [x] Status: Done
- Depends on: Task-11
- Goal: Persist the 3.5→6.5/24-week/60-minute goal and allocate review plus primary/support skill.
- Definition of done: allocation tests cover phase, target level, timing, and personalization.

## Revision-2 Task-14 — Adaptive daily-session UI
- [x] Status: Done
- Depends on: Task-12, Task-13
- Goal: Add registration/profile UX and show week, phase, target band, minutes, and rationale.
- Definition of done: frontend tests and browser verification pass.

## Task-1 — DailyFocus model + migration
- [x] Status: Done
- Depends on: none
- Goal: Define `DailyFocus` (id, day, skill enum, focus_kind enum, focus_reference nullable, created_at, unique on (day, skill)) in `backend/app/models/daily_lesson_plan.py`, and the Alembic migration creating the `daily_focus` table — per `docs/adr/2026-07-30-daily-lesson-plan-data-model.md`.
- Files touched: `backend/app/models/daily_lesson_plan.py`, `backend/alembic/versions/<ts>_daily_focus_table.py`
- Definition of done: migration test creates the table with the expected columns and unique constraint; a model round-trip test confirms the unique constraint rejects a second row for the same (day, skill).

## Task-2 — Retire the old Study Plan module (backend)
- [x] Status: Done (backend portion; frontend removal is Task-10)
- Depends on: Task-1
- Goal: Remove `backend/app/models/study_plan.py`, `backend/app/routers/study_plan.py`, `backend/app/services/study_plan.py`, and their `tasks`/`plan_state` tables (Alembic migration dropping both tables), per the supersede note in `docs/specs/study-plan-execution/Specification.md` and the data-model ADR's Consequences.
- Files touched: deleted backend files above, `backend/alembic/versions/<ts>_drop_study_plan_tables.py`, `backend/app/main.py` (remove the old router registration)
- Definition of done: migration test confirms `tasks`/`plan_state` no longer exist after upgrade and are restored on downgrade; the full backend test suite passes with zero references to the removed module remaining.

## Task-3 — Personalization selection service
- [x] Status: Done
- Depends on: Task-1
- Goal: Implement `get_or_create_focus(day: date, skill: Skill) -> DailyFocus` in `backend/app/services/daily_lesson_plan.py`: if a row already exists for (day, skill), return it; otherwise select a target from recent Mistake Notebook entries or vocabulary due for review (falling back to a general-topic default when neither exists) and persist it once.
- Files touched: `backend/app/services/daily_lesson_plan.py`, `backend/app/services/daily_lesson_plan_test.py`
- Definition of done: unit tests pass, asserting (1) with seeded mistake/vocabulary data, the selected focus references one of those items — covers FR-1; (2) with no such data, a default focus is still produced — covers FR-2; (3) a second call for the same (day, skill) returns the identical row — covers FR-3; (4) deleting the source mistake/vocabulary item after generation does not change the already-persisted `focus_reference` — covers FR-10.

## Task-4 — Prompt-text generation for Writing/Speaking
- [x] Status: Done (also extended writing_submissions/speaking_submissions with nullable `day` columns, and speaking_submissions with a nullable `prompt_text` column + optional `question_id`, so AI-generated Speaking prompts can be persisted alongside the existing seeded question bank — migration 0012)
- Depends on: Task-3
- Goal: Implement `generate_prompt_text(focus: DailyFocus) -> str` in `backend/app/services/daily_lesson_plan.py`, calling `AIProvider.chat()` with a constructed instruction to produce one IELTS-style Writing or Speaking prompt from the focus.
- Files touched: `backend/app/services/daily_lesson_plan.py`, `backend/app/services/daily_lesson_plan_test.py`
- Definition of done: unit test passes with a `FakeAIProvider`, asserting `chat()` is called with an instruction referencing the focus and the returned prompt text is what gets exposed for Writing/Speaking to use — covers FR-7.

## Task-5 — Status aggregation across skill modules
- [x] Status: Done
- Depends on: Task-1, Task-3, reading-practice Task-1, listening-practice Task-1
- Goal: Implement `get_skill_status(day: date, skill: Skill) -> Status` in `backend/app/services/daily_lesson_plan.py`, reading Reading Practice's, Listening Practice's, or the existing writing-submissions/speaking-submissions table for the matching day and mapping each module's own state to the shared Ready/Generating/Done/Failed vocabulary.
- Files touched: `backend/app/services/daily_lesson_plan.py`, `backend/app/services/daily_lesson_plan_test.py`
- Definition of done: unit tests pass with fixture rows in each of the four skill tables covering every state, asserting each maps to the correct shared status value — covers FR-4.

## Task-6 — Generation orchestration
- [x] Status: Done
- Depends on: Task-5, reading-practice Task-3, listening-practice Task-4, Task-4 (this spec)
- Goal: Implement `ensure_today_generated(day: date) -> None` in `backend/app/services/daily_lesson_plan.py`: for each of the four skills, if no focus exists yet for `day`, call `get_or_create_focus`, then trigger that skill's own generation (`reading_practice.get_or_create_exercise`, `listening_practice.get_or_create_exercise`, or `generate_prompt_text` for Writing/Speaking) with the resulting focus.
- Files touched: `backend/app/services/daily_lesson_plan.py`, `backend/app/services/daily_lesson_plan_test.py`
- Definition of done: integration test passes, asserting a fresh day's first call triggers generation for all four skills exactly once, and a second call for the same day triggers no further generation calls (reuses Task-3's `get_or_create_focus` idempotency).

## Task-7 — GET /api/daily-lesson/overview endpoint
- [x] Status: Done
- Depends on: Task-6
- Goal: Implement the overview endpoint: calls `ensure_today_generated` for the current calendar day, then returns today's four skills' focus/status plus any earlier day's skill still not Done, each labeled with its own day.
- Files touched: `backend/app/routers/daily_lesson_plan.py`, `backend/app/routers/daily_lesson_plan_test.py`, `backend/app/schemas/daily_lesson_plan.py`
- Definition of done: integration tests pass, asserting (1) the response includes a status and focus note per skill for today — covers FR-4, FR-6; (2) a not-yet-Done skill from an earlier day appears in the response labeled with its original day — covers FR-11, FR-12.

## Task-8 — POST /api/daily-lesson/{skill}/retry endpoint
- [x] Status: Done
- Depends on: Task-6
- Goal: Implement a retry endpoint that re-triggers the named skill's generation for a given day, reusing that day's already-computed focus rather than recomputing it.
- Files touched: `backend/app/routers/daily_lesson_plan.py`, `backend/app/routers/daily_lesson_plan_test.py`
- Definition of done: integration test passes, asserting the retried generation call's focus argument matches the original day's `daily_focus` row — covers FR-5.

## Task-9 — Frontend Daily Overview page
- [x] Status: Done
- Depends on: Task-7, Task-8
- Goal: Implement `src/app/daily-lesson/{models,data,state,pages/daily-overview}` rendering the skill cards, personalization notes, retry action, and carried-over-day distinction from `docs/ux/wireframes/daily-overview.md`, plus the secondary navigation row (Vocabulary, Mistakes, Progress, Export).
- Files touched: `src/app/daily-lesson/models/daily-focus.model.ts`, `src/app/daily-lesson/data/daily-lesson.repository.ts`, `src/app/daily-lesson/state/daily-lesson.state.ts`, `src/app/daily-lesson/pages/daily-overview/*`
- Definition of done: component tests pass covering all states from the wireframe (Ready/Generating/Done/Failed per skill, cold-start with no personalization data, carried-over day labeling) and confirming the secondary navigation renders regardless of skill states — covers FR-4, FR-6, FR-9, FR-11, FR-12.

## Task-10 — Remove old Study Plan frontend module and mount Daily Overview at root
- [x] Status: Done
- Depends on: Task-9, Task-2
- Goal: Remove `src/app/study-plan/` entirely and update `src/app/app.routes.ts` so the root route renders the Daily Overview page instead of the old daily-checklist page.
- Files touched: deleted `src/app/study-plan/*`, `src/app/app.routes.ts`
- Definition of done: full frontend test suite passes with zero references to the removed module remaining, and an end-to-end check confirms the root route renders Daily Overview.
