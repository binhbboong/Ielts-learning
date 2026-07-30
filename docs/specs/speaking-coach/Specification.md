# Specification: AI-Assisted Speaking Coaching
Related UX: none yet — no wireframe/journey exists for this epic (it's a new epic, not carried over from the client-only architecture)

## Status
Draft

## Overview
This feature lets a self-directed IELTS learner submit a spoken response to a specific speaking
question and receive AI-generated feedback scored against the official IELTS Speaking criteria.
Until now this capability could not exist at all: under the prior client-only architecture there
was no backend able to call an AI provider or a speech-to-text service, so Speaking feedback was
explicitly out of scope. The full-stack pivot makes it a real, buildable epic for the first time
(PRD Epic-8), alongside its sibling, AI-Assisted Writing Coaching (Epic-7).

A spoken submission is evaluated in two chained steps — the response is first transcribed to
text, then that transcript is evaluated — and each step can succeed or fail independently. This
specification treats the transcript as a real, learner-visible outcome in its own right, not a
hidden intermediate value, and requires the learner to be told plainly which step is holding up
a result or which step failed, rather than receiving one generic "something went wrong" message.
Feedback covers Fluency & Coherence, Lexical Resource, and Grammar — the three IELTS Speaking
criteria this feature can respond to from a transcript alone. Pronunciation is an official
fourth Speaking criterion, but estimating it from text without audio-level analysis is
unreliable; per the PRD and Vision, this feature must report Pronunciation as explicitly "not
assessed" rather than guess or silently drop it. This spec does not address whether the
underlying evaluation call can reliably complete within any hosting platform's execution time
limit — that is a flagged, unresolved infrastructure risk in the architecture — but it does
define what the learner must see and be able to do while a result is pending or has failed,
independent of how that risk is eventually mitigated.

## User Scenarios
- As a solo IELTS learner, I want to submit a spoken response to a specific speaking question, so
  that my feedback is always evaluated against the question I was actually answering.
- As a solo IELTS learner, I want to see the transcript produced from my spoken response, so that
  I can verify it captured what I actually said before I trust the feedback built on it.
- As a solo IELTS learner, I want feedback broken out separately for Fluency & Coherence, Lexical
  Resource, and Grammar, so that I know exactly which area to work on rather than one blended
  comment.
- As a solo IELTS learner, I want to be told explicitly that Pronunciation was not assessed, so
  that I don't mistake its absence for a perfect score or a system bug.
- As a solo IELTS learner, I want to know my submission is being processed and be free to leave
  and come back later, so that I'm not stuck staring at a spinner while two external steps run.
- As a solo IELTS learner, I want to know specifically whether transcription or evaluation failed
  when something goes wrong, so that I understand what to retry instead of just seeing "failed."
- As a solo IELTS learner, I want to retry a failed step without re-recording my answer from
  scratch, so that a transient failure doesn't cost me redoing the whole submission.
- As a solo IELTS learner, I want to come back later and open any past submission to see its
  transcript and feedback again, so that I can track what I was told and revisit it over time.

## Functional Requirements

### Submitting a spoken response
- FR-1: The system MUST require the learner to select or specify a speaking question/prompt
  before a spoken response can be submitted, and MUST NOT accept a spoken response with no
  associated question/prompt.
- FR-2: The system MUST let the learner submit one spoken audio response tied to the selected
  question/prompt as a single submission.
- FR-3: Upon successful submission, the system MUST present confirmation that the response was
  received and has begun processing, distinct from any later transcription or evaluation outcome.

### Transcription
- FR-4: The system MUST produce a text transcript of the submitted spoken response as a required
  step that completes before evaluation begins — evaluation MUST NOT run against a response that
  has not yet been transcribed.
- FR-5: The system MUST make the transcript viewable to the learner on its own, independent of
  whether evaluation has subsequently succeeded, failed, or is still pending.
- FR-6: If transcription does not complete successfully, the system MUST present a state
  distinctly labeled as a transcription failure, MUST NOT proceed to evaluation, and MUST let the
  learner retry transcription for that same submitted response without requiring a new recording.

### Evaluation feedback
- FR-7: Once a transcript exists, the system MUST produce feedback that assesses the spoken
  response individually against three criteria — Fluency & Coherence, Lexical Resource, and
  Grammar — with each criterion's feedback presented as its own distinct item, not merged into one
  combined comment.
- FR-8: For each of the three criteria in FR-7, the system MUST include a band-level indicator
  alongside its qualitative feedback.
- FR-9: The system MUST explicitly report Pronunciation as "not assessed" as part of every
  completed evaluation result, rather than omitting it from the result or presenting an estimated
  Pronunciation score.
- FR-10: If evaluation does not complete successfully after transcription has already succeeded,
  the system MUST present a state distinctly labeled as an evaluation failure, separate from a
  transcription failure, MUST retain the already-produced transcript, and MUST let the learner
  retry evaluation without requiring the response to be re-recorded or re-transcribed.

### Waiting and processing
- FR-11: While transcription or evaluation is in progress for a submission, the system MUST
  present a state that indicates processing is underway, distinguishable from both a completed
  result and either failure state.
- FR-12: The system MUST let the learner leave an in-progress submission (navigate elsewhere or
  end the session) and return later to view whatever outcome exists at that time, rather than
  requiring the learner to keep waiting continuously for a result.

### Retrieving past submissions
- FR-13: The system MUST let the learner retrieve a list of their previously submitted speaking
  responses, showing at minimum the associated question/prompt, the submission date, and the
  current status (processing, transcription failed, evaluation failed, or completed).
- FR-14: For any submission with a completed evaluation, the system MUST let the learner view that
  submission's transcript together with its full feedback (all three assessed criteria plus the
  Pronunciation "not assessed" marker) at any later time.
- FR-15: For a submission in a failed state, the system MUST clearly indicate, within the list and
  the submission's own view, which specific step failed (transcription or evaluation), consistent
  with the distinction required by FR-6 and FR-10.

## Out of Scope
- Live, real-time, turn-by-turn conversational speaking practice with an AI-simulated examiner —
  this epic covers submit-a-response-and-receive-feedback only, not an interactive session.
- Pronunciation scoring or estimation of any kind, whether derived from the transcript, from
  audio-level analysis, or otherwise — an explicit PRD and Vision non-goal for this phase; a
  dedicated speech-assessment capability is a separate, later decision.
- Video capture or evaluation of any kind.
- Aggregating or comparing scores across multiple submissions or questions into a combined
  "speaking ability" view — that belongs to Epic-4 (Practice Result Tracking & Progress
  Visibility), not this feature.
- Editing or correcting the transcript's text before evaluation runs — see Open Questions.
- Human or tutor review of submissions.
- Automatic or scheduled evaluation that is not triggered by an explicit learner submission (per
  the PRD's cost-conscious AI usage constraint).
- Logging a speaking practice result completed outside this application (e.g., a self-assessed
  score for an external speaking session) — that is Epic-4's practice-result logging, not this
  epic.
- Any retention, deletion, or long-term storage policy for submitted audio recordings after
  transcription — not addressed by this specification.

## Open Questions
- [NEEDS CLARIFICATION: Is there a maximum recording length per submission, and/or a limit on how
  many speaking submissions the learner may evaluate in a given period? Real AI and
  speech-to-text usage costs are now a PRD constraint, and IELTS Speaking answers vary widely in
  expected length (a short Part 1 answer vs. a longer Part 2 long-turn response), so this affects
  both cost and what "one submission" should reasonably contain.]
- [NEEDS CLARIFICATION: Should the feature distinguish IELTS Speaking's three exam parts (Part 1
  short-answer questions, Part 2 long-turn cue-card response, Part 3 discussion), each with
  different expected response length and prompt style, or should all speaking prompts be treated
  uniformly by this feature? This affects prompt selection, recording length expectations, and
  possibly how feedback is framed.]
- [NEEDS CLARIFICATION: Where do speaking questions/prompts come from — a curated question bank
  maintained within the application, or free-text prompts the learner supplies themselves? The
  PRD describes submitting a response "tied to" a question but does not establish the source.]
- [NEEDS CLARIFICATION: Can the learner re-record and resubmit a new spoken response for a
  question/prompt they have already submitted and received completed feedback for, and if so, are
  prior submissions for that same question retained alongside the new one or replaced?]
- [NEEDS CLARIFICATION: Should the learner be able to edit or correct the transcript's text before
  evaluation runs? Allowing edits could correct transcription errors that would otherwise unfairly
  skew Fluency & Coherence or Grammar feedback, but evaluating an edited transcript risks scoring
  the learner's writing skill rather than what they actually said.]

## Acceptance Criteria
- [ ] A spoken response cannot be submitted without an associated question/prompt (FR-1).
- [ ] A submission ties exactly one spoken response to the selected question/prompt (FR-2).
- [ ] A successful submission shows confirmation that processing has begun, distinct from later
      transcription/evaluation outcomes (FR-3).
- [ ] Evaluation never begins before transcription has completed for a given submission (FR-4).
- [ ] The transcript can be viewed on its own regardless of whether evaluation has succeeded,
      failed, or is still pending (FR-5).
- [ ] A transcription failure is shown in a state distinctly labeled as such, evaluation does not
      run, and transcription can be retried without a new recording (FR-6).
- [ ] A completed evaluation shows Fluency & Coherence, Lexical Resource, and Grammar feedback as
      three distinct items, not one combined comment (FR-7).
- [ ] Each of the three criteria's feedback includes a band-level indicator (FR-8).
- [ ] Every completed evaluation explicitly states Pronunciation as "not assessed" — never
      omitted and never an estimated score (FR-9).
- [ ] An evaluation failure after successful transcription is shown in a state distinctly labeled
      as such and separate from a transcription failure, the transcript remains available, and
      evaluation can be retried without re-recording or re-transcribing (FR-10).
- [ ] While a submission is processing, its state is visibly distinguishable from both a completed
      result and either failure state (FR-11).
- [ ] The learner can leave an in-progress submission and later return to see its current outcome,
      without needing to keep the session open continuously (FR-12).
- [ ] The list of past submissions shows question/prompt, submission date, and current status for
      every submission (processing, transcription failed, evaluation failed, or completed)
      (FR-13).
- [ ] Opening a completed submission at any later time shows its transcript and full feedback,
      including the Pronunciation "not assessed" marker (FR-14).
- [ ] A failed submission's list entry and detail view both indicate which specific step failed,
      matching the distinction from FR-6/FR-10 (FR-15).
