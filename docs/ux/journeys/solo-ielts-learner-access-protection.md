# User Journey: Access Protection
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
The learner opens the publicly reachable IELTS application to continue a study session. They
must prove they are the sole legitimate learner before any study data is shown, either on a
first visit or after a previous session has expired.

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Opens the application or follows a protected link | Application entry route | Return to the current study context without exposing personal study data | Medium: an unexplained redirect could look like broken navigation |
| 2 | Reads why identity proof is required | Login screen | Understand whether this is a normal first visit or an expired session | Low when the reason is explicit; high if expiry is shown as a generic failure |
| 3 | Enters the single learner password | Login screen | Prove identity with minimal friction and no account-selection flow | Medium: repeated failure without useful pacing feedback can cause frustration |
| 4 | Submits the password | Login screen | Receive a clear success, generic rejection, or temporary lockout response | High: this is the peak-friction point and must not leak security-sensitive detail |
| 5 | Continues to the requested protected destination | Daily Checklist or originally requested route | Resume studying without another proof prompt on each action | Low once recognition persists correctly |
| 6 | Repeats proof only after expiry or explicit logout | Login screen | Understand why access ended and recover in one short step | Medium: losing context after expiry can interrupt a time-limited study session |

## Emotional Arc
Friction peaks at submission because the learner wants to study, not manage an account. Relief
comes when one successful proof returns them directly to protected study content and remains
valid across subsequent actions.

## Success Criteria
- The learner reaches protected study content within three deliberate actions after the login
  screen appears: enter password, submit, continue.
- No learner data or protected navigation is visible before successful identity proof.
- An expired session is explained before the learner submits again.
- Failed or rate-limited attempts provide actionable retry feedback without revealing credential
  details.

## Candidate Screens
- Login
- Today's Plan / Daily Checklist
