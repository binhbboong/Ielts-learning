# ADR: Single-Learner Auth via Server-Verified Password + Stateless Signed Session Cookie

Date: 2026-07-29
Slug: signed-cookie-session-auth
Status: Accepted
Related spec: docs/specs/access-protection/Specification.md

## Context

`docs/architecture/Architecture.md` adopted a FastAPI + Neon PostgreSQL + Vercel serverless
full-stack architecture but explicitly left the auth mechanism as "not yet decided," to be
resolved when Epic-6 (Personal Access Protection) was planned. That spec establishes a
single-learner access gate (FR-1 through FR-12) and deliberately leaves three implementation
questions open: how long a proven-identity state should persist, what shape brute-force
protection should take, and whether concurrent multi-device access is allowed. Every other
epic's backend router depends on whatever gating mechanism this decision produces, and it is
expensive to change later once every router has a hard dependency on its shape — this is exactly
the kind of consequential, costly-to-reverse decision the implementation-planning process
requires an ADR for.

Three approaches were considered: (A) a shared password verified server-side, issuing a signed,
stateless, HttpOnly session cookie with expiry, verified by signature alone with no server-side
session store; (B) a database-backed session table, queried on every request, trading a request-
time DB round trip for precise per-session revocability; (C) a third-party OAuth provider
restricted to one allow-listed account, trading an external runtime dependency for not storing a
password in this codebase.

## Decision

Adopt Approach A. The backend verifies the single learner's password (bcrypt hash held in an
environment variable, `LEARNER_PASSWORD_HASH`) against a login submission and, on success, issues
an HttpOnly, Secure, `SameSite` cookie carrying a signed token (HMAC-signed via
`SESSION_SECRET`) with a 30-day expiry. Every subsequent request is authenticated purely by
verifying that signature and expiry — no database read in the hot path. `backend/app/core/db.py`
provides the shared SQLAlchemy engine/session/`get_db` dependency used across all epics.
`backend/app/core/security.py` provides `require_learner`, the FastAPI dependency every other
epic's router imports to gate its endpoints; it raises `401` with a `reason` of `"missing"`,
`"invalid"`, or `"expired"` and, on a request with a token nearing expiry (<7 days remaining),
transparently reissues a fresh 30-day cookie (sliding expiration).

This decision also resolves the spec's three open questions: session persistence is a 30-day
sliding-expiry cookie (FR-4/FR-11); brute-force protection is a rolling lockout of 5 failed
attempts per IP per 15-minute window, persisted in a Postgres `login_attempt` table rather than
in-memory (because Vercel serverless instances don't share memory) (FR-8/FR-9); concurrent
devices are explicitly allowed, each with its own independently-issued and independently-expiring
cookie, since the spec establishes one legitimate *identity*, not one legitimate *device*, and
logging out (FR-5) only ever clears the cookie for the device that requested it.

## Consequences

- **Easier**: no session-store schema or migration to design/maintain beyond a small
  `login_attempt` table; no added DB round trip on every protected request across every epic,
  which matters given Vercel's per-invocation execution limits (already flagged as an open risk
  in Architecture.md); every other epic's plan can depend on a single, simple, already-designed
  `require_learner` dependency instead of waiting on this decision.
- **Harder**: there is no way to revoke one specific device's session without invalidating all
  sessions (rotating `SESSION_SECRET` is the only kill switch, a manual/out-of-band action). This
  is accepted as consistent with the spec's Out-of-Scope decision that identity-proof recovery is
  already a manual, out-of-band action for this single-user tool, not a self-service capability
  it needs to build.
- **Forecloses**: building any per-session admin/history view (already Out of Scope in the spec)
  without a larger rework, since no per-session record is kept beyond login *attempts* (which
  exist for brute-force protection, not for session tracking).
- **Introduces a CSRF consideration** (cookie-based auth vs. a manually-attached bearer token)
  that this ADR resolves via `SameSite` cookie attributes plus origin-header verification in
  `require_learner`, rather than a separate CSRF-token system — noted as worth revisiting if the
  frontend and backend end up deployed to different subdomains rather than sharing an origin.
- **Supersedes** nothing; this is the first ADR to resolve Architecture.md's "Auth mechanism (not
  yet decided)" cross-cutting decision.
