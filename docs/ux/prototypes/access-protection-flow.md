# Prototype: Access Protection Flow
Journey: docs/ux/journeys/solo-ielts-learner-access-protection.md

## Screen Sequence
1. `docs/ux/wireframes/login.md` - triggered by opening the application without a valid
   recognized session, navigating to a protected route while unrecognized, or receiving an
   expired-session response from a protected request.
2. `docs/ux/wireframes/daily-checklist.md` - triggered by a successful password submission when
   the learner entered through the default application route.

When login was triggered from another protected destination, successful proof returns to that
destination instead of forcing the Daily Checklist.

## Transitions
| From | Trigger | To |
|---|---|---|
| Protected route | Route guard finds no valid recognized session | Login, without an expiry explanation |
| Protected request | Interceptor receives `401` with reason `expired` | Login, with the session-expired explanation |
| Login | Valid password returns `200` and establishes recognition | Originally requested protected route, or Today's Plan by default |
| Login | Invalid password returns `401` | Login error state with generic rejection copy |
| Login | Repeated attempts return `429` | Login lockout state with temporary pacing guidance |
| Protected application | Learner explicitly logs out | Login, with no expired-session explanation |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow.
- [x] Every transition has a clear, unambiguous trigger.
- [x] No screen exists in this flow without a stated purpose from the journey.
- [x] Open UX questions are listed below, not silently resolved.

## Open Questions
- None for the Task-20 login scope. Returning to the originally requested URL can be added as a
  later navigation enhancement; the current specification only requires redirecting to login.
