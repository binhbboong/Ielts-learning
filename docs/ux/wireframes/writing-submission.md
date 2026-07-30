# Wireframe: Writing Submission & Feedback
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/writing-coach/Specification.md

## Purpose
Let the learner submit a Writing response tied to a specific task/question and task type, then receive and read back per-criterion IELTS feedback specific enough to act on — without ever losing their written text to a slow or failed evaluation.

## Layout

**A — Submission form (before evaluation; also the Error state, text intact)**
```
+---------------------------------------------------------------+
| Header: Writing Submission                       [ Cancel ]     |
+---------------------------------------------------------------+
| Section: Task                                                   |
|   Task type:   ( ) Task 1   ( ) Task 2                          |
|   Question/prompt:                                              |
|   [ e.g. "The chart below shows... Summarize the information  ]|
|   [  by selecting and reporting the main features..."          ]|
|   (learner-entered or selected; stays pinned/visible while      |
|    writing the response below)                                  |
+---------------------------------------------------------------+
| Section: Your Response                                          |
|   [                                                             ]|
|   [   (large multi-line essay text area)                       ]|
|   [                                                             ]|
|   [                                                             ]|
+---------------------------------------------------------------+
| (if retrying after a failure — see Error state below)           |
|   [!] Evaluation failed. Your response text is unchanged.       |
|       [ Retry Evaluation ]                                      |
+---------------------------------------------------------------+
| Footer:                              [ Submit for Feedback ]    |
+---------------------------------------------------------------+
```

**B — Feedback (after evaluation succeeds) — this is the primary payoff of the screen**
```
+---------------------------------------------------------------+
| Header: Feedback — Task 2, submitted 2026-07-29    [ Back ]     |
+---------------------------------------------------------------+
| Question: "Some people think... Discuss both views and give    |
|            your own opinion."                                  |
+---------------------------------------------------------------+
| Section: Scores — all four shown together, always              |
|                                                                   |
|   Task Response          6.5   Coherence & Cohesion       6.0   |
|   Lexical Resource       6.5   Grammatical Range & Acc.   5.5   |
|                                                                   |
|   (Overall, if shown at all: 6.0 — appears here beside the      |
|    four, never displayed alone on its own)                      |
+---------------------------------------------------------------+
| Section: Per-criterion feedback (expanded by default)           |
|                                                                   |
|   Task Response — 6.5                                           |
|     Strength: addresses both views the prompt asks for          |
|     Weakness: conclusion in paragraph 4 ("In the end, both      |
|       sides matter") restates the topic without a clear own     |
|       opinion, which the prompt explicitly requires             |
|                                                                   |
|   Coherence & Cohesion — 6.0                                    |
|     Weakness: paragraph 2 uses "Moreover" three times, causing  |
|       repetitive linking rather than varied cohesion             |
|                                                                   |
|   Lexical Resource — 6.5 / Grammatical Range & Accuracy — 5.5    |
|     (same shape: strength/weakness quoting the essay)            |
+---------------------------------------------------------------+
| Section: Sentence-level corrections (at least one, always shown)|
|                                                                   |
|   Original: "The government should to build more schools."      |
|   Corrected: "The government should build more schools."        |
|                                                                   |
|   Original: "It make people more happy in they daily life."     |
|   Corrected: "It makes people happier in their daily life."     |
|                                                                   |
|   ... (additional corrections, same original/corrected shape)   |
+---------------------------------------------------------------+
| Footer:  [ Write a Revised Response to This Question ]          |
|          [ View All My Submissions ]                            |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Task type selector (Task 1 / Task 2) | Required before evaluation; determines which first criterion (Task Achievement vs. Task Response) applies (FR-2) | High |
| Question/prompt field, pinned alongside response | Ties the submission to the exact task it answers so feedback is judged against what was actually asked (FR-1) | High |
| Response text area | Where the learner writes/pastes their essay; the thing being evaluated (FR-3) | High |
| Submit for Feedback action | Triggers evaluation; disabled until task type, question, and a non-blank response are present (FR-1–FR-3) | High |
| Cancel/abandon action | Lets the learner leave an in-progress, unsubmitted response without saving or evaluating it (FR-4) | Low |
| In-progress indicator (Loading state) | Explicit "this takes a moment" signal for the ~25s evaluation call, so the screen never reads as frozen or lost (FR-9) | High |
| Failure message + Retry (Error state) | Distinct from loading/blank; response text and question stay populated so the learner never retypes to retry (FR-10) | High |
| Four per-criterion scores, shown together | Core deliverable: never collapsed into a single number (FR-5, FR-8) | High |
| Overall score (if shown) | Only ever displayed alongside the four criteria and their feedback, never alone (FR-8) | Medium |
| Per-criterion strengths/weaknesses, quoting the essay | Makes feedback actionable per criterion rather than generic (FR-6) | High |
| Sentence-level corrections (original → corrected) | Concrete, quoted fix the learner can directly apply (FR-7) | High |
| "Write a Revised Response to This Question" action | Starts a new, independent submission for the same question so the learner can attempt to improve and later compare (resubmission, resolved in-scope in ImplementationPlan.md) | Medium |
| "View All My Submissions" link | Route to writing-history.md | Low |

## States
- **Empty**: fresh submission form — no task type selected, question blank, response blank. Submit is disabled until task type, question, and a non-blank response are all present (FR-1, FR-2, FR-3).
- **Loading**: after Submit is pressed, the form is replaced (or overlaid) with an explicit in-progress indicator — e.g. "Evaluating your response — this can take up to 30 seconds" plus a spinner/progress cue — never a blank or frozen screen, since the evaluation call runs synchronously for up to ~25s before the server-side timeout (FR-9). The learner's response text remains held, not discarded, during this wait.
- **Error**: evaluation failed or timed out — the response text and question/task type are still shown exactly as entered (layout A), with an explicit failure message ("Evaluation failed — your response wasn't lost") distinct in wording from the loading state, and a "Retry Evaluation" action that resubmits the same payload without requiring re-entry (FR-10).
- **Populated**: evaluation succeeded — layout B, all four criterion scores shown together (never only one combined score), per-criterion strengths/weaknesses quoting the learner's own text, and at least one sentence-level correction with original and corrected text side by side (FR-5, FR-6, FR-7, FR-8). This is the state that receives the most layout priority on the screen.
