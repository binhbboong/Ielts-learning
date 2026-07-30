# Wireframe: Dashboard / Today Overview
Supports journey: docs/ux/journeys/solo-ielts-learner-vocabulary-review.md, docs/ux/journeys/solo-ielts-learner-data-backup-restore.md

> **Superseded** by `docs/ux/wireframes/daily-overview.md`. This screen was built around the 180-day plan/streak/backup model from the superseded architecture (see `docs/specs/study-plan-execution/Specification.md`'s own supersede note). Kept for history — do not implement against this version.

## Purpose
Give the learner a single at-a-glance landing screen — aggregating signals from the Study Plan, Vocabulary, and Backup/Restore modules (per Architecture.md's App Shell/Dashboard component) — so they can see where they stand and reach any module in one step, without owning or duplicating any module's underlying data.

## Layout
```
+---------------------------------------------------------------+
| Header: Personal IELTS Learning Dashboard                      |
+---------------------------------------------------------------+
| Nav: [Dashboard] [Today's Plan] [Vocabulary] [Mistakes]         |
|      [Progress] [Backup & Restore]                             |
+---------------------------------------------------------------+
| Main:                                                          |
|  1. Plan Progress card                                         |
|     "Day 12 of 180"   Streak: 5 days                            |
|     -> [ Go to Today's Plan ]                                  |
|                                                                 |
|  2. Vocabulary Due card                                        |
|     "15 words due today"                                       |
|     -> [ Start Review ]                                        |
|                                                                 |
|  3. Backup Status banner                                       |
|     "Last backup: 9 days ago"          [ Back Up Now ]          |
|     (visually distinct from cards above — persistent, not      |
|      dismissible without acting or explicitly deferring)       |
|                                                                 |
|  4. Secondary signals row (lower priority, glance-only)        |
|     Weakest skill: Speaking   |   Last score: Reading 6.5       |
|                                                                 |
|  5. Module entry points (if not already reached via nav)        |
|     [ Mistake Notebook ]   [ Progress / Analytics ]             |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Day/streak indicator ("Day 12 of 180", "Streak: 5 days") | Orient the learner in the overall 180-day plan and reflect ongoing consistency at a glance, without re-deriving it from the Daily Checklist screen (journey vocab-review step 1: "pick up where they left off") | High |
| Link into Today's Plan | Immediate drill-down from the summary into the full daily checklist | High |
| Vocabulary due-today count | Surface what's due "without hunting for it" (journey vocab-review step 1, direct pain point match) | High |
| Link into Vocabulary Review | One-step entry into tonight's review session | High |
| Backup Status indicator ("Last backup: X ago") | Catch attention before it's ignorable, per journey backup-restore step 1 flagged as the journey's highest drop-off risk — must not read as a passive, skippable line | High |
| Back Up Now action (inline on the status indicator) | Let the learner act on the reminder immediately, in place, instead of navigating away and losing the impulse | High |
| Weakest-skill indicator | Cross-epic signal aggregated for at-a-glance awareness (per Architecture.md App Shell/Dashboard responsibility) — explicitly excluded from the Study Plan spec's own screen, so it lives here | Medium |
| Last practice score(s) | Same rationale as weakest-skill — aggregated glance signal, not owned data | Medium |
| Nav / module entry points (Vocabulary, Mistakes, Progress, Backup & Restore) | Lets the learner jump directly to any module rather than only reaching them through cards | Medium |

## States
- **Empty** (post-data-loss, journey backup-restore step 7): no local data found for any module (fresh browser/cleared storage). Replace all cards with a single, unambiguous message distinguishing "no data yet" from "something broke" — e.g. "No study data found on this device. If this is unexpected (cleared browser, new device), you can restore from a backup." with a prominent `[ Restore from Backup ]` action leading into Backup & Restore's Import flow, plus a secondary `[ Start Fresh ]` path for a genuinely new setup. Nav remains fully visible/functional — the empty state must not read as a dead end.
- **Loading**: brief skeleton/placeholder in place of each card (Plan Progress, Vocabulary Due, Backup Status) while the App Shell reads from the Local Data Layer on entry; nav renders immediately since it doesn't depend on data.
- **Error**: local data exists but failed to load or parse (e.g. storage corrupted) for one or more modules — show a per-card or screen-level message explicitly distinct from the Empty state ("Something went wrong reading your data" vs. "No data found"), since a silent fallback to Empty state here would misread genuine corruption as a fresh start and could mask real data loss. Point toward Backup & Restore as a recovery path if a backup exists.
- **Populated**: the happy path shown in the layout above — all cards show current values (day/streak, due count, backup recency, weakest skill, last score), each linking into its owning module.
