# Wireframe: Reading Exercise & Result
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-lesson.md

## Purpose
Let the learner read an AI-generated passage targeted at their own recent mistakes/vocabulary, answer comprehension questions, and get an objective score immediately on submission.

## Layout

**A — Answering (populated)**
```
+---------------------------------------------------------------+
| Header: Reading — Today's Passage              [ Back to Today ]|
+---------------------------------------------------------------+
| Section: Why this passage                                       |
|   "Targets: conditional clauses, the word 'nevertheless'"       |
|   (ties back to a specific mistake/vocab item — pinned while    |
|    reading, not just shown once and scrolled away)               |
+---------------------------------------------------------------+
| Section: Passage (left/main, scrollable, stays visible)         |
|   [ ~300-400 word passage text ]                                |
|                                                                   |
+---------------------------------------------------------------+
| Section: Questions (below or beside passage)                    |
|   Q1. According to the passage, ...?                             |
|       ( ) Option A   ( ) Option B   ( ) Option C   ( ) Option D  |
|   Q2. ...                                                        |
|       ( ) ...                                                    |
|   ... (5-8 questions typical)                                    |
+---------------------------------------------------------------+
| Footer:                                   [ Submit Answers ]     |
+---------------------------------------------------------------+
```

**B — Result (after submission) — primary payoff**
```
+---------------------------------------------------------------+
| Header: Reading — Result                        [ Back to Today]|
+---------------------------------------------------------------+
| Score: 6 / 8 correct                                             |
+---------------------------------------------------------------+
| Section: Per-question review                                     |
|   Q1. [correct]  Your answer: B                                  |
|   Q2. [wrong]    Your answer: A   Correct: C                     |
|       -> [ Add to Mistake Notebook ] (pre-filled, one tap)        |
|   ... (same shape per question)                                  |
+---------------------------------------------------------------+
| Footer:                              [ Back to Today's Lesson ]  |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| "Why this passage" personalization note | Makes the personalization tie-back visible during the exercise itself, not just claimed on the Daily Overview — directly serves the journey's success criterion | High |
| Passage text | The generated reading material itself | High |
| Multiple-choice questions | Objectively scorable comprehension check (journey step 3) | High |
| Submit Answers action | Triggers immediate, local scoring — no AI call needed at this step, so no meaningful wait (journey step 4: "no waiting") | High |
| Score summary | Instant, objective feedback | High |
| Per-question correct/wrong + correct answer shown | Lets the learner see exactly what they missed, not just a final count | High |
| "Add to Mistake Notebook" quick action on wrong answers | Closes the loop into Epic-3 with one tap instead of a separate manual-entry flow, directly serving PRD Epic-9's scope ("flagging wrong answers as candidate entries for the mistake log") | High |
| Back to Today's Lesson | Returns to the Daily Overview to continue with another skill (journey step 2, any order) | Medium |

## States
- **Empty**: should not occur — a passage/questions are generated before this screen is reachable (Daily Overview gates entry on "Ready" state).
- **Loading**: brief, only for local scoring after Submit — expect near-instant; if a spinner is needed at all it should be sub-second, distinct from Writing/Speaking's multi-second AI wait.
- **Error**: passage/questions failed to load despite the Daily Overview showing "Ready" (edge case, e.g. stale state) — show a distinct message ("Couldn't load today's passage — [ Retry ]") rather than a blank passage area.
- **Populated**: layout A while answering, layout B after submission — B receives the most layout priority as the payoff state, per the journey's emphasis on instant, objective feedback.
