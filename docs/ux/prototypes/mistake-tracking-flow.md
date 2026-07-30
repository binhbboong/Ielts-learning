# Prototype: Mistake Logging & Weekly Pattern Review
Journey: docs/ux/journeys/solo-ielts-learner-mistake-tracking.md

## Screen Sequence

**Half 1 — In-the-moment logging (journey steps 1-6)**

1. *(No dedicated wireframe — see Readiness note below)* Log Mistake entry point, a contextual action on whatever study/practice screen the learner is currently on — triggered by: getting a question wrong during self-marked Reading/Listening/Writing/Speaking practice (journey step 1)
2. docs/ux/wireframes/mistake-logging-form.md (Empty state) — triggered by: tapping "Log Mistake" on the current study/practice screen (journey step 2); form opens pre-tagged with skill/source inferred from that context
3. docs/ux/wireframes/mistake-logging-form.md (Populated — complete or partial) — triggered by: the learner filling Section A (skill/question type/source), Section B (their answer, correct answer, or checking "I don't have the correct answer yet"), and Section C (reason category, optional explanation) (journey steps 3-5)
4. Return to prior study/practice context (same external screen as step 1, not a new wireframe) — triggered by: tapping "Save & Return to Practice" (journey step 6)

*(Time jump: approximately one week and several logged mistakes later — journey step 7)*

**Half 2 — Weekly review (journey steps 7-9)**

5. docs/ux/wireframes/mistake-review.md — Grouped view (Variant A, default) — triggered by: opening the Mistake Review view, a deliberate, unhurried entry point distinct from the logging half (journey step 7)
6. docs/ux/wireframes/mistake-review.md — List view (Variant B) — triggered by: tapping the "List" option in the view toggle from Grouped view (optional alternate lens; journey step 8's chronological pass, not required for the step 9 payoff)
7. docs/ux/wireframes/mistake-review.md — Category Detail (Variant C) — triggered by: selecting a category row (or its `[>]`) from Grouped view (journey step 9, the payoff step)

## Transitions
| From | Trigger | To |
|---|---|---|
| Study/practice screen (external, pre-Epic-3 context) | Learner gets a question wrong during self-marked practice | Study/practice screen (same screen — no navigation yet; this is the trigger, not an app transition) |
| Study/practice screen | Tapping "Log Mistake" action on that screen | mistake-logging-form.md (Empty state), pre-filled with inferable skill/source |
| mistake-logging-form.md (Empty) | Learner enters What/Where, Answers, and Why/Reason fields | mistake-logging-form.md (Populated — complete or partial, per which fields/checkboxes are used) |
| mistake-logging-form.md (any populated state) | Tapping "Save & Return to Practice" | Study/practice screen (prior context, resumed) |
| mistake-logging-form.md (any populated state) | Tapping `[X]` (close) | Study/practice screen (prior context), with the entry autosaved as a partial/incomplete draft, editable later from Mistake Review |
| mistake-logging-form.md (any populated state) | Tapping "Cancel" | Study/practice screen (prior context), entry discarded entirely |
| Study/practice screen (any later session) | Opening the Mistake Review view, roughly a week later | mistake-review.md — Grouped view (default) |
| mistake-review.md — Grouped view | Toggling the view toggle to "List" | mistake-review.md — List view |
| mistake-review.md — List view | Toggling the view toggle to "Grouped by reason" | mistake-review.md — Grouped view |
| mistake-review.md — Grouped view | Selecting a category row, or its `[>]` | mistake-review.md — Category Detail, for that category |
| mistake-review.md — Category Detail | Tapping "< Back to Grouped view" | mistake-review.md — Grouped view (same period preserved) |
| mistake-review.md — List view | Tapping `[View]` on a row | Single mistake's full logged detail (same underlying data as a Category Detail example entry; no separate wireframe defined for this row-level detail state) |
| mistake-review.md (any view) | Selecting a different value in the period selector | mistake-review.md (same view mode), content re-scoped to new period |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow.
- [x] Every transition has a clear, unambiguous trigger.
- [x] No screen exists in this flow without a stated purpose from the journey.
- [x] Open UX questions are listed below, not silently resolved.

**Note on the "Log Mistake entry point" (journey step 2):** this flow does not treat the missing dedicated wireframe as a readiness gap. `mistake-logging-form.md`'s own Purpose section explicitly designs this as a lightweight action folded into whatever study/practice screen the learner is already on ("not a separate screen... a button on the current task/practice view"), specifically so the learner isn't pulled out of context. Since the wireframe already states this design intent and defines exactly what the action does (opens the form pre-tagged with inferred context), there is a stated purpose and a clear trigger even without a screen of its own — the checklist item is satisfied. What is *not* yet resolved is *which* practice screens host that action and how many variants exist across skills; that's flagged below rather than assumed.

## Open Questions
- [NEEDS CLARIFICATION: The "Log Mistake" action needs a concrete home. Which practice/study screens (Reading passage view, Listening section player, Writing task editor, Speaking practice recorder) actually carry this button, and is its placement/label consistent across all four, or does each skill's practice UI need its own variant? These screens are outside Epic-3's wireframe set, so this can't be resolved from the docs read for this flow.]
- [NEEDS CLARIFICATION: mistake-review.md's Category Detail example format always shows "Your answer: ... Correct: ...", but the logging form allows saving a partial entry via "I don't have the correct answer yet" or leaving the reason as "Not sure yet / other". How should such partial entries render inside a Category Detail example list, or inside List view rows — as-is with a blank "Correct" field, with a visible "incomplete" flag, or excluded from counts until completed?]
- [NEEDS CLARIFICATION: The period selector defaults to "This week," but its exact boundaries aren't defined — a rolling trailing 7 days from "now," or a fixed calendar week (e.g. Mon-Sun)? This affects whether the journey's "by the end of week 4" success criterion lines up cleanly with four review sessions or drifts depending on when in the week the learner happens to open Review.]
- [NEEDS CLARIFICATION: Row-level `[View]` in List view is named as opening "the single mistake's full logged detail," reusing the same underlying data as a Category Detail example — but no wireframe defines this as its own screen or state. Is it a read-only detail panel, or does it reopen mistake-logging-form.md in an edit mode (relevant for completing partial/incomplete entries flagged above)?]
