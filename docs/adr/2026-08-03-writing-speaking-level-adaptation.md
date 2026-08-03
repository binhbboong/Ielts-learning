# ADR: Phase-appropriate Writing/Speaking task selection, level-aware grading, and wiring the AI-generated prompt into the submit UI

Date: 2026-08-03
Slug: writing-speaking-level-adaptation
Status: Accepted
Related spec: docs/specs/writing-coach/Specification.md, docs/specs/speaking-coach/Specification.md,
docs/specs/daily-lesson-plan/Specification.md

## Context

The user asked for Writing and Speaking to be appropriate for true IELTS beginners (the
"foundation" phase, target band ~4.5), with the AI auto-generating a lesson that actually fits
that level. Investigation found three compounding problems, not one:

1. **Task type never varies by level.** `_PROMPT_INSTRUCTION` in
   `backend/app/services/daily_lesson_plan.py` is a flat dict — every learner at every phase gets
   a Writing Task 2 essay prompt and a Speaking Part 2 cue-card prompt, the two hardest,
   most abstract task types in the exam. `focus.target_band`/`focus.phase` are only appended as
   trailing descriptive text in the instruction sent to the AI; they never influence which task
   type or how demanding the prompt actually is.
2. **Grading never varies by level either.** `WritingEvaluationRequest`/`SpeakingEvaluationRequest`
   (`backend/app/ai/schemas.py`) have no band/level field at all. The grading prompts in
   `backend/app/ai/claude_provider.py` and `backend/app/ai/openai_provider.py` grade every
   submission against an implicit flat band-9 rubric — a foundation learner's attempt is scored
   and critiqued exactly like an advanced candidate's would be.
3. **The AI-generated prompt never reaches the learner at all.** `DailyFocus.generated_prompt_text`
   is computed and stored by `generate_prompt_text`, but neither
   `src/app/writing-coach/pages/submit/` nor `src/app/speaking-coach/pages/record-response/`
   reads it — Writing requires the learner to type their own question from scratch; Speaking
   only offers a fixed 6-question seed bank unrelated to the day's personalization. This is the
   most fundamental gap: no fix to (1) or (2) matters if the personalized prompt never surfaces.
   (The backend already supports submitting a speaking response against free-text `prompt_text` +
   `day` instead of a seeded `question_id` — this was clearly built for exactly this purpose and
   simply never wired to the frontend.)

Both `docs/specs/speaking-coach/Specification.md`'s Open Questions already flagged part of this
("Should the feature distinguish IELTS Speaking's three exam parts... this affects prompt
selection") as unresolved — this decision resolves it.

## Decision

1. **Task type/complexity now depends on `focus.phase`**, not a flat template:
   - Speaking: `foundation`/`core_skills` → Part 1-style short personal-experience question;
     `development`/`consolidation` → Part 2-style cue-card long turn (today's existing default);
     `exam_readiness`/`peak_performance` → Part 3-style abstract discussion question.
   - Writing: real IELTS Task 1 (Academic) requires a chart/graph/diagram visual, which this
     app's text-only `AIProvider.chat()` cannot produce — switching task *type* by level is not
     achievable without new image-generation infrastructure, out of scope here. Instead, task
     *complexity* varies within the Task 2 essay format: `foundation`/`core_skills` gets a short,
     concrete, personal-experience-based question with an explicit "keep it to about 100-150
     words, simple everyday vocabulary" instruction; `development`/`consolidation` and above get
     the existing standard ~250-word opinion/discussion essay, `exam_readiness`/
     `peak_performance` skewing toward more abstract/policy topics.
2. **Grading is calibrated to the learner's level, not a flat band-9 standard.**
   `WritingEvaluationRequest`/`SpeakingEvaluationRequest` gain optional `target_band`/`phase`
   fields. `writing_coach.create_and_evaluate`/`speaking_coach.run_evaluation` look up that
   submission's `DailyFocus` (by day + skill + user, when the submission is tied to a day) and
   populate them; a submission with no associated day (free practice, pre-existing behavior)
   grades as before with no level context. The grading prompt instructs the AI to judge fairly
   against realistic expectations for that band/phase — it still returns an honest `overall_band`
   (grading isn't inflated, just contextualized) and still cites exact submitted wording.
3. **The AI-generated prompt is wired into both submit UIs.** `SkillOverviewEntry` (backend
   schema and frontend model) gains `generated_prompt_text`. The Writing submit page and Speaking
   record-response page each read today's (or the effective day's) entry for their skill from
   `DailyLessonFacade`/`DailyLessonRepository` (already loaded for the overview) and, when a
   generated prompt exists, pre-fill it (Writing: task type + question text, editable but
   pre-filled; Speaking: submits via `prompt_text` + `day`, the backend path that already exists)
   instead of requiring the learner to source their own question. Manual/free practice remains
   available (Writing: the learner can still edit or replace the pre-filled text; Speaking: the
   existing part/question-bank picker stays as a secondary option) — this decision does not
   remove the option, it makes the personalized path the default.

## Consequences

- Easier: a foundation-phase learner now gets a genuinely simpler Speaking question and a
  shorter, more concrete Writing prompt, graded with realistic expectations for their level —
  directly closing the gap the user asked about.
- Harder: task-type/complexity and grading calibration now depend on `DailyFocus` existing and
  being looked up correctly by day+skill+user; a submission not tied to any day (ad hoc free
  practice) still grades against the flat rubric as before — this is an accepted, unavoidable
  fallback, not a regression, since there is no level to calibrate against without a day.
- Forecloses (for now): true Writing Task 1 (Academic) with a real chart/graph, which would need
  image-generation capability this app doesn't have — flagged as a future decision, not solved
  here.
- The 6-question seeded Speaking bank is unchanged (no band tagging added) — it remains available
  as manual/free practice, superseded as the *daily* default by the AI-generated `prompt_text`
  path per learner phase.
