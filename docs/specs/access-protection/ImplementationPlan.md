# Implementation Plan: Personal Access Protection
Spec: docs/specs/access-protection/Specification.md

## Approach

The architecture (`docs/architecture/Architecture.md`) already commits this project to FastAPI +
Neon PostgreSQL + Vercel serverless deployment and explicitly flags the auth mechanism itself as
"not yet decided." That is this plan's job. Three approaches were considered.

**Approach A — Shared password, verified server-side, issuing a signed, stateless, HttpOnly
session cookie (recommended).** The learner submits the one configured password to a login
endpoint. The backend verifies it against a bcrypt hash held in an environment variable and, on
success, issues an HttpOnly, Secure, SameSite cookie containing a signed token (HMAC via
`itsdangerous`'s `URLSafeTimedSerializer`, keyed by a `SESSION_SECRET` env var) encoding only an
issued-at time and an expiry. Every subsequent request is authenticated by verifying the
signature and expiry — no database lookup, no server-side session store. This fits Vercel's
stateless serverless functions well: any function instance, cold or warm, in any region, can
verify a token without shared state.

**Approach B — Database-backed session table.** A `sessions` table holds one row per issued
session (token id, created_at, expires_at, revoked_at). Every request does a DB read to check
validity. More precisely revocable (a specific session can be killed server-side) but adds a
Postgres round trip to every single authenticated request — for a single learner with no
multi-user revocation need, that cost buys little.

**Approach C — Third-party OAuth restricted to one allowed account.** Delegate identity proof to
an external provider (e.g., GitHub/Google OAuth), allow-listing exactly one account. Removes
password storage/verification from this codebase but adds an external runtime dependency (the
provider's availability, its OAuth flow, redirect URI configuration per environment) for a
single-user personal tool that doesn't need federated identity, account recovery via a third
party, or "sign in with X" branding. Also complicates the "no information leaked on failure"
requirement (FR-7) since the provider's own UI, not this app, handles failed attempts.

**Recommendation: Approach A.** For a single learner on serverless infrastructure, statelessness
is the dominant advantage: no session table to design, migrate, or query on every request; no
extra Postgres round trip in the hot path of every protected endpoint; and a full "kill all
sessions" capability still exists as a manual, out-of-band action (rotate `SESSION_SECRET`,
which invalidates every outstanding cookie at once) — consistent with the spec's Out-of-Scope
decision that identity-proof recovery is a manual, out-of-band action, not a self-service flow.
Approach B is rejected as unnecessary cost (a DB round trip per request) for a revocation
granularity (per-session kill) this single-user spec never asks for. Approach C is rejected as an
external dependency this tool doesn't need to take on.

This is the costly-to-reverse decision every other epic's router will depend on
(`require_learner`), so it is recorded as an ADR — see below.

### Resolving the spec's three open questions

- **Session persistence duration (Open Question 1): 30-day sliding expiry.** The signed cookie
  carries a 30-day expiry. On any successful authenticated request where the token has less than
  7 days of remaining validity, `require_learner` reissues a fresh cookie with a new 30-day
  expiry via `Set-Cookie` on the response. Net effect: a learner who uses the app at least once
  every 30 days is never asked to re-authenticate; a browser left untouched for 30+ days requires
  a fresh login. This satisfies FR-4 ("a reasonable stretch of normal use") without indefinite
  persistence, and gives FR-11 a concrete trigger (token expiry) rather than an open-ended one.
- **Brute-force protection shape (Open Question 2): rolling IP-based lockout, 5 failures / 15
  minutes.** Every login attempt (success or failure) is recorded in a `login_attempt` table
  (IP address, timestamp, outcome). Before checking the submitted password, the login endpoint
  counts failed attempts from the same IP in the last 15 minutes; at 5 or more, it returns
  `429 Too Many Requests` without checking the password at all (so a locked-out caller can never
  learn whether a given password would have worked). The lockout is rolling (based on the age of
  the oldest attempt in the window, not a fixed timer), and applies only to the login endpoint —
  it never touches learner data, satisfying FR-9. This is persisted in Postgres (not in-memory)
  specifically because Vercel serverless functions do not share memory across instances/cold
  starts; an in-memory counter would silently reset and defeat the protection.
- **Concurrent-device policy (Open Question 3): allowed, independently.** Each device that logs
  in gets its own independently-issued, independently-expiring cookie; there is no server-side
  concept of "the current session" to contend over. Logging out on one device (FR-5) clears only
  that device's cookie and has no effect on any other device's session. Reasoning: the spec
  establishes one legitimate *identity*, not one legitimate *device* — a learner using a laptop
  and a phone in the same day is normal single-user behavior, not a security concern, and
  enforcing single-device exclusivity would require the server-side session registry Approach B
  was rejected for.

### Auth flow summary
1. `POST /api/auth/login {password}` → service checks lockout, then verifies password against
   `LEARNER_PASSWORD_HASH` (bcrypt) → on success, sets the signed session cookie and returns
   `200`; on failure, records the attempt and returns a generic `401` (wrong password) or `429`
   (locked out) — never anything that distinguishes *why* beyond that binary, satisfying FR-7 (in
   this single-identity system, "identity doesn't exist" isn't a distinguishable case to begin
   with, since there is exactly one identity and no username).
2. `POST /api/auth/logout` → clears the cookie (`Set-Cookie` with `Max-Age=0`) unconditionally;
   idempotent whether or not a valid session existed.
3. `GET /api/auth/status` → always `200`, returns `{ "authenticated": boolean }` by attempting
   (non-raising) token verification — this is what the frontend uses to render FR-10's
   unambiguous recognized/not-recognized signal at all times, including on initial app load,
   without depending on a protected endpoint throwing.
4. Every other epic's router depends on `require_learner`, which raises `401` with a
   machine-readable `reason` (`"missing" | "invalid" | "expired"`) when the cookie is absent,
   malformed, or past expiry — the frontend interceptor uses `reason` to show FR-11's "your
   session expired" messaging specifically, versus FR-12's generic redirect for "never proved
   identity at all."

## File/Module Structure

No wireframe or prototype exists yet for this epic (`Related UX: none yet` in the spec) — the
Login screen listed below has no wireframe behind it; this is flagged explicitly rather than
inventing one.

| Path | Responsibility | Implements (wireframe/prototype) |
|------|-----------------|-----------------|
| `backend/app/core/db.py` | SQLAlchemy engine, `SessionLocal` factory, declarative `Base`, and the `get_db` FastAPI dependency (yields a session per request, closes it after). Shared by every epic's routers/services. | — |
| `backend/app/core/security.py` | Session-token issuance (`create_session_token`) and verification (`verify_session_token`), the `SESSION_COOKIE_NAME` constant, and the `require_learner` FastAPI dependency every other epic's router imports to gate its endpoints. | — |
| `backend/app/core/config.py` (shared file, this epic adds fields) | Adds `SESSION_SECRET`, `LEARNER_PASSWORD_HASH`, `SESSION_COOKIE_MAX_AGE_DAYS` (30) settings, read from environment variables — alongside the other epics' settings already living in this file. | — |
| `backend/app/models/access_protection.py` | SQLAlchemy model `LoginAttempt` (id, ip_address, occurred_at, succeeded) — the sole persisted table this epic owns. | — |
| `backend/app/schemas/access_protection.py` | Pydantic request/response shapes: `LoginRequest` (password), `AuthStatusResponse` (authenticated: bool) — no response body ever echoes the password or a hash. | — |
| `backend/app/services/access_protection.py` | Business logic: `verify_password()`, `is_locked_out(ip)`, `record_attempt(ip, succeeded)`, and `authenticate(password, ip)` orchestrating the three into the login flow (FR-6, FR-7, FR-8, FR-9). | — |
| `backend/app/routers/access_protection.py` | Exposes `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/status`; sets/clears the session cookie on the response. | — |
| `backend/alembic/versions/<ts>_create_login_attempt_table.py` | Migration creating the `login_attempt` table. | — |
| `src/app/core/auth/models/auth-status.model.ts` | TypeScript type for `{ authenticated: boolean, reason?: 'missing' \| 'invalid' \| 'expired' }` — types only. | — |
| `src/app/core/auth/data/auth.repository.ts` | Sole point of contact with `api-client.ts` for `/api/auth/*` calls (login, logout, status). | — |
| `src/app/core/auth/state/auth.state.ts` | Holds the current authenticated/not-authenticated signal app-wide, updated by login/logout/interceptor/bootstrap status-check; the single source of truth `auth.guard.ts`, the interceptor, and any nav "logged in as learner" indicator read from. | — |
| `src/app/core/auth/auth.interceptor.ts` | HTTP interceptor: attaches credentials to every API call (cookie-based, so `withCredentials`), and on a `401` response, reads the `reason`, updates `auth.state.ts`, and triggers redirect-to-login (FR-11, FR-12). | — |
| `src/app/core/auth/auth.guard.ts` | Route guard: blocks navigation to any protected route unless `auth.state.ts` currently reports authenticated; redirects to the login route otherwise (FR-1, FR-12). | — |
| `src/app/core/auth/pages/login/login.component.ts` | Renders the password entry form, submits via `auth.repository.ts`, shows the generic failure message on rejection, and the "why you're here" explanation when arriving via an expired-session redirect. **No wireframe exists for this screen** — new epic, none authored yet. | none yet |
| `src/app/core/auth/auth.routes.ts` | Declares the login route (and any logout confirmation, if needed) for mounting into the app root. | — |

Not owned by this plan, but this epic requires two small integration points in files other
epics/plans own: `src/app/core/api/api-client.ts` must send cookies (`withCredentials: true`) on
every request, and the App Shell's nav must host a persistent "recognized as learner" indicator
and a Log Out control (FR-10, FR-5) wired to `auth.state.ts` / `auth.repository.ts`.

## Testing Strategy

Constitution principle 2 (tests-first) applies throughout: every row below is written as a
failing test against the FR before the corresponding backend/frontend code exists.

| Requirement | Verified by |
|---|---|
| FR-1 (no screen/feature/data reachable pre-proof) | Backend integration test: any protected endpoint called with no cookie returns `401`. Frontend: `auth.guard.ts` unit test blocking navigation to a protected route when `auth.state.ts` reports unauthenticated. |
| FR-2 (every data-bearing request rejected without proof, uniformly) | Backend: a parametrized test iterating every registered route that isn't `/api/auth/*` asserts each rejects a cookie-less request with `401` (a shared test helper this plan provides for other epics' own test suites to reuse against their routers). |
| FR-3 (exactly one identity; no registration path) | Backend test: no `/api/auth/register` (or equivalent) route exists in the OpenAPI schema; `authenticate()` only ever compares against the single configured `LEARNER_PASSWORD_HASH`, never a lookup keyed by username. |
| FR-4 (recognized across subsequent actions without re-proof) | Backend integration test: log in once, then make N subsequent authenticated requests reusing the same cookie — all succeed. |
| FR-5 (explicit end of proven state, effective immediately) | Backend integration test: `POST /api/auth/logout` clears the cookie; the very next request using the pre-logout cookie value is rejected as `401` once the cookie's `Max-Age=0` has been honored by the client (verified at the HTTP-response level: `Set-Cookie` header expires it). |
| FR-6 (failed attempt grants no access) | Backend unit test: `authenticate()` with a wrong password returns failure and no `Set-Cookie` header is present on the response. |
| FR-7 (no distinguishing info on failure) | Backend unit test: response body/status for "wrong password" is asserted to contain no field or timing signal differentiating it from any other failure mode besides the documented lockout case. |
| FR-8 (protection against repeated automated attempts) | Backend integration test: 5 failed logins from the same IP within the window, 6th attempt returns `429` without evaluating the password (verified by using a *correct* password on the 6th attempt and confirming it still fails). |
| FR-9 (failed attempts never affect learner data) | Backend integration test: after triggering lockout, assert rows in unrelated data tables (e.g., a seeded study-plan/vocabulary fixture) are unchanged; also assert lockout expires (rolling window) and a subsequent correct-password attempt succeeds. |
| FR-10 (unambiguous recognized/not-recognized signal at all times) | Frontend unit test: `auth.state.ts` reflects `GET /api/auth/status` on app bootstrap and updates synchronously on every login/logout/401 event; component test that the nav indicator renders the current state. |
| FR-11 (expired state clearly explained, not an unexplained error) | Backend unit test: `require_learner` returns `reason: "expired"` specifically (not `"missing"`/`"invalid"`) when the token's expiry has passed. Frontend interceptor test: a `401` with `reason: "expired"` renders the "your session expired" explanation before redirecting. |
| FR-12 (protected action while unrecognized redirects, no silent failure) | Frontend: `auth.guard.ts` test (navigation case) and `auth.interceptor.ts` test (in-page API-call case) both redirect to the login route rather than rendering a broken/empty state. |

## Risks / Open Questions

- **Revocation granularity is coarse.** The only way to invalidate *all* outstanding sessions at
  once is rotating `SESSION_SECRET` (a manual, out-of-band env var change) — there is no way to
  kill one specific device's session while leaving others valid, since no per-session state is
  stored server-side. Accepted deliberately per the Approach-A trade-off above; flagged here in
  case future requirements change this.
- **CSRF surface from cookie-based auth.** Because auth is a cookie rather than a bearer token
  the frontend attaches manually, state-changing endpoints (`POST`/`PUT`/`DELETE` across every
  epic) are technically CSRF-exposed unless mitigated. This plan mitigates via `SameSite=Lax` (or
  `Strict`, to be confirmed once the frontend/backend's exact same-site relationship on Vercel is
  known) on the session cookie plus origin-header verification in `require_learner`, rather than
  a separate CSRF-token system — flagged as a decision worth revisiting if frontend and backend
  end up on different subdomains rather than the same Vercel deployment origin.
- **Password hashing cost vs. cold starts.** Bcrypt's cost factor must be tuned to be expensive
  enough to resist offline guessing but cheap enough not to meaningfully add to a cold Vercel
  function's latency on the (rare, single-user) login request; not a correctness risk, just a
  tuning note for implementation time.
- **`login_attempt` table growth.** With no learner-facing history view (explicitly Out of
  Scope) and no automatic pruning designed here, the table grows unboundedly over the life of the
  project. Low real-world risk at single-user login volume, but a future cleanup job or TTL is a
  reasonable follow-up, not designed in this plan.

## Related ADRs
- docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md
- docs/adr/2026-07-29-signed-cookie-session-auth.md
