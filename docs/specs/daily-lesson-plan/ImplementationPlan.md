# Implementation Plan: Daily Personalized Lesson Plan
Spec: docs/specs/daily-lesson-plan/Specification.md

## Approach

**Revision-2 foundation**: introduce a `users` identity table and signed sessions containing
`user_id`; add ownership foreign keys to every learner-owned aggregate. Introduce one
`study_profiles` row per user and extend `daily_focus` with allocation metadata
(`target_band`, `estimated_minutes`, `priority`, `phase`, `rationale`). Existing rows migrate
to a legacy user. Routers pass authenticated identity explicitly and services include it in
every query.

The allocator uses a deterministic six-phase, 24-week IELTS Academic schedule as its safe
baseline, then uses per-user mistakes, due vocabulary, and recorded performance as priority
signals. It creates only the day's primary/supporting skills, reserving review time separately,
so generated workload fits the 60-minute budget.

**Chosen approach**: a single new backend module (`daily_lesson_plan`) that owns one table —
the per-day/per-skill personalization decision (`daily_focus`, see
`docs/adr/2026-07-30-daily-lesson-plan-data-model.md`) — and derives each skill's
Ready/Generating/Done/Failed status by reading Reading Practice's, Listening Practice's, and
the existing writing-submissions/speaking-submissions tables directly, rather than owning a
duplicated status cache. Two alternatives were considered and rejected; see the ADR's Context
section for the full comparison (a status-cache table with cross-epic write coordination, and
no dedicated module at all with each skill computing its own focus inline) — both were rejected
there for the same reasons that apply to this plan.

**Prompt generation for Writing/Speaking (FR-7)**: generating an actual IELTS-style
prompt sentence (not just a short focus description like "the word 'nevertheless'") from a
personalization focus is itself a small AI-generation step. Rather than adding a seventh
`AIProvider` method for this, the plan uses the already-existing, deliberately generic
`AIProvider.chat()` method (`docs/adr/2026-07-29-ai-provider-interface-shape.md`) with a
constructed instruction ("write one IELTS Writing Task 2-style prompt about X" /
"write one IELTS Speaking Part 2-style cue card about X"). This is a low-risk, easily-reversible
use of an already-decided general-purpose primitive, not a new interface shape — no ADR
warranted (implementation-planning skill: reserve ADRs for real forks in the road).

**The existing `study_plan` backend module and `study-plan` Angular module are removed**, not
kept alongside the new one — per the PRD's supersede note and the ADR's Consequences, this is a
rework. Their tests are removed along with them; nothing from that implementation is reused
(its data model doesn't fit — see the ADR).

## File/Module Structure
| Path | Responsibility | Implements (wireframe/prototype) |
|------|-----------------|-----------------|
| `backend/app/models/daily_lesson_plan.py` | `DailyFocus` SQLAlchemy model (`daily_focus` table, per ADR) | — |
| `backend/alembic/versions/000X_daily_focus_and_drop_study_plan.py` | Creates `daily_focus`; drops `tasks`/`plan_state` (old study-plan tables) | — |
| `backend/app/schemas/daily_lesson_plan.py` | Pydantic response shapes: per-skill overview entry (`skill`, `status`, `focus_reference`, `day`), the full overview response (today + carried-over days) | docs/ux/wireframes/daily-overview.md |
| `backend/app/services/daily_lesson_plan.py` | Personalization selection (reads Mistake Notebook/Vocabulary tables), `get_or_create_focus(day, skill)`, prompt-text generation via `AIProvider.chat()` for Writing/Speaking, status aggregation across skill tables | — |
| `backend/app/routers/daily_lesson_plan.py` | `GET /api/daily-lesson/overview` (today + carried-over), `POST /api/daily-lesson/{skill}/retry` | docs/ux/wireframes/daily-overview.md |
| `backend/app/ai/schemas.py` (extended) | No new types needed — prompt generation reuses `ChatRequest`/`ChatResult` | — |
| `src/app/daily-lesson/models/daily-focus.model.ts` | TypeScript types for the overview response | — |
| `src/app/daily-lesson/data/daily-lesson.repository.ts` | Calls `GET /api/daily-lesson/overview`, `POST /api/daily-lesson/{skill}/retry` via the shared `ApiClient` | — |
| `src/app/daily-lesson/state/daily-lesson.state.ts` | Holds the current overview (today + carried-over), refresh/retry actions | — |
| `src/app/daily-lesson/pages/daily-overview/` | Renders the skill cards, personalization notes, retry action, navigation into each skill and into Vocabulary/Mistakes/Progress/Export | docs/ux/wireframes/daily-overview.md |
| `src/app/app.routes.ts` (modified) | Root route becomes Daily Overview (replacing the old study-plan daily-checklist root route) | — |
| `src/app/study-plan/` | **Removed** (backend `study_plan` module and its routes also removed) | — |

## Testing Strategy
| FR-0 / FR-0A (accounts and ownership) | Registration/login tests plus two-user integration tests proving cross-user reads and mutations return no data |
| FR-0B (goal profile) | Model/API round-trip and validation tests |
| FR-0C (60-minute allocation) | Allocator unit tests asserting review=10 and allocated skills sum to 50 |
| FR-0D (visible plan context) | Router schema and Angular component tests |
| FR-0E (Academic/level-aware generation) | Fake-provider request assertions |
| Requirement | Verified by |
|---|---|
| FR-1 (per-skill focus derived from mistakes/vocab) | Service unit test seeding real mistake/vocabulary rows, asserting the selected focus references one of them |
| FR-2 (cold-start default) | Service unit test with empty mistake/vocabulary tables, asserting a default focus is still produced for all four skills |
| FR-3 (generate once, reuse) | Service test calling the get-or-create path twice for the same (day, skill), asserting the second call returns the identical row (no new row, `daily_focus`'s unique constraint enforces this) |
| FR-4 (four states always shown) | Router integration test with fixture rows in Reading/Listening/writing-submissions/speaking-submissions tables covering each status, asserting the overview response reflects each correctly |
| FR-5 (retry reuses same focus) | Router integration test on `POST /api/daily-lesson/{skill}/retry`, asserting the retried generation call's focus argument matches the original |
| FR-6 (personalization note is human-readable) | Schema/response test asserting `focus_reference` is present and non-empty when source data exists |
| FR-7 (Writing/Speaking prompt supplied) | Service unit test asserting `AIProvider.chat()` is called with the day's focus and the returned prompt text is what's exposed to Writing/Speaking's submission flow |
| FR-8 (no fixed end date) | Service test computing a focus for a day far in the future, asserting it succeeds with no bound check |
| FR-9 (secondary nav always reachable) | Frontend component test asserting the four secondary links render regardless of injected skill states, including all-Failed |
| FR-10 (no retroactive invalidation) | Service test: generate a day's focus referencing a mistake, delete that mistake, assert the already-generated `daily_focus` row and its `focus_reference` are unchanged |
| FR-11 (incomplete skill carries over) | Router integration test: a not-yet-Done skill from an earlier day still appears in the overview response on a later day |
| FR-12 (carried-over skill visibly distinguished) | Frontend component test asserting a carried-over card renders its original day, distinct from today's cards |

## Risks / Open Questions
- The overview read path queries once per skill per rendered day (today plus any carried-over
  days) — acceptable at single-learner scale (per the ADR), flagged here so it isn't revisited
  as an unexplained N+1 pattern later.
- `AIProvider.chat()` for prompt generation has no existing caller today (unused, like
  `generate_quiz()` before this epic) — this plan is its first real usage; `ClaudeProvider`'s
  `chat()` implementation should be verified against a real prompt-generation instruction during
  implementation, not assumed to work from its interface signature alone.

## Related ADRs
- docs/adr/2026-07-30-daily-lesson-plan-data-model.md
