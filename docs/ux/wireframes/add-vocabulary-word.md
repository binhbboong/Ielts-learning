# Wireframe: Add Vocabulary Word
Supports journey: docs/ux/journeys/solo-ielts-learner-vocabulary-review.md (Steps 9-10 — "Notices a new word worth keeping and opens the add-word form, ideally without leaving the review context" / "Fills in word, meaning, example, and topic, then saves it," touchpoint "Add Vocabulary Word screen" / "... — save confirmation")

## Purpose
Let the learner capture a new word (word, meaning, example, topic) in under 30 seconds without abandoning an in-progress review session, and get it onto the spaced-repetition schedule starting at the 1-day interval.

## Layout
```
+--------------------------------------------------------------+
| Overlay panel header: "Add Vocabulary Word"      [x] Close     |
+--------------------------------------------------------------+
| Context strip: "Review paused — you'll return to your place   |
|  in the queue after saving or closing"                        |
+--------------------------------------------------------------+
| Main content (form, in priority order):                       |
|  1. Word *      [ text input, auto-focused ]                  |
|  2. Meaning *   [ textarea ]                                   |
|  3. Example     [ textarea, optional ]                         |
|  4. Topic       [ text input w/ suggestions, optional ]        |
+--------------------------------------------------------------+
| Inline message area (validation / save error — appears here)  |
+--------------------------------------------------------------+
| Actions:                    [ Cancel ]      [ Save Word ]      |
+--------------------------------------------------------------+
| Schedule note: "Saved words start at the 1-day review interval"|
+--------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels. Rendered as an overlay/side panel above the
Vocabulary Review Session screen, not a full page navigation — this is the direct mitigation for
the step 9 drop-off risk: leaving the review context entirely invites "do it later.")

## Key Elements

| Element | Purpose | Priority |
|---|---|---|
| Word input (required) | Core identity of the entry; journey step 10 lists it first and nothing can be saved without it | 1 (highest) |
| Meaning input (required) | The other field the review session actually tests (recall-the-meaning); without it the word can't function in spaced repetition | 1 (highest) |
| Save Word button | Primary action; completes the journey-10 goal of getting the word onto the schedule with no extra setup | 1 (highest) |
| Cancel / Close (x) | Escape hatch back to the paused review session with no penalty; directly addresses the step 9 risk of feeling trapped in the add-word flow | 2 |
| Context strip ("Review paused...") | Reassures the learner the review queue is not lost or abandoned, reducing the "do it later" temptation from step 9 | 2 |
| Example textarea (optional) | Supports recall later but not required to get the word scheduled; secondary per the journey's emphasis order | 3 |
| Topic input (optional, with suggestions from existing topics) | Aids later filtering/grouping; least essential to the immediate goal of "get it on the schedule" | 3 |
| Schedule note ("...1-day interval") | Confirms the journey-10 outcome (spaced-repetition entry point) so the learner isn't left wondering what happens next | 3 |
| Inline validation/error message area | Surfaces missing-required-field or save-failure feedback in place, without a full-page error screen | 2 |

**Ambiguity noted:** the app is client-only with no backend (per Vision/Architecture), so a "save" is really a local write (e.g. IndexedDB/localStorage). A visible loading state is still specified below for perceived feedback and to prevent double-submit, even though the write is expected to be near-instant; a real failure here is more likely to be a storage-quota or corruption issue than a network error.

## States

- **Empty**: Panel opens with all fields blank, Word field auto-focused. Meaning, Example, and Topic are empty placeholders (e.g. "e.g. to procrastinate"). Save Word is disabled until both Word and Meaning have content, since those are the two fields the schedule actually depends on. The review session underneath remains paused, not exited — this is the direct fix for the step 9 "abandon the flow" risk.
- **Loading** (save in progress): Save Word shows a brief in-progress indicator (e.g. "Saving...") and is disabled to prevent double-submit; Word/Meaning/Example/Topic fields become read-only but keep their typed values visible; Cancel/Close is disabled for the moment so the learner can't dismiss mid-write and lose the entry.
- **Error** (save failed — e.g. local storage write/quota failure): All four fields retain exactly what the learner typed — nothing is cleared or reset. An inline message appears in the message area (e.g. "Couldn't save this word — your entry hasn't been lost. Try again."). Save Word re-enables for an immediate retry; Cancel/Close remains available if the learner chooses to abandon, but only as their own choice, never as a side effect of the failure.
- **Populated** (word + meaning filled, optionally example/topic too): Save Word becomes enabled once Word and Meaning are non-empty. On successful save, the panel shows a brief confirmation (e.g. "Added — starts review in 1 day") and then closes, returning the learner to the exact point they left in the review session — satisfying the journey's "without derailing the in-progress review queue" success criterion.
