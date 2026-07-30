# Wireframe: Writing Submissions History
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/writing-coach/Specification.md

## Purpose
Let the learner browse every past Writing submission at a glance, see when a question was attempted more than once, and reopen any one of them to review its full original feedback again.

## Layout
```
+---------------------------------------------------------------+
| Header: My Writing Submissions                                  |
+---------------------------------------------------------------+
| Filter/Sort: Task type [All | Task 1 | Task 2]                  |
|              Sort      [Newest first | Oldest first]             |
+---------------------------------------------------------------+
| Main: submissions list (one row per submission, grouped when    |
|       multiple attempts share the same question)                |
|                                                                   |
|   "Some people think... Discuss both views..."     (Task 2)     |
|     - 2026-07-29  Overall 6.0  (TR 6.5 / CC 6.0 / LR 6.5 / GRA 5.5)|
|       Attempt 2 of this question — previous attempt: 5.0        |
|     - 2026-07-20  Overall 5.0  (TR 5.0 / CC 5.5 / LR 5.0 / GRA 4.5)|
|       Attempt 1 of this question                                |
|                                                                   |
|   "The chart below shows..."                       (Task 1)     |
|     - 2026-07-22  Overall 6.5  (TR 7.0 / CC 6.5 / LR 6.0 / GRA 6.5)|
|       Attempt 1 of this question                                |
|                                                                   |
|   ... (older entries/questions below, same row shape) ...       |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Question text (per group/row) | Identifies which task/question the submission answered, at a glance (FR-12) | High |
| Submission date (per row) | Lets the learner place the entry in time and tell attempts apart (FR-12) | High |
| Task type (Task 1 / Task 2) | Minimum identifying detail required by FR-12 | High |
| Overall + four per-criterion scores (at a glance, per row) | Enough score detail to distinguish one submission from another without opening it (FR-12) | High |
| "Attempt N of this question" / previous-score annotation | Makes a resubmission relationship visible so the learner can see whether a revision improved, without requiring the learner to spot matching question text themselves | High |
| Row click / "View Feedback" action | Opens the same full feedback detail view as writing-submission.md's Populated state — all four criteria, strengths/weaknesses, corrections, unchanged from when produced (FR-13) | High |
| Task type filter | Narrows the list when the learner only cares about one task type right now | Medium |
| Sort order (Newest/Oldest first) | Supports both "what did I just write" and "how did I start out" review habits | Medium |
| "Submit a New Response" action | Routes to writing-submission.md; present in both populated and empty states | Medium |

## States
- **Empty**: the learner has never successfully submitted a Writing response — show "You haven't submitted any Writing responses yet" plus a direct action to writing-submission.md ("Submit your first response"), not a blank or broken-looking list (FR-14).
- **Loading**: brief placeholder while the submissions list loads from the server; filter/sort controls remain visible (disabled) rather than disappearing, so the screen's structure doesn't shift once data arrives.
- **Error**: the list failed to load — state this explicitly as "Couldn't load your submissions — try again", worded distinctly from the empty state's "you haven't submitted any yet," with a retry action; the same distinction applies inside an individual submission's feedback detail view if that fetch fails after being opened from this list (FR-15).
- **Populated**: filter/sort controls plus the list of past submissions, grouped by question where more than one attempt exists and annotated with the attempt number and prior score so improvement (or its absence) is visible without opening each entry, as sketched above (FR-12, FR-13).
