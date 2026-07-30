# PRD: Personal IELTS Learning Dashboard
Vision: docs/business/Vision.md

## Status
Draft (revision 3 — reflects the Vision revision that shifts the product from a self-directed progress tracker to an AI-generated daily lesson engine across all four skills; see docs/business/Vision.md)

## Summary
This product gives a solo, self-directed IELTS learner a "personal teacher" that generates a fresh, personalized set of practice for all four skills (Reading, Listening, Writing, Speaking) every day — targeted at the learner's own recurring mistakes and due vocabulary — instead of a static question bank or a bare progress tracker the learner has to feed themselves. It reviews vocabulary on schedule, catches and correlates recurring mistakes across skills, and shows the learner their own skill progress over time, including AI-graded feedback on Writing and Speaking scored against the official IELTS criteria. Because the application is reachable over the public Internet rather than running only inside the learner's own browser, protecting the learner's personal data from anyone else is a first-class concern, not an afterthought. The learner must always be able to export their data — including generated lessons and results — so depending on a hosting/database/AI provider never becomes a lock-in.

## Epics

### Epic-1: Daily Personalized Lesson Plan
- Priority: Must
- Scope: Each day, decides what today's practice should focus on for all four skills — pulling from the learner's recent mistake patterns (Epic-3) and vocabulary due for review (Epic-2) to target real weaknesses instead of a generic curriculum — and presents one always-current daily overview showing what's ready across Reading, Listening, Writing, and Speaking. This is the orchestration/personalization layer; the actual exercise content per skill is produced by that skill's own epic (Epic-9 for Reading, Epic-10 for Listening) or supplies the day's prompt to the existing Writing/Speaking coaching epics (Epic-7, Epic-8). Continuous — a new day's set is generated whenever the learner is ready for it, with no fixed calendar length. Traces to Vision goals G-1, G-2.
- Future spec slug: daily-lesson-plan
- Note: supersedes the prior "study-plan-execution" epic, whose scope assumed a fixed 180-day plan of learner-authored checklist items with no generated content — that premise no longer holds under the revised Vision; re-derive the spec from this scope rather than reusing the old one as-is.

### Epic-2: Vocabulary & Spaced Repetition Review
- Priority: Must
- Scope: Lets the learner capture new vocabulary and reviews it on a spaced-repetition schedule that surfaces exactly what's due, so retention doesn't depend on memory or willpower alone. Vocabulary due for review is also a direct input into Epic-1's daily personalization, so review isn't just a standalone list — due words shape what today's generated exercises contain. Traces to Vision goals G-2, G-4.
- Future spec slug: vocabulary-review

### Epic-3: Mistake Tracking & Pattern Insight
- Priority: Must
- Scope: Lets the learner log individual mistakes across all four skills with enough detail (what went wrong, why) to later group them into recurring patterns, so those patterns surface before they calcify into habits. Recurring mistake patterns are also a direct input into Epic-1's daily personalization, closing the loop from "what went wrong" to "tomorrow's practice targets it." Traces to Vision goals G-2, G-3.
- Future spec slug: mistake-tracking

### Epic-4: Practice Result Tracking & Progress Visibility
- Priority: Should
- Scope: Aggregates results across all four skills and shows the trend over time, so momentum and weak areas are visible rather than felt. The primary source of Reading/Listening results is now Epic-9/Epic-10's auto-scoring of AI-generated exercises, and Writing/Speaking results come from Epic-7/Epic-8's AI-graded submissions; manual logging of practice done outside the app remains available as a supplementary path, not the primary one. Traces to Vision goal G-5.
- Future spec slug: progress-tracking
- Note: downgraded from Must — the daily lesson loop (Epic-1/7/8/9/10) functions and delivers the core value on its own without a trends view; this epic makes progress *visible*, which serves Vision goal G-5, but nothing else structurally depends on it.

### Epic-5: Data Portability & Export
- Priority: Must
- Scope: Lets the learner export the entirety of their learning data — including AI-generated lessons (Reading/Listening/Writing/Speaking prompts), vocabulary, mistakes, practice results, and submissions — at any time into a portable format, so they always hold an independent copy and are never locked into this application's hosting, database, or AI provider. Traces to Vision goal G-6.
- Future spec slug: data-portability

### Epic-6: Personal Access Protection
- Priority: Must
- Scope: Ensures that only the learner themselves can view or modify their study data, generated lessons, and submissions once the application is reachable over the public Internet — a single-user login/access gate, not a multi-role permission system. Traces to Vision goal G-8.
- Future spec slug: access-protection

### Epic-7: AI-Assisted Writing Coaching
- Priority: Must
- Scope: Presents the learner with a Writing prompt — sourced from Epic-1's daily personalization by default, though the learner may also submit ad-hoc — and returns AI-generated feedback scored against the four official IELTS Writing criteria (Task Response/Achievement, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy), including specific sentence-level corrections — so the learner knows exactly what to fix, not just a single band number. Raised from Should to Must: under the revised Vision, Writing is one of the four skills the daily lesson plan must always cover. Traces to Vision goals G-1, G-7.
- Future spec slug: writing-coach

### Epic-8: AI-Assisted Speaking Coaching
- Priority: Must
- Scope: Presents the learner with a Speaking prompt — sourced from Epic-1's daily personalization by default, though the learner may also submit ad-hoc — and returns AI-generated feedback on Fluency & Coherence, Lexical Resource, and Grammar against IELTS Speaking criteria from a recording plus transcription. Pronunciation scoring from the transcript alone is explicitly out of this epic's scope — estimating pronunciation without audio-level analysis produces unreliable feedback; a dedicated speech-assessment capability is a separate, later decision. Raised from Should to Must for the same reason as Epic-7. Traces to Vision goals G-1, G-7.
- Future spec slug: speaking-coach

### Epic-9: AI-Generated Reading Practice & Auto-Scoring
- Priority: Must
- Scope: Generates a Reading passage and comprehension questions targeted at today's personalization focus (Epic-1), lets the learner answer, and scores the answers immediately and objectively (Reading correctness is well-defined, unlike Writing/Speaking) — feeding the result into Epic-4's progress view and flagging wrong answers as candidate entries for Epic-3's mistake log. Traces to Vision goals G-1, G-2, G-5.
- Future spec slug: reading-practice
- Note: did not exist as an epic before this revision — Reading practice was previously assumed to happen outside the app, with only the result logged via Epic-4.

### Epic-10: AI-Generated Listening Practice & Auto-Scoring
- Priority: Must
- Scope: Generates a Listening script and comprehension questions targeted at today's personalization focus, produces audio the learner can play from that script, and scores the learner's answers objectively — the same feedback loop into Epic-3/Epic-4 as Epic-9. Traces to Vision goals G-1, G-2, G-5.
- Future spec slug: listening-practice
- Note: did not exist as an epic before this revision, for the same reason as Epic-9. Requires a text-to-speech capability the current architecture does not yet have — this is a new cross-cutting decision for `/business:architecture` to resolve, not assumed here.

## Out of Scope (product-level)
- Multi-user, social, or collaborative capability of any kind (accounts for others, sharing, leaderboards, peer review) — this remains a single-learner tool, not a commercial LMS.
- Any commercial capability (payment, subscription, resale of access).
- Multi-role or enterprise-grade authentication (SSO, role-based access control) — Epic-6 is a single-user access gate only.
- Pronunciation scoring derived from a text transcript alone (see Epic-8).
- A statically-authored, bulk-composed question bank — Epic-9/Epic-10 generate content on demand; there is no pre-written library to maintain.
- A large-scale exam-simulation question bank or full mock-test engine.
- Public-facing marketing or a landing page.
- Weekly reports, smart recommendations, or PDF export — mentioned as a possible later phase in the source spec document, but not yet backed by a Vision goal; do not start a spec for this without first amending the Vision.

## Constraints
- Single maintainer, part-time effort — epics should be sized so any one of them can be built incrementally without requiring sustained full-time work.
- The application has real, ongoing operating costs (hosting, database, AI API usage, and now text-to-speech for Epic-10) — prefer free/hobby tiers of chosen providers where available, and keep AI usage cost-conscious: each day's lesson content (Epic-1/9/10) is generated once and reused, never silently regenerated on every page view, and Writing/Speaking evaluation (Epic-7/8) still happens only on explicit learner submission.
- No secret (AI provider API key, database credentials, or any other credential) may ever be committed to source control or exposed to the frontend — this is enforced by the architecture itself (all AI/database calls go through the backend only), not left to convention.
- Learner's personal data (generated lessons, study history, vocabulary, mistakes, submissions) must remain exportable by the learner at any time (Epic-5) even though it now lives in server-side storage rather than solely on the learner's own device.
