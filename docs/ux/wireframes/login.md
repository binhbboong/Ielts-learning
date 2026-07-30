# Wireframe: Login
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/access-protection/Specification.md

## Purpose
Let the one legitimate learner prove their identity with a single password before any screen, feature, or data in the app becomes reachable (FR-1, FR-3), while giving an unambiguous, correctly-explained reason for being here whether this is a first-ever visit or a return after an expired session (FR-10, FR-11).

## Layout
```
+----------------------------------------------------+
| Header: App name/logo (no nav — nothing else is     |
|         reachable pre-proof, per FR-1)               |
+----------------------------------------------------+
| Main content (centered card):                        |
|                                                        |
|  [Context banner — only when arriving via redirect]  |
|   "Your session expired. Please log in again."       |
|   (session-expired state only — FR-11; absent on a   |
|   first-ever visit)                                   |
|                                                        |
|  Heading: "Log in"                                    |
|                                                        |
|  Label: Password                                      |
|  [ Password input field                          ]   |
|                                                        |
|  [ Inline error message — error states only ]         |
|                                                        |
|  [        Log In (submit button)        ]             |
|                                                        |
|  (No username field — exactly one identity, FR-3)     |
|  (No "forgot password" link — self-service recovery   |
|   is explicitly Out of Scope)                          |
+----------------------------------------------------+
| Footer: (none — minimal chrome; nothing else is       |
|          reachable pre-proof)                          |
+----------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Context banner ("session expired") | Satisfies FR-11: explains *why* the learner is back at login instead of presenting an unexplained error; shown only when the interceptor detects `reason: "expired"` from a `401` | High (when applicable) |
| Heading ("Log in") | Orients the learner that this is the identity-proof step, satisfying FR-10's "unambiguous state" requirement at a glance | High |
| Password input | The single identity-proof mechanism per FR-3 (no username — there is exactly one identity to prove) | High |
| Inline error message | Surfaces failure feedback; copy varies by error state (generic wrong-password vs. lockout) but never reveals which part of the (nonexistent) "identity" was wrong, per FR-7 | High (error states only) |
| Log In button | Submits the password to `POST /api/auth/login`; disabled/showing a busy state while the request is in flight | High |
| Absence of username field | Deliberate omission — reinforces FR-3 (single known identity, nothing to select or type an identity for) | N/A (structural decision) |
| Absence of "forgot password" link | Deliberate omission — self-service recovery is Out of Scope per the spec; recovery is a manual, out-of-band action outside this UI | N/A (structural decision) |
| Absence of top/side navigation | Nothing beyond the identity-proof step is reachable pre-proof (FR-1) | N/A (structural decision) |

## States
- **Empty (first-ever visit, ready to submit):** No context banner. Heading + empty password field + Log In button. This is the base/default state for a learner arriving at the app with no prior session and no redirect reason.
- **Loading (submitting):** Password field and button disabled; button shows a busy indicator (e.g., "Logging in…"). No error message visible. Triggered on submit, resolved by the `POST /api/auth/login` response.
- **Error — wrong password (generic, FR-6/FR-7):** Inline message reads generically, e.g. "Incorrect password." Does not distinguish "wrong password" from any other failure reason, and does not hint at password requirements or partial correctness. Password field is cleared or retains focus for retry; no lockout implied.
- **Error — locked out (FR-8, distinct from wrong password):** Inline message conveys rate-limiting rather than incorrectness, e.g. "Too many attempts. Please wait a few minutes before trying again." Submit is disabled (or attempts are rejected server-side with `429` even if the button is left enabled) so the learner cannot infer anything about password correctness from a locked-out attempt. Visually and textually distinct from the generic wrong-password message so the learner understands *this* is a pacing issue, not a typo.
- **Session-expired arrival (FR-11, distinct from first-ever visit):** Same base form as Empty, plus the context banner explaining that a previous session expired and re-proof is required — reached when `auth.interceptor.ts` catches a `401` with `reason: "expired"` and redirects here, versus a plain redirect for "never proved identity" (FR-12).
- **Populated:** Not applicable to a login form in the traditional sense — "ready to submit" is treated as part of the Empty state above (a password value present but not yet submitted is still the Empty/base state, just with input in the field).
