# Wireframe: Speaking Submissions History
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/speaking-coach/Specification.md

## Purpose
Let the learner browse every past speaking submission in one chronological list — including ones still mid-pipeline — and reopen any of them to see its transcript and feedback (or whatever step it's actually at).

## Layout
```
+-------------------------------------------------------------------+
| Header: Speaking Submissions                    [ + New Response ] |
+-------------------------------------------------------------------+
| Filter/Sort:  Status [All | Processing | Failed | Completed]        |
|               Part   [All | Part 1 | Part 2 | Part 3]               |
+-------------------------------------------------------------------+
| Main: submissions list (one row per submission, newest first)       |
|                                                                       |
|   Date        Part    Question                    Status            |
|   ------------------------------------------------------------      |
|   2026-07-29  Part 2  "Describe a skill you..."    ● Evaluating      |
|                                                     (still processing)|
|   ------------------------------------------------------------      |
|   2026-07-28  Part 1  "Do you enjoy cooking?"       ✓ Completed      |
|                                                     F&C 6.0 / LR 6.5 |
|                                                     / Gr 6.0          |
|   ------------------------------------------------------------      |
|   2026-07-27  Part 3  "How has technology..."       ✗ Evaluation     |
|                                                        failed         |
|                                                     (transcript ready)|
|   ------------------------------------------------------------      |
|   2026-07-25  Part 2  "Describe a memorable..."     ✗ Transcription  |
|                                                        failed         |
|   ------------------------------------------------------------      |
|   2026-07-20  Part 1  "What kind of music..."       ✓ Completed      |
|                                                     F&C 5.5 / LR 6.0 |
|                                                     / Gr 5.5          |
|   ... (older entries below, same row shape) ...                     |
+-------------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Date, Part, Question (per entry) | Minimum scannable identity for a submission — which question, which part, when it was answered (FR-13) | High |
| Status badge (per entry: Processing/Evaluating, Completed, Transcription Failed, Evaluation Failed) | Shows the submission's *current* pipeline status at a glance, using the same four learner-facing labels as the detail screen, so a still-processing or failed entry is never confused with a finished one (FR-13, FR-15) | High |
| Band summary snippet (Completed entries only) | Lets the learner recognize a result's rough outcome without opening it, mirroring Practice Log's scannable-row pattern | Medium |
| "Transcript ready" hint (Evaluation Failed entries only) | Signals that this failure isn't a total loss — the transcript already exists and is viewable even though evaluation isn't, consistent with FR-10/FR-5 | Medium |
| Status filter (All / Processing / Failed / Completed) | Lets the learner narrow the list to, e.g., only unfinished submissions worth checking on | Medium |
| Part filter (All / Part 1 / Part 2 / Part 3) | Lets the learner review history for one exam part at a time | Low |
| "+ New Response" action | Direct entry point to record a new submission (Speaking Submission & Feedback screen), kept visible at all times, not just in the empty state | Medium |
| Row tap/click target (whole row) | Opens that submission's detail view, which renders whatever step it's actually at — full feedback if Completed, transcript-only plus a labeled failure/in-progress state otherwise (FR-14, FR-15) | High |

## States
- **Empty**: no speaking submissions have ever been made (first-time state, not an error). Show "No speaking submissions yet" plus a direct call to action pointing at the Speaking Submission & Feedback screen ("Record your first response"), consistent with the same guided-empty-state pattern used on Practice Log History — the learner is pointed at the one action that populates this list, not left wondering if the screen is broken.
- **Loading**: brief placeholder while the submissions list loads; filter/sort controls remain visible (disabled) rather than disappearing, so the screen's structure doesn't jump once data arrives.
- **Error**: the list failed to load — stated explicitly as "couldn't load your speaking submissions," distinct from the empty state's "nothing submitted yet," so the learner doesn't mistake a fetch failure for having no history.
- **Populated**: filter/sort controls plus the chronological list, as sketched above. Each row is structurally self-contained regardless of its status — a still-processing entry shows its live pipeline status (e.g. "Evaluating") instead of a score, a failed entry shows which step failed instead of a score, and only a Completed entry shows the band summary — so the list never implies an unfinished or failed submission is done. Opening any row navigates to that submission's own detail view (the Speaking Submission & Feedback screen's populated/loading/error states, per that wireframe), which reads the submission's real current status rather than assuming it's fully evaluated — a Processing entry resumes/shows its actual step, a failed entry shows the correct labeled failure with its retry action, and only a Completed entry shows full feedback (FR-14, FR-15).
