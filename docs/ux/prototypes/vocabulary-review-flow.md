# Prototype: Evening Vocabulary Review (Spaced Repetition)
Journey: docs/ux/journeys/solo-ielts-learner-vocabulary-review.md

## Screen Sequence
1. docs/ux/wireframes/dashboard-overview.md — triggered by: opening the app for tonight's study session (entry point; journey step 1, "sees how many words are due")
2. docs/ux/wireframes/vocabulary-due-list.md — triggered by: tapping "Start Review" on the Dashboard's Vocabulary Due card
3. docs/ux/wireframes/vocabulary-review-session.md — triggered by: tapping "Start Review" (fresh queue) or "Resume Review" (interrupted queue) on Vocabulary Due List; internally loops Recall Prompt → Answer Revealed → Self-Assessment → auto-advance per word (journey steps 3-7), then transitions to its own internal "Session complete" state once the last word is assessed (journey step 8) — not a separate screen file
4. docs/ux/wireframes/add-vocabulary-word.md — triggered by any of three distinct entry points: "Add a new word" on Vocabulary Due List, "+ Add a word I just noticed" mid-session on Vocabulary Review Session, or "+ Add a word" from the Session-complete sub-state (journey steps 9-10, secondary/optional path)

## Transitions
| From | Trigger | To |
|---|---|---|
| Dashboard / Today Overview | Tapping "Start Review" on the Vocabulary Due card (Populated state) | Vocabulary Due List |
| Vocabulary Due List | Tapping "Start Review" (Populated state, no prior interrupted session) | Vocabulary Review Session — Recall Prompt, first due word |
| Vocabulary Due List | Tapping "Resume Review" (Populated state, shown instead of "Start Review" when a prior session was left in progress) | Vocabulary Review Session — resumes silently at the exact next unreviewed word |
| Vocabulary Due List | Tapping "Add a new word" | Add Vocabulary Word — see open question on return destination for this entry point |
| Vocabulary Due List (Empty state, nothing due) | Tapping "Add a new word" (the only action offered; no "Start Review" shown) | Add Vocabulary Word |
| Vocabulary Review Session — Recall Prompt | Tapping "Reveal Answer" | Vocabulary Review Session — Answer Revealed (meaning + example shown, same word) |
| Vocabulary Review Session — Answer Revealed | Tapping "Forgot" or "Remembered" | The assessment is saved immediately, then the queue auto-advances to the next word's Recall Prompt (or, if that was the last due word, to Session complete) |
| Vocabulary Review Session (any word in the loop) | Automatically, the instant the last due word's Forgot/Remembered choice is saved and the due queue is empty | Vocabulary Review Session — Session complete (internal state change, same screen) |
| Vocabulary Review Session (any point mid-loop) | Tapping "+ Add a word I just noticed" in the footer | Add Vocabulary Word (opens as an overlay; review session pauses in place underneath) |
| Vocabulary Review Session — Session complete | Tapping "+ Add a word" | Add Vocabulary Word — see open question on return destination for this entry point |
| Vocabulary Review Session — Session complete | Tapping "Back to Today" | Dashboard / Today Overview |
| Add Vocabulary Word (opened mid-session) | Tapping "Save Word" with Word + Meaning both non-empty and the save succeeds (brief confirmation shown, panel then closes) | Vocabulary Review Session, resumed at the exact word/position the learner left, queue intact |
| Add Vocabulary Word (opened mid-session) | Tapping "Cancel" or the "[x] Close" control | Vocabulary Review Session, resumed at the exact word/position the learner left, no data saved |
| Add Vocabulary Word (opened from Vocabulary Due List or from Session complete) | Tapping "Save Word" (success) or "Cancel" / "[x] Close" | Ambiguous — see Open Questions; assumed to return to whichever screen/state it was opened from, but the wireframe's copy and behavior are only specified for the mid-session case |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow. Steps 1-2 → Dashboard and Vocabulary Due List; steps 3-8 → Vocabulary Review Session (including its internal Session-complete state); steps 9-10 → Add Vocabulary Word.
- [ ] Every transition has a clear, unambiguous trigger. **Partially met.** The core review loop's triggers (Reveal Answer, Forgot/Remembered, auto-advance, Start/Resume Review) are explicit and unambiguous. However, the two non-mid-session entry points into Add Vocabulary Word (from Vocabulary Due List, and from Session complete) have clear *entry* triggers but ambiguous *return* behavior, since the Add Vocabulary Word wireframe's context strip and its "returns to your place in the queue" behavior are written only for the mid-session case. This is flagged below rather than resolved by assumption.
- [x] No screen exists in this flow without a stated purpose from the journey. Dashboard (step 1), Vocabulary Due List (step 2), Vocabulary Review Session (steps 3-8), Add Vocabulary Word (steps 9-10) all trace directly to journey touchpoints.
- [x] Open UX questions are listed below, not silently resolved.

Cross-check against journey Success Criteria: the flow carries the persona through Dashboard → Due List → the full Review Session loop → Session complete, satisfying "clears every word due that day in a single sitting... without needing to remember or manually figure out what's due" (steps 1-8). It also includes all three Add Vocabulary Word entry points, satisfying "a new word captured mid-session... saved with all four fields... without derailing the in-progress review queue" for the mid-session case specifically (steps 9-10). The flow does not stop short of either success criterion for the primary (mid-session) path; the two secondary entry points into Add Vocabulary Word are covered structurally but their exact return behavior is an open question, not a gap in coverage.

## Open Questions
- [NEEDS CLARIFICATION: The Add Vocabulary Word wireframe specifies its overlay behavior, context-strip copy ("Review paused — you'll return to your place in the queue after saving or closing"), and return-to-exact-position behavior only for the case where it's opened mid-session from Vocabulary Review Session. It does not specify what happens when opened from Vocabulary Due List's "Add a new word" action (no review session is in progress yet — there is no "place in the queue" to return to) or from the Session-complete sub-state's "+ Add a word" button (the queue is already finished). Does the panel show different copy in these two cases, and does Save/Cancel return the learner to Vocabulary Due List / Session complete respectively, or somewhere else (e.g., straight into a freshly started review)?]
- [NEEDS CLARIFICATION: The Dashboard's Vocabulary Due card action is labeled "Start Review," and Vocabulary Due List's primary action is also labeled "Start Review," but they trigger different outcomes — the Dashboard action lands on Vocabulary Due List (per journey step 2's touchpoint), while Due List's own "Start Review" is what actually begins the Recall Prompt loop. Is this double use of the same label intentional, or should the Dashboard card's action be relabeled (e.g., "Review Vocabulary") to avoid implying it jumps straight into the session?]
