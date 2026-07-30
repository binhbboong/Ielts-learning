# Wireframe: Mistake Logging Form
Supports journey: docs/ux/journeys/solo-ielts-learner-mistake-tracking.md

## Purpose
Let the learner capture one mistake — what/where it happened, both answers, and why it happened — in under 2 minutes, reached via a "Log Mistake" entry-point action from wherever they're currently studying (step 2), without losing their place in that session.

Note on the entry point: "Log Mistake" is not a separate screen — it's a lightweight action (e.g. a button on the current task/practice view) that opens this form pre-tagged with whatever study context is known (skill, source), so the learner isn't asked to re-supply what the app can already infer.

## Layout
```
+---------------------------------------------------------------------+
| Header: Log Mistake — from "Reading Passage 2, Q14"    [X] (saves    |
|                                                          draft, no    |
|                                                          data lost)  |
+---------------------------------------------------------------------+
| Section A — What & Where                                             |
|   Skill:          [ Reading v ]            (pre-filled from context) |
|   Question type:  [ Matching Headings v ]                            |
|   Source:         [ Cambridge 17, Test 2 ------------------ ]        |
+---------------------------------------------------------------------+
| Section B — Answers                                                  |
|   Your answer:      [ ------------------------------------- ]        |
|   Correct answer:   [ ------------------------------------- ]        |
|   [ ] I don't have the correct answer yet — fill in later            |
+---------------------------------------------------------------------+
| Section C — Why It Happened  (the part that matters most later)      |
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
|                                                                        |
|   Explanation (optional — add detail now, or later from Review):     |
|   [ + Add explanation ]   <- collapsed by default                    |
+---------------------------------------------------------------------+
| Footer:  [ Save & Return to Practice ]        [ Cancel ]              |
+---------------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Context breadcrumb ("from ...") | Confirms the learner's place is held, reducing the step-2 "this feels like a detour" risk | High |
| Close [X] (autosaves draft) | Lets the learner bail out mid-entry without losing what they've typed, so an interrupted log never means lost data | High |
| Skill / Question type / Source fields | Step-3 what/where context, kept short and factual so this section stays low-friction | Medium |
| Your answer / Correct answer fields | Step-4 concrete specifics needed later to "cite concrete examples" | High |
| "I don't have the correct answer yet" checkbox | Directly defuses the step-4 abandonment risk — unblocks save when the answer key isn't at hand instead of forcing a half-filled entry to be discarded | High |
| Reason-category single-select | The core data for later pattern grouping (step 8-9 payoff); presented as one tap, before the explanation, so the highest-value field is also the lowest-effort one | High |
| "Not sure yet / other" reason option | An honest low-effort choice instead of a forced guess — reduces step-5's "rushed with a generic reason" failure mode named in the journey | High |
| Explanation field (collapsed, optional) | Captures the *why* in the learner's words when they have energy for it, but never gates the save — directly targets step 5's flagged high drop-off risk | Medium |
| Save & Return to Practice (primary action) | Fast save-and-return per step 6, preserving session momentum | High |
| Cancel action | Discards the entry entirely if the learner decides not to log it after all | Low |

## States
- **Empty**: form freshly opened from the entry point; Skill/Source pre-filled if inferable from study context, all other fields blank, reason category unselected, explanation collapsed.
- **Loading**: brief placeholder while the current study-context tags (skill, source) are read from local storage to pre-fill Section A; under ~1s, no spinner needed beyond a dimmed field state.
- **Error**: Save fails (e.g. local storage write blocked) — inline error message near the Save button, all entered fields and selections remain exactly as typed (nothing cleared), and the learner can retry Save without re-entering anything, since there's no server to fall back on.
- **Populated (complete)**: all sections filled, a reason category selected, and (optionally) an explanation written — the full happy-path entry ready to save.
- **Populated (partial / incomplete)**: learner exits via [X] or an interrupted session before finishing — the draft is saved as-is (e.g. missing correct answer with the "fill in later" box checked, or reason left as "Not sure yet"), flagged as incomplete, and remains editable from the Mistake Review screen later rather than being silently discarded.
