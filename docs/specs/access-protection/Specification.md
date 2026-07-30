# Specification: Personal Access Protection
Related UX: none yet — no wireframe/journey exists for this epic (it's a new epic, not carried over from the client-only architecture)

## Status
Draft

## Overview
Now that the application is reachable over the public Internet rather than running only
inside the learner's own browser, it has no equivalent of the old access boundary — the
browser itself. Anyone who finds the application's address can currently reach every screen
and every piece of the learner's data: the study plan, vocabulary, mistake log, practice
results, and — most sensitively — Writing/Speaking submissions and their AI feedback. This
feature closes that gap with a single-learner access gate: a way for the one legitimate
learner to prove their identity before the application shows or accepts anything, and a
guarantee that no data-bearing request succeeds without that proof.

This is deliberately not a general-purpose authentication system. There is exactly one
legitimate user of this application, known in advance, not a population of accounts to
register, verify, or manage. The feature's job is narrow: stand between the public Internet
and the learner's data, let the real learner through, and keep everyone else out — without
the registration flows, role assignment, or admin tooling a multi-user system would need.

## User Scenarios
- As the learner, I want to prove my identity before I can see or use any of my study data,
  so that a stranger who finds the application's address cannot view my plan, vocabulary,
  mistakes, practice results, or Writing/Speaking submissions.
- As the learner, I want every action that reads or changes my data — not just the first
  screen I land on — to be blocked unless I've already proven my identity, so that there's no
  side door into my data that bypasses the initial gate.
- As the learner, I want to stay recognized as myself for a reasonable stretch of normal use,
  so that I'm not forced to re-prove my identity on every single action within one sitting.
- As the learner, I want a failed identity-proof attempt to be rejected without revealing
  anything about what would have made it succeed, so that a stranger poking at the gate learns
  nothing useful from trying.
- As the learner, I want repeated, automated guessing against the gate to be slowed down or
  blocked, so that my data isn't left exposed to a brute-force attack just because the
  application is public.
- As the learner, I want a clear, unambiguous signal when I'm not currently recognized as
  myself (as opposed to some other error), so that I always understand why I'm being asked to
  prove my identity again.

## Functional Requirements

### Proving identity
- FR-1: The system MUST require the learner to prove their identity before granting access to
  any screen, feature, or data beyond the identity-proof step itself.
- FR-2: The system MUST reject any request that attempts to read or modify learner data
  (study plan, vocabulary, mistakes, practice results, submissions, AI feedback, exports, or
  any other learner data introduced by another epic) unless the request has already proven the
  requester is the learner. This applies uniformly across every existing and future data-bearing
  request, not to an enumerated list of screens.
- FR-3: The system MUST treat exactly one identity as legitimate. It MUST NOT provide any
  mechanism for registering, inviting, or recognizing a second distinct identity.
- FR-4: Once the learner has proven their identity, the system MUST recognize them as the
  learner across subsequent actions in that visit without requiring them to prove their
  identity again for each individual action.
- FR-5: The system MUST provide a way for the learner to explicitly end their proven-identity
  state on demand (e.g., stepping away from a shared or public device) such that, immediately
  afterward, the system treats any subsequent request as not yet having proven identity.

### Handling failed and repeated attempts
- FR-6: When an identity-proof attempt fails, the system MUST reject it and MUST NOT grant any
  level of access as a result of that attempt.
- FR-7: When an identity-proof attempt fails, the system MUST NOT reveal information that would
  help distinguish "the identity being claimed doesn't exist" from "the identity exists but the
  proof offered was wrong" — the rejection MUST look the same either way.
- FR-8: The system MUST apply some form of protection against repeated, automated identity-proof
  attempts (e.g., against a party rapidly trying many guesses in succession), such that
  unlimited automated guessing is never possible.
- FR-9: A failed identity-proof attempt, and any protective action taken as a result of repeated
  failures, MUST NOT destroy, corrupt, or lock the learner out of their existing data — the
  protection applies to the identity-proof step only, never to the data itself.

### Signaling access state
- FR-10: The system MUST make it unambiguous to the learner, at all times, whether they are
  currently recognized as the learner or not.
- FR-11: When a previously proven-identity state stops being valid (e.g., it has expired or was
  ended), the system MUST require the learner to prove their identity again before any further
  data-bearing request is honored, and MUST clearly indicate that this is why they are being
  asked again — not present it as an unexplained error.
- FR-12: If the learner attempts an action that requires proven identity while not currently
  recognized as the learner, the system MUST redirect them to the identity-proof step rather
  than failing silently or showing a broken/empty state.

## Out of Scope
- Multi-user or multi-role capability of any kind (additional accounts, role assignment,
  admin/user distinctions, permission levels) — this feature recognizes exactly one legitimate
  identity, per PRD Epic-6 and PRD product-level Out of Scope ("multi-role or enterprise-grade
  authentication").
- Self-service registration or sign-up flow — there is no population of new users to onboard;
  the one legitimate identity is established outside the running application, not created
  through it.
- Self-service, in-app recovery of a lost identity-proof (e.g., an automated "forgot it" flow
  that emails a reset link or generates a new proof on demand). For a genuinely single-user
  personal tool, the learner is also the operator of the system; recovering from a lost
  identity-proof is reasonably a manual, out-of-band action (performed directly against the
  underlying account/configuration, outside this application's own UI) rather than a
  self-service flow this feature must build and secure. This is a deliberate scope reduction
  given the single-user context, not an oversight.
- Any capability for the learner to view, audit, or manage a history of past access attempts
  from within the application (e.g., a login-history screen).
- Protecting against threats other than unauthorized access to the application itself (e.g.,
  physical device security, network-level attacks, security of the learner's own credential
  storage) — this feature covers the application's access gate only.

## Open Questions
- [NEEDS CLARIFICATION: How long should a proven-identity state persist before the learner is
  required to prove their identity again — for the remainder of a single browsing session only,
  for a fixed longer duration (hours/days), or indefinitely until explicitly ended (FR-5)? The
  PRD and Vision establish that protection is required but don't state a persistence duration or
  re-authentication frequency.]
- [NEEDS CLARIFICATION: What specific protective response should repeated failed identity-proof
  attempts trigger (FR-8) — a temporary delay, a temporary lockout of further attempts, an
  alert to the learner, some combination, or something else — and after how many failures? The
  PRD/Vision require that *some* protection exist but don't specify its shape or thresholds.]
- [NEEDS CLARIFICATION: Should the learner be able to remain recognized simultaneously from more
  than one device/browser at the same time (e.g., proving identity on a laptop and a phone
  concurrently), or does proving identity on a new device end recognition on the previous one?
  Neither the PRD nor Vision addresses concurrent access from multiple devices.]

## Acceptance Criteria
- [ ] No screen, feature, or data beyond the identity-proof step is reachable without first
  proving identity (FR-1).
- [ ] Every data-bearing request (study plan, vocabulary, mistakes, practice results,
  submissions, AI feedback, exports) is rejected when the requester has not proven identity,
  with no exceptions found across any epic's data (FR-2).
- [ ] No path exists in the system to register, invite, or recognize a second distinct identity
  (FR-3).
- [ ] After proving identity once, the learner can perform multiple subsequent actions in the
  same visit without being asked to prove identity again for each one (FR-4).
- [ ] An explicit action exists that ends the proven-identity state on demand, and the very next
  data-bearing request afterward is treated as not-yet-proven (FR-5).
- [ ] A failed identity-proof attempt is rejected and grants no access (FR-6).
- [ ] Rejection messaging for a failed attempt is identical whether the claimed identity is
  wrong or the proof offered is wrong (FR-7).
- [ ] Automated, rapid, repeated identity-proof attempts trigger some protective response rather
  than being processed without limit (FR-8).
- [ ] A failed attempt, and any resulting protective action, leaves the learner's existing data
  fully intact and does not itself lock the learner out of their data permanently (FR-9).
- [ ] The current recognized/not-recognized state is always visibly and unambiguously
  communicated to the learner (FR-10).
- [ ] When a previously proven-identity state stops being valid, the next data-bearing action
  prompts re-proof with a clear explanation, not an unexplained error (FR-11).
- [ ] Attempting a protected action while not recognized redirects to the identity-proof step
  rather than failing silently or rendering a broken/empty state (FR-12).
