# Wireframe: Daily Overview
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-lesson.md

> Supersedes `docs/ux/wireframes/dashboard-overview.md` — that screen was built around the 180-day plan/streak/backup model from the superseded architecture. This screen is now the app's landing screen: today's AI-generated practice set across all 4 skills, not a general-purpose dashboard.

## Purpose
Give the learner, the moment they open the app, a single at-a-glance view of today's practice across all 4 skills — what's ready, what's still generating, what's already done — and a direct entry point into each.

## Layout
```
+---------------------------------------------------------------+
| Header: IELTS Daily Lessons                    [Logout]         |
+---------------------------------------------------------------+
| Main:                                                          |
|  1. Today's focus banner                                       |
|     "Today's focus: Cause-effect language, 'consequently' set" |
|     (derived from recent mistakes / due vocabulary)            |
|                                                                 |
|  2. Skill cards (one per skill, equal visual weight)            |
|     +----------------+ +----------------+                     |
|     | READING        | | LISTENING      |                     |
|     | [Ready]         | | [Generating…]   |                    |
|     | -> Start        | | (disabled)      |                    |
|     +----------------+ +----------------+                     |
|     +----------------+ +----------------+                     |
|     | WRITING        | | SPEAKING       |                     |
|     | [Done - 6.5]    | | [Ready]         |                    |
|     | -> Review       | | -> Start        |                    |
|     +----------------+ +----------------+                     |
|                                                                 |
|  3. Secondary links row (lower priority)                        |
|     [ Vocabulary Review ]  [ Mistake Notebook ]  [ Progress ]   |
|     [ Export My Data ]                                          |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Today's focus banner | Make personalization visible and felt, not just claimed (journey success criterion: "personalization is felt, not just claimed") — names the specific mistake pattern/vocabulary driving today's content | High |
| Per-skill card with explicit state (Ready / Generating… / Done) | The journey's #1 flagged risk is a skill silently unusable — the state must be unambiguous per skill, never a single global "loading" that hides which skill is actually blocked (journey step 1) | High |
| Start / Review action per card | One-step entry into each skill's exercise or its result, matching journey steps 2, 7, 9 (any order, no forced sequence) | High |
| Done state showing the outcome inline (e.g. score/band) | Lets the learner see today's full result set without re-entering each skill (journey step 11 payoff moment) | High |
| Secondary links (Vocabulary, Mistakes, Progress, Export) | Entry points into existing supporting features, kept visually subordinate to the daily practice cards since they are not today's primary task | Medium |
| Logout | Standard access-protection affordance, already established pattern | Low |

## States
- **Empty**: should not normally occur — the daily set is generated before this screen is shown. If generation for the entire day hasn't started yet (e.g. very first load), show all 4 cards in "Generating…" state rather than an empty screen, so the learner never sees a screen implying nothing is planned.
- **Loading**: initial fetch of today's status — show all 4 skill cards as skeletons; the focus banner can appear slightly after (non-blocking).
- **Error**: one or more skills failed to generate (e.g. AI provider error) — that card shows a distinct "Couldn't generate today — [ Retry ]" state, scoped to that card only; the other 3 skills remain usable. A screen-wide error banner appears only if the entire day's generation failed (e.g. not logged in, or a systemic failure), not for a single skill's failure.
- **Populated**: the happy path shown in the layout above — each card reflects its true current state (Ready / Generating… / Done / Failed).
