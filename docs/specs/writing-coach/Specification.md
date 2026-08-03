# Specification: AI-Assisted Writing Coaching
Related UX: none yet — no wireframe/journey exists for this epic (it's a new epic, not carried over from the client-only architecture)

## Revision 2 — Level-appropriate prompts and grading

Decision: `docs/adr/2026-08-03-writing-speaking-level-adaptation.md`.

- FR-17: When `daily-lesson-plan` has generated today's (or the effective day's) Writing prompt
  for the learner, the submission screen MUST pre-fill the task type and question text from it
  rather than requiring the learner to source their own — the learner MAY still edit or replace
  the pre-filled text.
- FR-18: The generated prompt's complexity MUST vary by the learner's current phase: foundation
  and core-skills phases get a short (~100-150 word), concrete, everyday-topic question;
  later phases get the standard ~250-word opinion/discussion essay.
- FR-19: When a submission is tied to a specific day, evaluation MUST be calibrated to the
  learner's target band/phase for that day (realistic expectations for that level) rather than a
  flat band-9 standard — the returned `overall_band` MUST still be an honest assessment, not
  inflated, and criteria feedback MUST still cite exact submitted wording. A submission not tied
  to any day (free/ad hoc practice) grades with no level context, unchanged from before.

## Status
Draft

## Overview
This feature lets a self-directed IELTS learner submit a Writing response — tied to the
specific task/question it answers — and receive feedback scored against the four official
IELTS Writing criteria (Task Response/Achievement, Coherence & Cohesion, Lexical Resource,
Grammatical Range & Accuracy), with corrections specific enough to point at exact sentences
or phrases in the submission. This is PRD Epic-7 and directly serves Vision goal G-6: without
a human grader, a solo learner otherwise has no reliable way to know their Writing band or
exactly what to fix. This epic was explicitly out of scope under the prior client-only
architecture (there was no backend able to safely call an AI provider) and is a new, buildable
capability under the full-stack architecture described in
`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`.

The persona's defining pain point here is twofold: not knowing *where* they stand against the
real exam rubric (as opposed to a vague self-assessment), and not knowing *what specifically*
to change in their own writing. A single overall number does not solve either problem — it is
the per-criterion breakdown and the sentence-level corrections that make the feedback
actionable. Producing that feedback depends on an external AI evaluation step that is neither
instant nor guaranteed to succeed, so this feature also covers how the learner experiences
waiting for, retrieving, and recovering from that evaluation. What the evaluation is graded
by, how it is computed, and how results are stored are implementation concerns outside this
specification.

## User Scenarios
- As a solo IELTS learner, I want to submit a Writing response together with the exact
  task/question it answers, so that the feedback I get back is judged against what I was
  actually asked to write, not the essay text in isolation.
- As a solo IELTS learner, I want to see a separate score for each of the four official IELTS
  Writing criteria, so that I know exactly which dimension of my writing is weakest instead of
  one blended number that hides it.
- As a solo IELTS learner, I want strengths, weaknesses, and corrections that point at specific
  sentences or phrases from my own submission, so that I know exactly what to fix rather than
  receiving generic advice that could apply to any essay.
- As a solo IELTS learner, I want a clear indication that my submission is being evaluated
  while I wait, so that I don't wonder whether my submission was lost or the app is broken.
- As a solo IELTS learner, I want my submitted text preserved and an explicit failure message
  if evaluation doesn't complete, so that I never have to retype my essay to try again.
- As a solo IELTS learner, I want to come back later and reopen the full feedback for any essay
  I've previously submitted, so that I can review past corrections without having to remember
  them or resubmit the same essay.
- As a solo IELTS learner, I want a clear empty state the first time I have no past submissions,
  so that I understand where to go to submit my first one rather than seeing a blank or broken
  screen.

## Functional Requirements
- FR-1: The system MUST require a learner to provide both the Writing response text and the
  specific task/question it responds to before a submission can be evaluated; the system MUST
  NOT accept or evaluate a response with no associated task/question.
- FR-2: The system MUST require the learner to indicate which IELTS Writing task the response
  answers (Task 1 or Task 2), since the applicable first criterion (Task Achievement vs. Task
  Response) depends on it.
- FR-3: The system MUST NOT allow submission of an empty or effectively blank response for
  evaluation.
- FR-4: The system MUST let the learner abandon an in-progress, unsubmitted response at any
  point without it being evaluated or saved.
- FR-5: For every successfully evaluated submission, the system MUST produce a distinct score
  for each of the four official IELTS Writing criteria (Task Response/Achievement, Coherence &
  Cohesion, Lexical Resource, Grammatical Range & Accuracy) — never only a single combined
  score in place of the four.
- FR-6: For each of the four criteria, the system MUST provide written feedback (strengths
  and/or weaknesses) that references a specific part of the learner's own submission (e.g., a
  quoted or identified sentence/phrase) rather than a statement generic enough to apply to any
  essay. A criterion's feedback consisting only of a generic statement (e.g., "your grammar
  needs work" with no example from the submission) does not satisfy this requirement.
- FR-7: The system MUST provide sentence-level corrections: for at least one specific problem
  identified in the submission, the system MUST show the original sentence or phrase from the
  learner's own text alongside a corrected or improved version of it.
- FR-8: If the system presents an overall/combined score for a submission, it MUST always be
  presented together with the four per-criterion scores and the specific feedback from FR-6 and
  FR-7 in the same result — never displayed alone as the only feedback given.
- FR-9: While a submitted response is being evaluated, the system MUST present the learner with
  an explicit in-progress/waiting indication, and MUST NOT present a blank, frozen, or
  ambiguous screen that could be mistaken for the submission having failed silently.
- FR-10: If an evaluation attempt fails to complete, the system MUST preserve the learner's
  submitted response text and task/question, present an explicit failure indication distinct
  from the in-progress state, and let the learner retry evaluation without re-entering the
  response.
- FR-11: The system MUST persist every submission that completes evaluation successfully —
  including the response text, the task/question it answered, the task type, and the full
  feedback returned — so it can be retrieved again later in a separate session.
- FR-12: The system MUST let the learner browse a list of their own past submissions, showing
  at minimum the date submitted, the task type, and enough of the result (e.g., the overall or
  per-criterion scores) to distinguish one submission from another.
- FR-13: The system MUST let the learner select any one past submission from that list and view
  its full original feedback again — all four criterion scores, the associated strengths and
  weaknesses, and the sentence-level corrections — exactly as it was produced at evaluation
  time.
- FR-14: When the learner has never successfully submitted a Writing response, the submission
  list MUST present a message directing them to submit one, rather than an empty or blank list.
- FR-15: The system MUST distinguish, within the submission list and within an individual past
  submission's feedback, between "nothing submitted yet" / no result and a genuine failure to
  load existing data, using wording that makes clear which situation applies.
- FR-16: The system MUST NOT allow a learner to view, retrieve, or evaluate another person's
  Writing submissions or feedback.

## Out of Scope
- Showing a model/sample essay for the submitted task alongside the returned feedback — this
  feature returns feedback on the learner's own submission only.
- Any human review, override, or manual adjustment of AI-generated feedback.
- Real-time or inline grammar/style checking while the learner is still typing — evaluation
  happens only after explicit submission (also a cost-consciousness constraint per the PRD).
- Editing an already-evaluated submission's text in place and having its existing feedback
  update — a past submission's stored feedback is immutable once produced (see Open Questions
  for whether a *new* resubmission of a revised essay is separately in scope).
- Comparing Writing scores or feedback across multiple learners, or any shared/social view of
  submissions.
- Plagiarism or AI-generated-text detection on the submitted response.
- Speaking submissions and Speaking-specific criteria (PRD Epic-8, separate feature).
- Any large-scale exam-simulation or timed full-mock-test experience around the submission.
- Weekly reports, smart recommendations, or PDF export of feedback (not yet backed by a Vision
  goal per the PRD's product-level Out of Scope).

## Open Questions
- [NEEDS CLARIFICATION: Is there a limit on how many Writing submissions a learner can evaluate
  (per day, per week, or in total)? The PRD constrains AI usage to be cost-conscious and
  explicit-submission-only, but does not state a specific cap. This affects whether FR-1/FR-9
  need a "limit reached" state in addition to in-progress/failure.]
- [NEEDS CLARIFICATION: Should the learner be able to submit a revised version of an essay
  they've already submitted and have it evaluated again, with some way to see whether their
  fix worked (the informal source workflow that grounded this spec mentions re-evaluating a
  revision, but the PRD Epic-7 scope as written doesn't explicitly require it)? If yes, this
  spec needs an additional requirement for linking a revision to its original submission and
  presenting a before/after comparison; if no, a learner wanting to retry simply creates an
  unrelated new submission under FR-1.]

## Acceptance Criteria
- [ ] A submission without both a response and its task/question cannot be evaluated (FR-1).
- [ ] A submission requires the learner to specify Task 1 or Task 2 before evaluation (FR-2).
- [ ] An empty or blank response cannot be submitted for evaluation (FR-3).
- [ ] An in-progress, unsubmitted response can be abandoned without being saved or evaluated
      (FR-4).
- [ ] A successfully evaluated submission always shows four distinct criterion scores, never
      only one combined score (FR-5).
- [ ] Each criterion's feedback references a specific part of the learner's own submission, not
      a generic statement (FR-6).
- [ ] At least one sentence-level correction is shown, quoting the learner's original sentence
      alongside a corrected version (FR-7).
- [ ] If an overall score is shown, it always appears together with the four per-criterion
      scores and specific feedback, never alone (FR-8).
- [ ] While evaluation is running, an explicit in-progress indication is shown, never a blank or
      ambiguous screen (FR-9).
- [ ] After a simulated evaluation failure, the response text and task/question are still
      present, an explicit failure message is shown, and retry does not require re-entering the
      response (FR-10).
- [ ] A successfully evaluated submission (response, task/question, task type, and full
      feedback) can be retrieved again in a later, separate session (FR-11).
- [ ] The past-submissions list shows date, task type, and enough score detail to tell entries
      apart (FR-12).
- [ ] Selecting a past submission shows its full original feedback — all four criteria,
      strengths/weaknesses, and sentence-level corrections — unchanged from when it was
      produced (FR-13).
- [ ] With no submissions ever made, the list shows a message directing the learner to submit
      one, not a blank list (FR-14).
- [ ] "Nothing submitted yet" wording is visibly distinct from "failed to load" wording, in both
      the list and an individual submission's feedback (FR-15).
- [ ] A learner cannot view or evaluate another learner's submissions or feedback (FR-16).
