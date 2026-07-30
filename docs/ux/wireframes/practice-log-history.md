# Wireframe: Practice Log / History
Supports journey: docs/ux/journeys/solo-ielts-learner-progress-tracking.md

> Note: no single numbered step in this journey walks through this screen in detail — it appears only as a candidate screen ("Practice Log / history list (past logged results)"). It is a supporting/reference screen, analogous to how Day History (docs/ux/wireframes/day-history.md) supports a different epic: a read-only, browsable record that sits alongside the main loop (logging in steps 1-7, reviewing trend in steps 8-10) rather than being a step in it.

## Purpose
Let the learner browse the raw, chronological record of every logged Reading/Listening practice result — an objective, inspectable list they can scan or dig into per entry — separate from the aggregated trend view.

## Layout
```
+---------------------------------------------------------------+
| Header: Practice Log                                            |
+---------------------------------------------------------------+
| Filter/Sort:  Skill [All | Reading | Listening]                 |
|               Sort   [Newest first | Oldest first]               |
+---------------------------------------------------------------+
| Main: results list (one row per logged result)                  |
|                                                                   |
|   Date        Skill      Source              Score   Time        |
|   ---------------------------------------------------------      |
|   2026-07-28  Reading    Cambridge 17 T3      32/40   58 min      |
|     Missed: True/False/NG (4), Matching Headings (2)             |
|     Note: rushed the last passage, ran short on time              |
|                                                                   |
|   2026-07-25  Listening  6 Minute English      9/10   12 min      |
|     Missed: Sentence Completion (1)                               |
|     (no note)                                                     |
|                                                                   |
|   2026-07-22  Reading    Cambridge 17 T2      29/40   62 min      |
|     Missed: Matching Headings (3), Summary Completion (2)         |
|     Note: headings still the weak spot                           |
|                                                                   |
|   ... (older entries below, same row shape) ...                  |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Date, Skill, Score, Time (per entry) | The most scannable facts — lets the learner recognize a specific session at a glance without opening it, satisfying the "objective, inspectable record" goal | High |
| Source | Identifies which material the result came from, needed to judge whether the score is comparable to another entry | High |
| Skill filter (All / Reading / Listening) | Lets the learner narrow the list when they only care about one skill's history right now | Medium |
| Sort order (Newest/Oldest first) | Supports both "what did I just do" and "how did I start out" review habits | Medium |
| Missed question types (per entry) | Secondary diagnostic detail — visible without leaving the list, but subordinate to the scannable summary row | Medium |
| Note (per entry, if present) | Free-text context the learner wrote for themselves; shown last since it's the least structured/scannable field | Low |

## States
- **Empty**: no practice results have ever been logged (a very likely early-days state, not an error). Show "No practice results logged yet" plus a direct call to action pointing at Log Practice Result, so the learner is guided to start the loop rather than left wondering if the screen is broken.
- **Loading**: brief placeholder while entries load from local storage; skill filter and sort control remain visible (disabled) rather than disappearing, so the screen's structure doesn't jump once data arrives.
- **Error**: local data failed to load — state this explicitly as "couldn't load your practice log" distinct from the empty state's "nothing logged yet," and point toward restoring from a backup (Epic-5) if available, consistent with the same distinction made on Day History.
- **Populated**: filter/sort controls plus the chronological list of entries, each showing date/skill/source/score/time prominently and missed-question-types/note as secondary per-entry detail, as sketched above.
