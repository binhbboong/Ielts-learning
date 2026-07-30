# Wireframe: Vocabulary Due List
Supports journey: docs/ux/journeys/solo-ielts-learner-vocabulary-review.md (Step 2 — "Opens the vocabulary review flow and sees the size of today's due queue," touchpoint "Vocabulary Due List")

## Purpose
Let the learner confirm the scope of today's due-vocabulary queue and commit to starting the review — or divert to adding a new word — without the queue size itself feeling like a reason to defer.

## Layout
```
+--------------------------------------------------------------+
| Header: "Vocabulary Review" | back-to-dashboard link          |
+--------------------------------------------------------------+
| Nav (minimal) | Main content:                                 |
| - Dashboard    |  1. Due-queue summary (count + scope framing)|
| - Vocabulary   |  2. Composition breakdown (by interval/topic)|
|   (current)    |  3. Primary action: "Start Review"           |
| - Grammar      |  4. Secondary action: "Add a new word"       |
| - Settings     |  5. Reassurance / context note (streak,      |
|                |     partial-session resume, last reviewed)   |
+--------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements

| Element | Purpose | Priority |
|---|---|---|
| Due-queue count (e.g. "14 words due today") | Directly answers the journey-step goal: confirm scope before committing time | 1 (highest) |
| Scope-framing subtext (e.g. "~7 minutes" or "small batch" framing instead of a bare large number) | Mitigates the medium drop-off risk — reframes a large due count so it reads as a bounded, doable task rather than a chore | 1 |
| "Start Review" button | Primary action; the only thing the learner needs to decide once scope is confirmed | 1 |
| Composition breakdown (count by interval bucket — e.g. "3 first-review · 8 due-3-day · 3 due-7-day", or by topic) | Lets the learner see *why* the number is what it is (e.g. a missed day inflated it), which defuses the "queue looks large" anxiety with context rather than hiding the number | 2 |
| In-progress session indicator (if a prior session was interrupted) | Journey step 7 risk: sessions can be interrupted; this element makes resuming a partial queue explicit instead of silently restarting or losing progress | 2 |
| "Add a new word" link/button | Reaches Add Vocabulary Word flow referenced in journey steps 9-10, without requiring the learner to be mid-session first | 2 |
| Last-completed / streak note (e.g. "Last reviewed yesterday") | Low-cognitive-load reassurance; supports persona's value of not having to mentally track schedule adherence | 3 |
| Back-to-dashboard link | Escape hatch back to Today Overview (journey step 1) without penalty | 3 |

## States

- **Empty** (nothing due today): Reads as a positive/neutral milestone, not a dead end. Show a calm confirmation message (e.g. "Nothing due today — you're on schedule") plus a clearly secondary "Add a new word" action, since the learner may still want to log something. No "Start Review" button is shown (there is nothing to review); do not imply a failure or gap.
- **Loading**: Placeholder/skeleton for the due-count region and composition breakdown while the queue is computed; nav and header remain interactive; no action buttons are enabled until the real count resolves, so the learner never commits to a stale or guessed number.
- **Error** (queue couldn't be computed/loaded — e.g. local data store read failure): Neutral, non-alarming message stating the due queue couldn't be loaded right now, with a retry action. Explicitly does not show a fabricated or zero count, since a wrong "0 due" could cause the learner to skip a real review. "Add a new word" remains available since it doesn't depend on the due-queue data.
- **Populated** (normal case, 1+ words due): Due count is the first thing seen, immediately followed by the scope-framing subtext and composition breakdown so the number is never presented "bare." If a prior session was left in progress, the primary action becomes "Resume Review" (with an indication of how many remain) instead of "Start Review," addressing the mid-session interruption risk from the journey.
