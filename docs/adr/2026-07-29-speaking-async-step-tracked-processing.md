# ADR: Speaking Submissions Process as an Asynchronous, Step-Tracked Pipeline (Not One Synchronous Call)

Date: 2026-07-29
Slug: speaking-async-step-tracked-processing
Status: Accepted
Related spec: docs/specs/speaking-coach/Specification.md

## Context

`docs/architecture/Architecture.md`'s Known Constraints section flags Vercel serverless
execution-time limits as an open, unresolved risk, and calls out Speaking evaluation
specifically: it chains two external calls (Speech-to-Text, then
`AIProvider.evaluate_speaking()`) inside what would naturally be a single request handler —
exactly the scenario the note warns could exceed a serverless function's maximum execution
time. Writing evaluation (Epic-7) makes only one external call and does not carry this risk to
the same degree.

Independently of that infrastructure risk, `docs/specs/speaking-coach/Specification.md`
requires (FR-6, FR-10) that a transcription failure and an evaluation failure be presented as
distinct, separately labeled states, each independently retryable without redoing earlier
work, and requires (FR-11, FR-12) a genuine "processing" state the learner can walk away from
and return to later without waiting continuously. A single synchronous
submit-and-get-a-result call satisfies neither requirement without bolting on extra state
tracking after the fact — at which point it has stopped being simpler than designing for steps
from the start.

This choice fixes the database's status semantics, the API's endpoint shape, and the
frontend's orchestration model. Once other code (the Angular facade, and potentially the
Practice & Progress module reading speaking status later) depends on that shape, reversing it
is expensive — this is exactly the kind of costly-to-reverse decision the planning process
requires an ADR for, and it is a distinct decision from Epic-7's `AIProvider` interface ADR
(owned by the writing-coach plan): that ADR is about the shape of one interface method, this
one is about how a request lifecycle spanning two external calls is executed and observed.

## Decision

Speaking submissions are processed as an asynchronous, step-tracked pipeline:

- Creating a submission is a single fast database write with **no external call** — it
  persists the audio reference and the selected question, sets status to `PROCESSING`, and
  returns immediately. This is the "received, processing has begun" confirmation FR-3
  requires, produced before transcription is ever attempted.
- Transcription and evaluation are each triggered by their **own separate backend
  endpoint/request** (`POST /speaking-submissions/{id}/transcribe`,
  `POST /speaking-submissions/{id}/evaluate`), so each external call runs inside its own
  serverless invocation's execution budget instead of two calls sharing one. This removes the
  flagged risk by construction, without needing to know the actual (still-undetermined) time
  limit.
- Status is persisted after every step as one of four learner-facing values —
  `PROCESSING`, `TRANSCRIPTION_FAILED`, `EVALUATION_FAILED`, `COMPLETED` — matching FR-13's
  wording exactly. Whether the next step is "transcribe" or "evaluate" is derived from whether
  the `transcript` column is populated, not tracked as a separate internal state.
- The Angular frontend chains transcribe → evaluate automatically right after submission
  (normal happy path, no learner action needed beyond the initial submit), and resumes that
  chain automatically whenever the learner opens a `PROCESSING` submission's detail view later
  (self-healing resume covering FR-12's "leave and come back"). A genuine step failure instead
  surfaces an explicit, learner-initiated Retry action calling the same step endpoint — failures
  are never silently auto-retried, per FR-6/FR-10.
- No message queue, cron worker, or third-party job runner is introduced for this MVP. If a
  submission's next step is never triggered because the learner never revisits it, it simply
  stays `PROCESSING` — an accepted trade-off (see Consequences), not solved with new
  infrastructure now.

## Consequences

- **Easier**: FR-6/FR-10/FR-11/FR-12 are satisfied close to directly by the status model
  itself, with no separate tracking layer bolted on afterward. The single-request execution-time
  risk is avoided regardless of what Vercel's actual limit turns out to be. No new paid
  infrastructure is introduced, consistent with the PRD's cost-consciousness and hobby-tier
  preference. FR-13/FR-14/FR-15's list/detail requirements read directly off the same
  status/transcript-presence model used to drive the pipeline.
- **Harder**: processing only advances when a client actively views or drives it — there is no
  guaranteed background completion if the learner submits a recording and never opens the app
  again. Acceptable for a single solo learner's own tool (they are the only client that will
  ever open it), but would need revisiting (e.g., a Vercel Cron sweep, or a real queue) if this
  ever needs guaranteed completion independent of a client returning. Slightly more endpoints
  and persisted state to build and test than a single synchronous call. The frontend must
  implement resume-on-view logic rather than a simple await-the-response flow.
- **Forecloses, reversibly**: a true fire-and-forget background-job model is not built now, but
  this schema/API shape does not need to change to add one later — a cron sweep or queue
  consumer could call the exact same `transcribe`/`evaluate` endpoints; only the trigger
  mechanism would be added on top.
