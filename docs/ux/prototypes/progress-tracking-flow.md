# Prototype: Practice Result Logging & Progress Trend Flow
Journey: docs/ux/journeys/solo-ielts-learner-progress-tracking.md

## Screen Sequence
1. docs/ux/wireframes/log-practice-result.md — triggered by: learner opens the app right after finishing an external Reading/Listening practice session and starts a new entry (journey step 2)
2. docs/ux/wireframes/log-practice-result.md (Saved confirmation sub-state) — triggered by: tapping "Save Result" on screen 1 with the minimum viable fields (Skill, Source, Score/Total) filled (journey step 7)
3. docs/ux/wireframes/progress-trend.md — triggered by: on a later, separate visit, learner selects "Progress Trend" from the app's persistent nav specifically to check progress (journey step 8)
4. docs/ux/wireframes/practice-log-history.md — triggered by: learner selects "Practice Log" / "History" from the persistent nav at any point (side branch — not a required step toward this journey's success criteria; see note below)

## Transitions
| From | Trigger | To |
|---|---|---|
| (app entry) | Learner opens the app right after finishing external practice and selects "Log Result" (or equivalent entry action) | Log Practice Result, Empty state |
| Log Practice Result | Learner fills Skill, Source, and Score/Total (the minimum viable fields) | Log Practice Result, Filled/unsaved state — Save enabled |
| Log Practice Result | Learner taps "Save Result" and the local write succeeds | Log Practice Result, Saved confirmation sub-state ("Result saved — Reading, 27/40") |
| Log Practice Result | Learner taps "Save Result" and the local write fails | Log Practice Result, Error state — inline "Couldn't save — try again," all typed fields retained, Save retryable in place |
| Log Practice Result | Learner taps "Cancel" | Exits the form unsaved, back to wherever the learner entered from |
| Log Practice Result (Saved confirmation) | Learner taps "Log Another" | Log Practice Result, Empty state (new entry) |
| Log Practice Result (Saved confirmation) | Learner taps the return action | Back to wherever the learner entered from |
| (app entry, later visit) | Learner opens the app specifically to check progress and selects "Progress Trend" from the persistent nav | Progress Trend — Populated state if 4+ sessions logged for the selected skill/period, otherwise Empty state |
| Progress Trend | Learner changes the Skill filter (Reading / Listening / Both) or the Period selector | Progress Trend, same screen — both regions re-render for the new filter |
| Progress Trend | Learner taps "Refresh" | Progress Trend, same screen — re-reads current local data |
| Progress Trend (Empty state, zero sessions logged at all) | Learner taps the onboarding message's link back to logging | Log Practice Result, Empty state |
| (any screen, persistent nav) | Learner selects "Practice Log" / "History" from the nav | Practice Log / History — Populated state if entries exist, otherwise Empty state |
| Practice Log / History | Learner changes the Skill filter or Sort order | Practice Log / History, same screen — list re-renders |
| Practice Log / History (Empty state) | Learner taps the call-to-action pointing at Log Practice Result | Log Practice Result, Empty state |

## Readiness for Specification
- [ ] Every step of the source journey is covered by a screen in this flow. **Partially met, and deliberately so**: step 1 (finishing practice outside the app) has no screen by design — it happens before the app is opened. Steps 2-7 are fully covered by Log Practice Result and its Saved confirmation sub-state. Steps 8-10 are fully covered by Progress Trend (Region 1 = steps 8-9, Region 2 = step 10). Practice Log / History, however, is **not** walked through by any numbered journey step — it was listed only as a candidate screen, exactly like Day History was for the daily-checklist journey (docs/ux/prototypes/daily-checklist-flow.md). It is included here as a reachable side branch (browsing raw entries), not as a required leg of the success path, so this checklist item is honestly marked partial rather than fully satisfied.
- [x] Every transition has a clear, unambiguous trigger — see table above; no "eventually gets to" steps.
- [ ] No screen exists in this flow without a stated purpose from the journey. **Partially met**: Practice Log / History has a clear purpose stated in its own wireframe (browsing the raw, chronological record, separate from the aggregated trend) but that purpose is self-declared by the wireframe, not derived from a journey step — flagged here rather than silently counted as fully covered, consistent with the daily-checklist prototype's treatment of its own side-branch screen.
- [x] Open UX questions are listed below, not silently resolved.

## Open Questions
- [NEEDS CLARIFICATION: What exact UI mechanism satisfies journey step 2 ("opens the app and starts a new practice result entry")? No wireframe defines the app's home/landing chrome — is there a persistent "Log Result" primary action, a nav item, or is Log Practice Result itself the default landing screen right after a practice session?]
- [NEEDS CLARIFICATION: Is Practice Log / History expected to be part of *this* journey's success path (e.g., as a way to double-check a specific past entry before trusting the trend), or is it purely a supporting/reference feature reached outside the "log then later check trend" scenario? No journey step currently walks through it — same open question the daily-checklist prototype flagged for Day History, and possibly worth resolving once, consistently, across both epics rather than per-flow.]
- [NEEDS CLARIFICATION: The missed-question-type taxonomy per skill (Reading vs Listening) is explicitly left undefined in Log Practice Result's own notes. Since Progress Trend's Region 2 ranked breakdown depends on the same taxonomy, this should be resolved once and applied consistently to both screens, not decided independently in each.]
- [NEEDS CLARIFICATION: Progress Trend's Empty state (fewer than 4 sessions) still renders a partial Region 2 breakdown "based on 2 sessions so far, not yet a full trend." Should this partial breakdown link out to Practice Log / History for the underlying raw entries, or are the two screens intentionally kept independent with no cross-navigation between them?]
