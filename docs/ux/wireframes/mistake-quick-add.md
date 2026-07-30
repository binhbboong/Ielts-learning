# Wireframe: Mistake Quick-Add (from Reading/Listening result)
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-lesson.md

## Purpose
Let the learner turn a wrong Reading/Listening answer into a Mistake Notebook entry in one tap-and-confirm, since the app already knows every field the manual `mistake-logging-form.md` would otherwise ask for (question, learner's answer, correct answer, skill, source = today's generated exercise) — the only thing genuinely missing is *why*, which the learner may or may not want to add right now.

## Layout
```
+---------------------------------------------------------------------+
| Header: Add to Mistake Notebook                            [X] Cancel|
+---------------------------------------------------------------------+
| Section A — Already known (read-only, not re-entered)                |
|   Skill:            Reading  (or Listening)                          |
|   Source:           Today's generated passage, Q4                    |
|   Question:          "According to the passage, what caused...?"     |
|   Your answer:       A                                                |
|   Correct answer:    C                                                |
+---------------------------------------------------------------------+
| Section B — Why It Happened (the only thing left to decide)          |
|   Reason (pick one — quick tap, no writing required):                |
|     ( ) Didn't know the vocabulary                                   |
|     ( ) Missed a paraphrase                                          |
|     ( ) Misread the question                                         |
|     ( ) Missing information                                          |
|     ( ) Used outside knowledge                                       |
|     ( ) Ran out of time                                               |
|     ( ) Carelessness                                                  |
|     ( ) Wrong grammar                                                 |
|     ( ) Not sure yet / other                                          |
|   (same fixed category list as mistake-logging-form.md)               |
+---------------------------------------------------------------------+
| Footer:  [ Add to Notebook ]        [ Skip Reason & Add Anyway ]      |
+---------------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Read-only "already known" section | Removes all re-entry the manual form would otherwise require — the entire reason this screen exists instead of reusing mistake-logging-form.md as-is | High |
| Reason-category single-select (same fixed list as the manual form) | Preserves one consistent taxonomy across manually-logged and auto-sourced mistakes, so Epic-3's pattern-grouping (mistake-tracking) works identically regardless of entry source | High |
| "Add to Notebook" primary action | Completes the one-tap-and-confirm flow the journey calls for | High |
| "Skip Reason & Add Anyway" | Mirrors the manual form's "Not sure yet / other" — logging the mistake should never be blocked on picking a reason, matching the existing form's established pattern of not gating save on this field | Medium |
| Cancel [X] | Lets the learner decide not to log this particular miss after all, returning to the Reading/Listening result screen unchanged | Low |

## States
- **Empty**: freshly opened from a wrong-answer row's "Add to Mistake Notebook" action — Section A fully pre-filled (nothing here is ever blank, since it's all sourced from the exercise itself), reason unselected.
- **Loading**: not applicable in the normal case — Section A's data already exists in the current screen's state, no fetch needed. If saving requires a server round-trip, a brief inline state on the primary action button (not a full-screen loader) is enough.
- **Error**: save fails (e.g. network/server error) — inline error message near the action buttons, all context and reason selection remain exactly as they were, retry without re-entry.
- **Populated**: reason selected, ready to save — this is the expected common case given the low-effort single-tap design.
