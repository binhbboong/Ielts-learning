# Tasks: Personal Access Protection
Plan: docs/specs/access-protection/ImplementationPlan.md

## Task-1 — Shared DB scaffold: engine, session, Base, get_db
- [x] Status: Done
- Depends on: none
- Goal: Build `backend/app/core/db.py`: the SQLAlchemy engine (reading the DB connection string from `backend/app/core/config.py`'s existing/settings object — create a minimal `DATABASE_URL` setting in `config.py` if none yet exists), a `SessionLocal` session factory, the declarative `Base` every model in the project inherits from, and the `get_db` FastAPI dependency that yields one session per request and closes it afterward. This file has no auth logic of its own — it is the shared scaffold every other epic's routers/services and this epic's own `LoginAttempt` model sit on top of, so it is built first and scoped to nothing but connection/session plumbing.
- Files touched: `backend/app/core/db.py`, `backend/app/core/config.py` (only if `DATABASE_URL` doesn't already exist)
- Definition of done: a test using a real test-database connection round-trips a trivial write/read — e.g. a throwaway table (or a minimal test-only model built on `Base`) is created, a row is written through a session obtained from `get_db`, and reading it back through a fresh session returns identical data. No FR is claimed by this task; it is the verifiable milestone every later task (and every other epic) depends on before anything auth-specific or data-bearing can be tested against a real database.

## Task-2 — Config additions: SESSION_SECRET, LEARNER_PASSWORD_HASH, SESSION_COOKIE_MAX_AGE_DAYS
- [x] Status: Done
- Depends on: none
- Goal: Add `SESSION_SECRET`, `LEARNER_PASSWORD_HASH`, and `SESSION_COOKIE_MAX_AGE_DAYS` (default 30) settings to `backend/app/core/config.py`, read from environment variables, alongside whatever settings other epics already have there.
- Files touched: `backend/app/core/config.py`
- Definition of done: a config unit test asserts each of the three settings is present on the settings object, is populated from environment variables when set (test sets env vars, reloads/constructs settings, asserts values match), and `SESSION_COOKIE_MAX_AGE_DAYS` defaults to `30` when unset. No FR of its own — this is infrastructure every auth-specific task below depends on.

## Task-3 — LoginAttempt model + migration
- [x] Status: Done
- Depends on: Task-1
- Goal: Define the SQLAlchemy `LoginAttempt` model (`id`, `ip_address`, `occurred_at`, `succeeded`) in `backend/app/models/access_protection.py` on top of `Base`, and author the Alembic migration creating the `login_attempt` table.
- Files touched: `backend/app/models/access_protection.py`, `backend/alembic/versions/<ts>_create_login_attempt_table.py`
- Definition of done: against a real test database, running the migration creates the `login_attempt` table with the expected columns; a test writes a `LoginAttempt` row through a `get_db` session and reads it back with identical `ip_address`/`occurred_at`/`succeeded` values. No FR of its own — this is the persisted table Task-5/Task-6/Task-14 (FR-8/FR-9) are built on.

## Task-4 — Password verification
- [x] Status: Done
- Depends on: Task-2
- Goal: Implement `verify_password(plain_password: str) -> bool` in `backend/app/services/access_protection.py`, comparing the submitted password against the bcrypt hash in `LEARNER_PASSWORD_HASH`.
- Files touched: `backend/app/services/access_protection.py`, `backend/app/services/access_protection_test.py`
- Definition of done: unit tests pass, asserting `verify_password` returns `True` for the correct password against a known bcrypt hash and `False` for any incorrect password — covers the password-check component of FR-6.

## Task-5 — Lockout tracking: is_locked_out / record_attempt
- [x] Status: Done
- Depends on: Task-3
- Goal: Implement `record_attempt(ip: str, succeeded: bool)` (writes a `LoginAttempt` row) and `is_locked_out(ip: str) -> bool` (counts failed attempts from that IP in the trailing 15-minute rolling window; `True` at 5 or more) in `backend/app/services/access_protection.py`.
- Files touched: `backend/app/services/access_protection.py`, `backend/app/services/access_protection_test.py`
- Definition of done: integration tests against a real test database pass, asserting (a) 5 recorded failed attempts from the same IP within 15 minutes makes `is_locked_out` return `True`, (b) attempts older than the 15-minute window are excluded from the count so the lockout rolls off, and (c) attempts from a different IP don't count toward the first IP's lockout — covers FR-8.

## Task-6 — authenticate(): generic, non-distinguishing outcome
- [x] Status: Done
- Depends on: Task-4, Task-5
- Goal: Implement `authenticate(password: str, ip: str) -> AuthResult` orchestrating `is_locked_out`, `verify_password`, and `record_attempt`: if locked out, return a lockout outcome *without ever calling* `verify_password`; otherwise verify the password, record the attempt (success or failure), and return a success/failure outcome that carries no information distinguishing *why* it failed.
- Files touched: `backend/app/services/access_protection.py`, `backend/app/services/access_protection_test.py`
- Definition of done: unit tests pass, asserting (1) when locked out, a *correct* password still fails and `verify_password` is never invoked (mocked/spied) — covers FR-8; (2) a wrong password returns a failure outcome, is recorded via `record_attempt`, and grants no access — covers FR-6; (3) the failure outcome's shape/fields are identical regardless of failure cause (wrong password vs. locked out is only distinguished by the caller's own lockout check, never by inspecting `authenticate`'s failure payload for a "why") — covers FR-7.

## Task-7 — Session token issuance and verification
- [x] Status: Done
- Depends on: Task-2
- Goal: Implement `create_session_token()` and `verify_session_token(token)` in `backend/app/core/security.py` using `itsdangerous`'s `URLSafeTimedSerializer` keyed by `SESSION_SECRET`, encoding issued-at and a 30-day (`SESSION_COOKIE_MAX_AGE_DAYS`) expiry; define the `SESSION_COOKIE_NAME` constant.
- Files touched: `backend/app/core/security.py`, `backend/app/core/security_test.py`
- Definition of done: unit tests pass, asserting a freshly created token verifies successfully before expiry, a tampered/malformed token fails verification distinguishably as "invalid," and a token past its expiry fails verification distinguishably as "expired" (simulate via a short max-age or an injected/monkeypatched clock). No FR is claimed directly by this task — it is the signing/verification primitive `require_learner` (Task-8) is built on, which is where FR-1/FR-2/FR-11 are actually exercised end-to-end.

## Task-8 — require_learner dependency: reject missing/invalid/expired
- [x] Status: Done
- Depends on: Task-7
- Goal: Implement the `require_learner` FastAPI dependency in `backend/app/core/security.py`: reads the session cookie, and raises `401` with a machine-readable `reason` of `"missing"`, `"invalid"`, or `"expired"` when the cookie is absent, malformed, or past expiry; on a valid token, allows the request through.
- Files touched: `backend/app/core/security.py`, `backend/app/core/security_test.py`
- Definition of done: integration tests pass using a `TestClient` against a dummy protected test route wired to `require_learner`: no cookie → `401` with `reason: "missing"`; a malformed cookie value → `401` with `reason: "invalid"`; an expired token → `401` with `reason: "expired"`; a valid token → request proceeds (`200`) — covers FR-1, FR-2, FR-11.

## Task-9 — require_learner sliding-expiry reissue
- [x] Status: Done
- Depends on: Task-8
- Goal: Extend `require_learner` so that on a successful request where the token has less than 7 days of remaining validity, the response is given a fresh `Set-Cookie` with a renewed 30-day expiry.
- Files touched: `backend/app/core/security.py`, `backend/app/core/security_test.py`
- Definition of done: integration test passes, asserting a request with a near-expiry token (< 7 days remaining) produces a `Set-Cookie` response header carrying a new token with a renewed ~30-day expiry, while a request with a fresh (not-near-expiry) token produces no reissued `Set-Cookie` — covers the reissue mechanism behind FR-4.

## Task-10 — Shared FR-2 test helper for other epics' routers
- [x] Status: Done
- Depends on: Task-8
- Goal: Provide a reusable pytest helper/fixture (e.g. `assert_all_routes_require_learner(app, exclude_prefixes=["/api/auth"])`) that iterates every registered route on a given FastAPI app not under an excluded prefix and asserts each rejects a cookie-less request with `401`, for other epics' own test suites to import against their routers.
- Files touched: `backend/app/core/security.py` (or a `backend/tests/helpers.py` shared test-support module), corresponding test file
- Definition of done: a self-test registers one dummy `require_learner`-protected route and one deliberately unprotected route on a throwaway test app; running the helper against the deliberately-unprotected route fails (proving the helper actually detects a gap) and against the protected-only app it passes — covers FR-2, and hands every other epic a ready-made way to prove FR-2 against its own routes.

## Task-11 — POST /api/auth/login endpoint
- [x] Status: Done
- Depends on: Task-6, Task-7
- Goal: Implement `POST /api/auth/login` in `backend/app/routers/access_protection.py`: reads `LoginRequest{password}`, calls `authenticate(password, request_ip)`; on success, sets the signed session cookie (`create_session_token`) and returns `200`; on lockout, returns `429` without ever checking the password; on wrong password, returns a generic `401` with no distinguishing detail.
- Files touched: `backend/app/routers/access_protection.py`, `backend/app/schemas/access_protection.py`, corresponding test file
- Definition of done: integration tests pass, asserting: correct password → `200` + `Set-Cookie` present; wrong password → `401`, no `Set-Cookie` header, generic body (covers FR-6, FR-7); 5 failed attempts from one IP then a 6th attempt *with the correct password* → still `429`, proving the password was never evaluated (covers FR-8); no `/api/auth/register` (or equivalent) route exists anywhere in the app's OpenAPI schema, and login only ever compares against the single `LEARNER_PASSWORD_HASH`, never a username-keyed lookup (covers FR-3).

## Task-12 — POST /api/auth/logout endpoint
- [x] Status: Done
- Depends on: Task-7
- Goal: Implement `POST /api/auth/logout` in `backend/app/routers/access_protection.py`: unconditionally clears the session cookie (`Set-Cookie` with `Max-Age=0`), regardless of whether a valid session existed.
- Files touched: `backend/app/routers/access_protection.py`, corresponding test file
- Definition of done: integration tests pass, asserting a request with a valid session cookie gets back a `Set-Cookie` header expiring the cookie (`Max-Age=0`), and a request with no cookie at all also succeeds idempotently with the same clearing header — covers FR-5.

## Task-13 — GET /api/auth/status endpoint
- [x] Status: Done
- Depends on: Task-7
- Goal: Implement `GET /api/auth/status` in `backend/app/routers/access_protection.py`: always returns `200` with `AuthStatusResponse{authenticated: bool}`, using non-raising token verification (no cookie or an invalid/expired cookie yields `authenticated: false`, never an error).
- Files touched: `backend/app/routers/access_protection.py`, `backend/app/schemas/access_protection.py`, corresponding test file
- Definition of done: integration tests pass, asserting: no cookie → `200 {authenticated: false}`; valid cookie → `200 {authenticated: true}`; malformed/expired cookie → `200 {authenticated: false}` (never a non-200 or exception) — covers FR-10.

## Task-14 — FR-9 data-safety verification: lockout never touches learner data
- [x] Status: Done
- Depends on: Task-11
- Goal: Add an integration test proving that triggering the lockout protection (Task-11) never destroys, corrupts, or blocks access to any existing data, and that the lockout itself is temporary, not permanent.
- Files touched: test file only (e.g. `backend/app/routers/access_protection_test.py`), using a seeded test-only fixture table built on `Base` to stand in for another epic's data table (no other epic's tables exist yet at this point in parallel development)
- Definition of done: integration test passes, asserting (a) after driving an IP into lockout via 5 failed logins, rows in an unrelated seeded fixture table are byte-for-byte unchanged, and the lockout itself does not delete or alter the `login_attempt` rows that caused it; (b) once the rolling 15-minute window has elapsed (simulated via backdated `occurred_at` timestamps), a subsequent correct-password login from that IP succeeds — covers FR-9.

## Task-15 — Full backend auth-flow integration: multiple authenticated requests without re-proof
- [x] Status: Done
- Depends on: Task-9, Task-11, Task-12
- Goal: Add an end-to-end backend integration test that logs in once via `POST /api/auth/login`, then reuses the resulting cookie across several separate requests to a `require_learner`-protected dummy route, confirming none require re-authentication.
- Files touched: test file only (e.g. `backend/app/routers/access_protection_test.py`)
- Definition of done: integration test passes, asserting that after one successful login, at least 3 subsequent requests reusing the same session cookie against a protected route all succeed (`200`) without any additional login call — covers FR-4.

## Task-16 — Frontend: auth types + repository
- [x] Status: Done
- Depends on: Task-11, Task-12, Task-13
- Goal: Define the `AuthStatusResponse`/reason TypeScript types in `src/app/core/auth/models/auth-status.model.ts`, and implement `src/app/core/auth/data/auth.repository.ts` as the sole point of contact with `api-client.ts` for `login(password)`, `logout()`, and `status()` calls against `/api/auth/*`. Types are folded into this task rather than given their own, per the sizing rule — a types-only file has no behavior to test on its own.
- Files touched: `src/app/core/auth/models/auth-status.model.ts`, `src/app/core/auth/data/auth.repository.ts`, `src/app/core/auth/data/auth.repository.spec.ts`
- Implementation note: Added typed login/logout/status HTTP calls and five `HttpTestingController` tests covering successful requests plus `401`/`429` login rejection propagation.
- Definition of done: repository unit tests pass (using `HttpTestingController` against a mocked backend, per the project's existing frontend test conventions), asserting `login()` POSTs `{password}` to `/api/auth/login` and resolves on `200`/rejects on `401`/`429`, `logout()` POSTs to `/api/auth/logout`, and `status()` GETs `/api/auth/status` and returns a correctly-typed `AuthStatusResponse`. This is plumbing with no FR fully satisfied alone; it is the dependency Task-17 through Task-20 (FR-1, FR-5, FR-10, FR-11, FR-12) are built on.

## Task-17 — Frontend: auth.state.ts
- [x] Status: Done
- Depends on: Task-16
- Goal: Implement `src/app/core/auth/state/auth.state.ts` holding the app-wide authenticated/not-authenticated signal, initialized from `auth.repository.ts`'s `status()` call on bootstrap, and updated synchronously whenever login, logout, or the interceptor detects a `401`.
- Files touched: `src/app/core/auth/state/auth.state.ts`, `src/app/core/auth/state/auth.state.spec.ts`
- Implementation note: Added app-wide readonly authentication/initialization signals, bootstrap status loading, synchronous state updates, and two signal-focused unit tests.
- Definition of done: unit tests pass, asserting the state reflects a mocked `status()` response on initialization, and that an explicit `setAuthenticated(true/false)` call updates the exposed signal synchronously and is observed immediately by a subscriber — covers FR-10.

## Task-18 — Frontend: auth.interceptor.ts
- [x] Status: Done
- Depends on: Task-17
- Goal: Implement `src/app/core/auth/auth.interceptor.ts`: attaches `withCredentials: true` to every outgoing API request, and on a `401` response reads the `reason` field, updates `auth.state.ts` to unauthenticated, and triggers a redirect to the login route (carrying the `reason` so the login page can distinguish an expired-session redirect from a first-visit one).
- Files touched: `src/app/core/auth/auth.interceptor.ts`, `src/app/core/auth/auth.interceptor.spec.ts`
- Implementation note: Added a functional interceptor that sends credentials on every request, handles FastAPI's `detail.reason` error shape, synchronizes auth state, and preserves the expired-session redirect reason; four interceptor tests cover the required paths.
- Definition of done: interceptor unit tests pass, asserting every request is issued with `withCredentials: true`; a simulated `401` with `reason: "expired"` updates `auth.state.ts` to unauthenticated and navigates to the login route flagged as an expiry redirect; a `401` with `reason: "missing"`/`"invalid"` also redirects to login, without the expiry flag — covers FR-11 (expiry-specific messaging trigger) and FR-12 (in-page call case: redirect rather than a broken/silent failure).

## Task-19 — Frontend: auth.guard.ts
- [x] Status: Done
- Depends on: Task-17
- Goal: Implement `src/app/core/auth/auth.guard.ts`: a route guard that blocks navigation to any protected route unless `auth.state.ts` currently reports authenticated, redirecting to the login route otherwise.
- Files touched: `src/app/core/auth/auth.guard.ts`, `src/app/core/auth/auth.guard.spec.ts`
- Implementation note: Added a functional route guard that waits for bootstrap authentication status, permits authenticated navigation, and returns a login `UrlTree` otherwise; two guard tests cover allow and redirect behavior.
- Definition of done: guard unit tests pass, asserting navigation is allowed when `auth.state.ts` reports authenticated, and blocked-with-redirect-to-login when it reports unauthenticated — covers FR-1 and FR-12 (navigation case).

## Task-20 — Frontend: login page
- [x] Status: Done
- Depends on: Task-16, Task-18
- Goal: Implement `src/app/core/auth/pages/login/login.component.ts`: renders a password entry form, submits via `auth.repository.ts`'s `login()`, shows the backend's generic rejection message on failure (rendering nothing more specific than what the backend returned), and shows a distinct "your session expired, please log in again" explanation when arrived at via an interceptor-triggered expiry redirect (vs. a plain, unexplained first-visit login). No wireframe exists for this screen yet (new epic, none authored) — flagged explicitly per the plan rather than inventing one.
- Files touched: `src/app/core/auth/pages/login/login.component.ts`, `.../login.component.html`, `.../login.component.spec.ts`
- Implementation note: Implemented the existing login wireframe as an accessible standalone Angular form with responsive light/dark styling, loading/error handling, expired-session context, and three component tests. Added the supporting access-protection journey and prototype without replacing the existing wireframe.
- Definition of done: component tests pass, asserting: submitting the correct password calls `auth.repository.login()` and updates `auth.state.ts` to authenticated on success; submitting a wrong password renders the generic failure message and nothing that distinguishes it from any other failure mode (covers FR-6, FR-7); arriving via a simulated expiry redirect renders the expiry-specific explanation rather than a generic/unexplained error (covers FR-11).

## Task-21 — Frontend: auth.routes.ts and mount into app root
- [x] Status: Done
- Depends on: Task-20, Task-19
- Goal: Declare `src/app/core/auth/auth.routes.ts` (the login route, and a logout confirmation route if needed) and mount it into the app root's routes, with `auth.guard.ts` applied to protected routes.
- Files touched: `src/app/core/auth/auth.routes.ts`, `src/app/app.routes.ts`
- Implementation note: Added the public login route, guarded every Study Plan route, registered the credentialed auth interceptor in application configuration, and added routing/config integration tests. Updated the existing Study Plan routing harness to model its authenticated precondition.
- Definition of done: routing test passes, asserting the login route resolves to `LoginComponent`, and attempting to navigate directly to a `auth.guard.ts`-protected route while unauthenticated redirects to the login route rather than rendering the target component — covers FR-1, FR-12.

## Task-22 — Production-safe session cookie attributes
- [x] Status: Done
- Depends on: Task-11, Task-12
- Goal: Align issued and cleared session cookies with the approved public-Internet plan by applying HttpOnly, Secure, SameSite=Lax, and a root path consistently.
- Files touched: `backend/app/routers/access_protection.py`, `backend/app/routers/access_protection_test.py`
- Implementation note: Login and logout now use a consistent root-scoped `HttpOnly; Secure; SameSite=Lax` cookie contract; the HTTPS test harness proves secure-cookie continuity and the full 40-test backend suite passes.
- Definition of done: integration tests prove the login cookie carries `HttpOnly`, `Secure`, `SameSite=Lax`, and `Path=/`, while logout clears the same cookie scope; covers the production transport portion of FR-1/FR-2.

## Task-23 — Shared frontend ApiClient
- [x] Status: Done
- Depends on: Task-18
- Goal: Add the shared typed HTTP wrapper every frontend epic's repository plan references, without duplicating authentication or state behavior already owned by the interceptor.
- Files touched: `src/app/core/api/api-client.ts`, `src/app/core/api/api-client.spec.ts`
- Implementation note: Added a typed injectable GET/POST/PATCH/DELETE wrapper with three `HttpTestingController` tests; the full 58-test frontend suite passes.
- Definition of done: `HttpTestingController` tests prove typed GET/POST/PATCH/DELETE calls use the requested URL/body and flow through the registered credential interceptor.

## Task-24 — App Shell authentication indicator and logout
- [x] Status: Done
- Depends on: Task-17, Task-12, Task-21
- Goal: Show protected navigation only while authenticated, display an unambiguous recognized-as-learner indicator, and provide a persistent Logout action that calls the repository, clears auth state, and returns to Login.
- Files touched: `src/app/app.ts`, `src/app/app.html`, `src/app/app.css`, `src/app/app.spec.ts`
- Implementation note: Protected navigation is hidden before identity proof; authenticated sessions show a persistent learner indicator and logout action. Three App Shell tests cover hidden, recognized, and logout states; the full 59-test frontend suite and production build pass.
- Definition of done: component tests prove unauthenticated users see neither protected nav nor logout controls; authenticated users see the indicator/nav; clicking Logout calls the endpoint, synchronously marks state false, and navigates to `/login`; covers FR-5 and FR-10 and aligns the shell with the Login wireframe.

## Notes
- Two integration points this epic depends on live in files owned by other plans, not this backlog: `src/app/core/api/api-client.ts` must send cookies (`withCredentials: true`) on every request (Task-18's interceptor is the epic-owned enforcement point, but the base client must not strip it), and the App Shell's nav must host a persistent "recognized as learner" indicator plus a Log Out control wired to `auth.state.ts`/`auth.repository.ts` (FR-10, FR-5). No task above edits those files; whichever epic owns the App Shell/api-client should wire to `auth.state.ts` and `auth.repository.ts` once Task-16/Task-17 land.
- The spec's three `[NEEDS CLARIFICATION]` open questions (session duration, lockout shape, concurrent devices) are already resolved by the ADR (`docs/adr/2026-07-29-signed-cookie-session-auth.md`) and folded into the tasks above (30-day sliding expiry: Task-7/9; 5-attempts/15-minute rolling lockout: Task-5; concurrent devices allowed independently: no server-side session registry exists anywhere in this backlog, by design).
- Task-1 and Task-2 are the two tasks every other epic's backend backlog should depend on before writing any test that touches a real database or an authenticated route — both are dependency-free and intentionally first.
