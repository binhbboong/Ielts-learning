# Wireframe: Progress Trend
Supports journey: docs/ux/journeys/solo-ielts-learner-progress-tracking.md (steps 8-10)

## Purpose
Let the solo learner open one screen and get an objective, feeling-independent read on whether Reading/Listening is improving (Vision G-4) — and, critically, pair that read with a specific, actionable weak spot in the same view, so a flat or declining trend lands as useful diagnostic signal rather than discouraging failure (step 9's risk, resolved by step 10's payoff).

## Notes on scope
This one screen absorbs both candidate names from the journey's candidate list:
- "Progress Trend view (average score + trend direction over time)" -> **Score Trend region** (top)
- "Missed question-type breakdown view" -> **Missed Question-Type Breakdown region** (bottom)

These are two regions of a single screen, not two screens. The breakdown region is never hidden behind a click or a second navigation step — it is always visible below the trend, because its entire purpose (per step 10) is to immediately reframe whatever the trend region just showed.

## Layout
```
+------------------------------------------------------------------+
| Header: "Progress Trend"                                         |
| Skill: ( Reading ) ( Listening ) ( Both )   Period: [Last 8 wks v]|
|                                                       [ Refresh ] |
+------------------------------------------------------------------+
| REGION 1 — Score Trend (top, always visible; step 8-9)           |
|                                                                    |
|  Average score: 6.5 / 9        Sessions counted: 6                |
|  Trend: Steady   (explicit text label, not an icon/color alone)  |
|                                                                    |
|  [ chart/graph placeholder: score per logged session, oldest ->  |
|    newest, for the selected skill/period — a line or bar chart   |
|    would render here; visual style/axis styling not decided in   |
|    this wireframe ]                                               |
|                                                                    |
|  Framing note (always present, wording adapts to trend — see      |
|  Key Elements):                                                   |
|  "Steady average this period. See your focus area below to push  |
|   it up next."                                                    |
+------------------------------------------------------------------+
| REGION 2 — Missed Question-Type Breakdown (bottom, always         |
| visible directly beneath Region 1, never a separate click; step   |
| 10 — the constructive payoff for whatever Region 1 just showed)  |
|                                                                    |
|  Most-missed question types this period (ranked, all shown):     |
|   1. Matching Headings ................ 6 misses (35%)  <- FOCUS |
|   2. True / False / Not Given ......... 4 misses (24%)           |
|   3. Sentence Completion ............... 3 misses (18%)          |
|   4. Multiple Choice .................... 2 misses (12%)          |
|   5. Short Answer ........................ 2 misses (12%)          |
|                                                                    |
|  Callout: "Focus next session on: Matching Headings"              |
+------------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Trend framing note (Region 1) | The direct fix for step 9's high-risk failure mode: pairs the raw average/direction with a short, non-judgmental sentence that always points at Region 2, so a flat/declining number is never left to stand alone as a bare verdict. Wording adapts to trend direction — e.g. Up: "Improving — keep it up, and here's what's still worth tightening." / Steady: "Steady this period — see your focus area below to push it up next." / Down: "Your average dipped this period. That's normal variation, not failure — here's exactly what to focus on next." | High |
| Average score + Trend (Up/Stable/Down as text) | Delivers the "objective, feeling-independent signal" step 9 asks for, stated as data rather than as an implied grade | High |
| Missed Question-Type Breakdown list, always visible below Region 1 | The step 10 payoff — turns "your score is flat" into "here's the specific thing to work on," which is the whole reason this journey's drop-off risk at step 9 is rated only Low at step 10 | High |
| "Focus next session on: X" callout | Converts the ranked list into a single, unambiguous next action, so the learner leaves with a decision made for them, not just more data to interpret | High |
| Sessions-counted indicator ("Sessions counted: 6") | Grounds the trend in how much evidence backs it, and is the same signal used to decide the Empty state threshold (4+ sessions per Vision success metric) | Medium |
| Skill filter (Reading / Listening / Both) | Lets the learner isolate a single skill's trend, since Reading and Listening are logged and expected to progress independently | Medium |
| Period selector (e.g. "Last 8 weeks") | Bounds the trend/breakdown to a meaningful recent window rather than an all-time blend that could mask recent improvement or recent decline | Medium |
| Chart/graph placeholder (Region 1) | Marks where a score-over-time visual belongs without committing to its visual design here (per wireframing scope) | Medium |
| Refresh control | Re-reads current data; relevant since this is a client-only app with local data ownership and no server push | Low |
| Return/find-this-screen path (nav, shared chrome) | Addresses step 8's risk directly — the check-in habit lapses if this view isn't easy to find or return to; this screen must be reachable from the app's persistent navigation, not buried | High |

## States
- **Empty**: fewer than 4 logged sessions for the selected skill/period (the threshold the Vision success metric itself requires before a trend is meaningful). Region 1 does **not** render a broken or blank chart — it shows a plain message instead, e.g. "Log a few more sessions to see a trend — you have 2 of the 4+ needed." Region 2 still renders if any missed-question-type data exists from the sessions logged so far (labelled "based on 2 sessions so far, not yet a full trend"), so the learner isn't left with nothing actionable even before the trend threshold is met; if zero sessions exist at all, both regions collapse into one onboarding message pointing back to the Log Practice Result screen. This state must read as "not enough data yet," never as "something is broken."
- **Loading**: header, skill filter, and period selector render immediately (they don't depend on data); Region 1 and Region 2 each show a lightweight placeholder (e.g. "Loading trend...", "Loading breakdown...") in place of the chart and ranked list.
- **Error**: local read/storage failure for one or both regions (client-only app, so this is a local data-layer failure, not a network error). Show a short, cause-agnostic message per affected region (e.g. "Couldn't load your progress data.") plus a retry action, explicitly distinct from the Empty state's "no data yet" wording so a real failure is never mistaken for a fresh start. Chrome (header, filters) stays visible and usable.
- **Populated**: both regions render together as in the Layout above — Region 1's framing note and Region 2's ranked breakdown are always shown side by side (stacked), regardless of whether the trend is Up, Steady, or Down, so the constructive payoff (step 10) is never separated from or delayed after the potentially discouraging signal (step 9).
