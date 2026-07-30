# Decision Log

The single, scannable index of every decision recorded in `docs/adr/`. Check here first
before opening individual ADR files. Appended to by `/spec:plan`, `/engineering:refactor`,
and `/decide` — every ADR gets a row here the moment it's written. New rows go at the top
(newest first, matching CHANGELOG.md's convention).

ADRs are identified by filename (`YYYY-MM-DD-slug.md`), not a sequential number — see
`README.md` in this folder for why. If two branches append a row at nearly the same time,
resolve the merge conflict here the normal way (keep both rows); there's no numbering to
reconcile since each ADR's identity is already unique.

| Date | Decision | Status | Supersedes | Affects |
|---|---|---|---|---|
| 2026-07-30 | [Daily Lesson Plan data model: per-day/per-skill `daily_focus` table, status derived from each skill's own table, never owned](2026-07-30-daily-lesson-plan-data-model.md) | Accepted | 2026-07-29-study-plan-relational-task-store, 2026-07-29-study-plan-flat-task-store | daily-lesson-plan |
| 2026-07-30 | [AIProvider gains `generate_reading_exercise()` / `generate_listening_script()`, typed passage/script + question + answer-key results](2026-07-30-reading-listening-generation-interface.md) | Accepted | — | reading-practice, listening-practice |
| 2026-07-30 | [Text-to-Speech integration mirrors Speech-to-Text (protocol + swappable local adapter); generated audio stored as `bytea` in Postgres, not object storage](2026-07-30-text-to-speech-integration-and-audio-storage.md) | Accepted | — | listening-practice |
| 2026-07-29 | [Adopt full-stack architecture (Angular + FastAPI + Neon PostgreSQL + Claude API) on Vercel](2026-07-29-fullstack-vercel-claude-architecture.md) | Accepted | 2026-07-29-v1-no-backend-architecture | docs/business/Vision.md, docs/business/PRD.md, docs/architecture/Architecture.md, all specs under docs/specs/*, study-plan-execution implementation (code, rebuilt) |
| 2026-07-29 | [Single-learner auth via server-verified password + stateless signed session cookie](2026-07-29-signed-cookie-session-auth.md) | Accepted | — | access-protection |
| 2026-07-29 | [Data export is a single versioned JSON document, assembled via a per-epic export contract](2026-07-29-data-portability-export-contract.md) | Accepted | — | data-portability |
| 2026-07-29 | [Study Plan data modeled as two Postgres tables — flat `tasks` + singleton `plan_state`](2026-07-29-study-plan-relational-task-store.md) | Superseded by 2026-07-30-daily-lesson-plan-data-model | (conceptually replaces 2026-07-29-study-plan-flat-task-store's storage mechanism) | study-plan-execution (superseded epic) |
| 2026-07-29 | [Vocabulary schema: normalized vocabulary_words + review_sessions + review_session_items tables](2026-07-29-vocab-relational-schema.md) | Accepted | — | vocabulary-review |
| 2026-07-29 | [Practice results table shape (open-string skill, array missed-types) and on-demand trend derivation](2026-07-29-practice-results-schema-and-derivation.md) | Accepted | — | progress-tracking |
| 2026-07-29 | [AIProvider interface: typed request/result pairs per method, synchronous, status-discriminated results, no vendor exceptions crossing the boundary](2026-07-29-ai-provider-interface-shape.md) | Accepted | — | writing-coach, speaking-coach |
| 2026-07-29 | [Speaking submissions process as an asynchronous, step-tracked pipeline (not one synchronous call)](2026-07-29-speaking-async-step-tracked-processing.md) | Accepted | — | speaking-coach |
| 2026-07-29 | [Versioned single-file backup payload; recency re-derived from restore](2026-07-29-backup-payload-versioning-and-recency-derivation.md) | Superseded in spirit by 2026-07-29-data-portability-export-contract (premise no longer applies, see fullstack-vercel-claude-architecture) | — | data-backup-restore (superseded epic) |
| 2026-07-29 | [Missed question-type taxonomy is a fixed, hardcoded list per skill](2026-07-29-missed-question-type-taxonomy.md) | Accepted — decision still valid, carried forward as-is into 2026-07-29-practice-results-schema-and-derivation | — | progress-tracking |
| 2026-07-29 | [Mistake-reason category persisted as a stable string key, not free text](2026-07-29-mistake-reason-category-enum-key.md) | Accepted — decision still valid, carried forward as a Postgres column in the new mistake-tracking plan | — | mistake-tracking |
| 2026-07-29 | [Study Plan data modeled as a flat, day-indexed task store with an explicit current-day pointer](2026-07-29-study-plan-flat-task-store.md) | Superseded by 2026-07-30-daily-lesson-plan-data-model | — | study-plan-execution (superseded epic) |
| 2026-07-29 | ["Forgot" resets a word's review interval to the 1-day step](2026-07-29-vocab-forgot-resets-interval.md) | Accepted — rule still valid; storage mechanism now carried by 2026-07-29-vocab-relational-schema | — | vocabulary-review |
| 2026-07-29 | [V1 architecture is client-only, no backend](2026-07-29-v1-no-backend-architecture.md) | Superseded by 2026-07-29-fullstack-vercel-claude-architecture | — | docs/architecture/Architecture.md |
