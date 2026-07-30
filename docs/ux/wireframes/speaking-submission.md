# Wireframe: Speaking Submission & Feedback
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/speaking-coach/Specification.md

## Purpose
Let the learner record a spoken response to a specific speaking question, track its asynchronous transcription and evaluation through a visible step-by-step pipeline (leaving and returning later if needed), and view the read-only transcript plus three-criterion feedback as soon as each becomes available.

## Layout
```
+-------------------------------------------------------------------+
| Header: Speaking Practice                              [ Back ]    |
+-------------------------------------------------------------------+
| Question:                                                          |
|   Part 2 (cue card)                                    [Part badge]|
|   "Describe a skill you would like to learn. You should say:       |
|    what it is, why you want to learn it, how you would learn       |
|    it, and explain why it would be useful to you."                 |
+-------------------------------------------------------------------+
| Recorder:                                                          |
|   [ (o) Record ]   00:00 / 02:00 max        (idle, before capture) |
+-------------------------------------------------------------------+
| Pipeline status:                                                    |
|   [✓ Submitted] -> [✓ Transcribing] -> [✓ Transcribed]              |
|        -> [✓ Evaluating] -> [● Evaluated]                          |
|   (step indicator — each node's actual rendering varies by state,  |
|    see States section: pending / active / done / failed)           |
+-------------------------------------------------------------------+
| Transcript                                            (read-only)  |
|   "I'd like to talk about learning to play the piano. I've always  |
|    wanted to learn because... [full transcript text]"              |
|   (shown as soon as transcription completes, regardless of          |
|    evaluation's own state)                                          |
+-------------------------------------------------------------------+
| Feedback                                                            |
|   Fluency & Coherence     Band 6.0                                  |
|     "Generally maintains flow, with some hesitation when            |
|      elaborating on the second bullet point..."                    |
|   ---------------------------------------------------------------  |
|   Lexical Resource        Band 6.5                                  |
|     "Uses a reasonable range of vocabulary; some repetition of      |
|      basic words where a synonym would score higher..."             |
|   ---------------------------------------------------------------  |
|   Grammar                 Band 6.0                                  |
|     "Mix of simple and complex sentences; occasional errors with    |
|      verb tense do not impede meaning..."                           |
|   ---------------------------------------------------------------  |
|   Pronunciation           Not Assessed                              |
|     "This feature evaluates transcript text only — Pronunciation    |
|      cannot be assessed without audio-level analysis."              |
+-------------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels; the sketch above shows the fully "Evaluated" populated state, the richest variant. Earlier pipeline states show a subset of these regions — see States below.)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Question text + Part badge (1/2/3) | Grounds the recording in the exact question being answered and its IELTS part, so feedback is always interpretable against what was actually asked (FR-1, FR-2) | High |
| Record control + 120s timer/cap | Captures exactly one spoken response tied to the selected question; visible countdown against the 120s max so the learner isn't cut off unexpectedly | High |
| Pipeline step indicator | Makes the asynchronous, multi-step nature of processing visible as discrete steps (submitted → transcribing → transcribed → evaluating → evaluated) rather than one opaque spinner, so the learner understands what's currently happening and what's left (FR-11) | High |
| Transcript section | Shows the transcript as soon as it exists, independent of evaluation's outcome — lets the learner verify what was captured before trusting feedback built on it (FR-4, FR-5) | High |
| Retry transcription action (failure state only) | Lets the learner retry just the transcription step on the same recording, without re-recording (FR-6) | High |
| Feedback section: Fluency & Coherence, Lexical Resource, Grammar (each with band) | Presents the three assessed criteria as distinct items, each with its own band-level indicator, so the learner knows exactly which area to work on (FR-7, FR-8) | High |
| Pronunciation — "Not Assessed" line | Explicitly and visibly states Pronunciation was not assessed, so its absence is never mistaken for a perfect score or a bug (FR-9) | High |
| Retry evaluation action (failure state only) | Lets the learner retry just the evaluation step, keeping the existing transcript, without re-recording or re-transcribing (FR-10) | High |
| Submission confirmation (immediately post-record) | Distinct acknowledgment that the response was received and processing has begun, separate from any later transcription/evaluation outcome (FR-3) | Medium |
| "Leave and come back" affordance (implicit — just Back/navigation) | Reinforces that the learner is free to close the app mid-pipeline; nothing on screen requires continuous waiting (FR-12) | Medium |

## States

- **Empty**: No question selected yet and no recording made. Shows the question-selection control (or a pre-selected question passed in from elsewhere) and an idle Record button at 00:00/02:00; no pipeline indicator, transcript, or feedback region is shown until a recording is actually submitted. Record/Submit is disabled until a question is selected (FR-1).

- **Loading** (the asynchronous pipeline — NOT one generic spinner; each sub-state below renders its own step indicator and available content):
  - *Recording*: mic active, timer counting up toward 02:00, with a visible warning/auto-stop as it nears the 120s cap.
  - *Submitted / uploading*: pipeline shows `[● Submitted] -> [ Transcribing ] -> ...` (first node active/spinning, rest pending). A distinct confirmation message ("Response received, processing has begun") is shown here — separate from any later outcome (FR-3). No transcript or feedback region yet.
  - *Transcribing*: pipeline shows `[✓ Submitted] -> [● Transcribing] -> [ Transcribed ] -> ...` (second node active). Still no transcript or feedback region — nothing to show yet.
  - *Transcribed, evaluation pending*: pipeline shows `[✓ Submitted] -> [✓ Transcribing] -> [✓ Transcribed] -> [● Evaluating] -> [ Evaluated ]`. The **Transcript section is now shown and populated**, read-only, even though evaluation hasn't finished — this is a legitimate populated sub-state, not "still loading everything" (FR-5). Feedback section is absent or shows a plain "Evaluation in progress" placeholder, clearly separate from the transcript above it.
  - *Reopened mid-pipeline from a previous visit*: identical rendering to whichever of the above sub-states the submission is actually at — the screen does not assume "just submitted"; on load it reads the submission's real persisted status and renders that step's indicator and content directly (FR-12). A brief "Resuming..." indicator may show while the app re-triggers the next pipeline call, but the step indicator itself reflects true state, not a reset spinner.

- **Error** (two distinct, separately-retryable failure states — never a single generic "failed"):
  - *Transcription failed*: pipeline shows `[✓ Submitted] -> [✗ Transcription failed]`, with the remaining steps (Transcribed/Evaluating/Evaluated) grayed out/not reached. Message explicitly labeled "Transcription failed" (not just "Error"). No transcript and no feedback section shown, since none exists yet. A **"Retry transcription"** action re-attempts transcription on the already-uploaded recording — no new recording required (FR-6). This state renders identically whether reached moments after submission or on a later visit.
  - *Evaluation failed*: pipeline shows `[✓ Submitted] -> [✓ Transcribing] -> [✓ Transcribed] -> [✗ Evaluation failed]`. Message explicitly labeled "Evaluation failed," visually distinct from "Transcription failed." The **Transcript section remains fully shown** (already produced, unaffected by this failure — FR-10). No feedback section (never completed), but a **"Retry evaluation"** action re-attempts evaluation using the existing transcript — no re-recording, no re-transcription. This state also renders identically on a later revisit.

- **Populated** (two legitimate sub-states, both real "populated" outcomes):
  - *Transcribed, evaluation pending or in progress*: as described under Loading above — transcript visible and read-only, feedback not yet available. Included here explicitly because the transcript being viewable is itself a completed, populated outcome per FR-5, not merely a loading placeholder.
  - *Evaluated (fully complete)*: as sketched above — pipeline shows all five nodes complete, transcript shown, and feedback shown as three distinct items (Fluency & Coherence, Lexical Resource, Grammar), each with a band-level indicator, plus the Pronunciation "Not Assessed" line always present (FR-7, FR-8, FR-9). This is the terminal state and renders identically whether reached right after evaluation finishes or opened fresh on any later visit (FR-14).
