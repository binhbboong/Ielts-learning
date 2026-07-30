# ADR: Text-to-Speech integration mirrors Speech-to-Text; audio stored as bytea in Postgres

Date: 2026-07-30
Slug: text-to-speech-integration-and-audio-storage
Status: Accepted
Related spec: docs/specs/listening-practice/Specification.md

## Context

Listening Practice (Epic-10) needs to convert a generated script into playable audio (FR-2).
`docs/architecture/Architecture.md` flagged this as a new integration with no chosen vendor.
Two decisions are actually needed here, not one: (1) the shape of the integration boundary
itself, and (2) where the resulting audio bytes live once generated, since — unlike every
other epic's data, which is plain text/JSON — an audio clip is a binary asset, and this
project has no object-storage service (S3, Vercel Blob, etc.) today.

The codebase already has a directly analogous integration for the opposite direction:
`backend/app/services/speech_to_text.py` defines a `SpeechToText` `Protocol` with a single
`transcribe()` method and a `LocalDemoSpeechToText` adapter used for local dev, with the real
vendor deferred and swappable behind that boundary. Text-to-Speech is the mirror-image
capability (text in, audio out, instead of audio in, text out).

## Decision

**Integration shape**: mirror `SpeechToText` exactly.

```
# backend/app/services/text_to_speech.py

class SynthesisResult:
    status: Literal["ok", "error"]
    audio_bytes: bytes | None
    content_type: str | None      # e.g. "audio/mpeg" — needed to serve it back correctly
    error_message: str | None

class TextToSpeech(Protocol):
    def synthesize(self, script_text: str) -> SynthesisResult: ...

class LocalDemoTextToSpeech:
    """Runnable local adapter; replace behind this boundary when a vendor is selected."""
    def synthesize(self, script_text: str) -> SynthesisResult:
        # returns a short, fixed, valid audio clip (e.g. a pre-recorded "local demo" WAV
        # bundled in the repo) so the full pipeline is exercisable end-to-end locally
        # without a real TTS vendor or network call, exactly as LocalDemoSpeechToText does.
```

Selected the same way `SpeechToText`/`AIProvider` are selected: an environment-variable-driven
choice in `backend/app/core/config.py` (e.g. `TTS_PROVIDER`), read once at startup — not
decided further here; the vendor itself remains an open choice for whenever real deployment
needs it, same status as Speech-to-Text's own vendor today.

**Audio storage**: the generated audio is stored as a `bytea` column directly in Postgres,
alongside the `Listening Practice` exercise row — not in a separate object-storage service.

Reasoning:
1. **Scale**: single learner, one clip per calendar day, a few minutes of speech each — this is
   a small, bounded, slow-growing amount of binary data, not a workload object storage exists
   to solve.
2. **No new infrastructure**: every other piece of this system's state already lives in the one
   Postgres database the backend owns exclusively (per
   `docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`). Introducing an object-storage
   service for this one column would add a second storage system, a second set of credentials,
   and a second failure mode, for a problem Postgres already handles adequately at this scale.
3. **Export simplicity**: `docs/specs/listening-practice/Specification.md` FR-15 requires the
   actual audio file in the learner's data export. With the audio already inside the same
   database every other exported table is read from, Data Export (Epic-5) reads it the same
   way it reads everything else — no second read path, no signed-URL expiry concerns, no
   separate credential to export data from.
4. **Explicitly not chosen for future scale reasons**: if audio volume ever grew far beyond a
   single learner's daily clip (e.g. multiple clips per day, much longer audio), row-size and
   backup-size growth in Postgres would become a real cost — noted here as the condition under
   which this decision should be revisited, not assumed to never apply.

## Consequences

- **Easier**: no new service, no new credential, no new deployment dependency; Data Export's
  existing per-table read pattern extends to this column without special-casing; local dev
  requires zero additional setup beyond the existing Postgres container.
- **Harder**: the `listening_exercise` (or equivalent) table carries a binary column that can be
  meaningfully larger than every other row in the schema — migrations and backups touching this
  table cost more than a typical row; the API response serving the audio to the frontend must
  stream/serve bytes from a database read rather than redirecting to a CDN-backed URL.
- **Forecloses**: nothing permanently — a future migration to object storage (if audio volume
  ever justifies it) only changes where the bytes live, not the `TextToSpeech`/`SynthesisResult`
  interface boundary or the export contract's guarantee that the actual audio is included.
