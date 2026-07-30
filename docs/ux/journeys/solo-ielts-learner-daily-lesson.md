# User Journey: Daily AI-Generated Lesson Across 4 Skills
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
The learner sits down for their daily IELTS study session (typically an evening after work) and opens the app expecting a ready-made set of practice across Reading, Listening, Writing, and Speaking — targeted at their own recent mistakes and due vocabulary — with nothing left for them to find or prepare themselves.

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Open the app | Daily Overview screen | See at a glance what's ready today across all 4 skills | If content for a skill is still being generated, the learner doesn't know whether to wait or come back later — needs a clear per-skill "ready / generating" state, not a blank or broken-looking screen |
| 2 | Pick a skill to start with | Daily Overview screen | Choose an entry point (any order, no forced sequence) | Low — the learner already does this today across separate features |
| 3 | Read the passage and answer questions | Reading Exercise screen | Complete a comprehension exercise that feels aimed at their actual level/weak points | If the generated passage/questions feel mismatched to ability (too easy/hard) or unrelated to any known weak point, personalization trust erodes |
| 4 | Submit answers, see the score immediately | Reading Result (inline or own screen) | Get instant, objective feedback — no waiting | Low — scoring is objective/local, should be immediate |
| 5 | Play the Listening audio and answer questions | Listening Exercise screen | Same as Reading, but depends on audio actually loading and playing | Highest risk in the journey — this is a brand-new integration (Text-to-Speech); if audio fails to load/play, the learner is fully blocked on this skill for the day |
| 6 | Submit answers, see the score immediately | Listening Result (inline or own screen) | Same instant feedback as Reading | Low, once audio played successfully |
| 7 | Respond to the day's Writing prompt | Writing Submission screen (existing) | Submit a response without having to invent their own topic | Low — prompt is already provided; existing flow |
| 8 | Wait for AI feedback, then read it | Writing Result screen (existing) | Understand exactly what to fix, not just a band number | Existing behavior, already validated by Epic-7 |
| 9 | Respond to the day's Speaking prompt (record) | Speaking Submission screen (existing) | Submit a spoken response without inventing their own topic | Recording itself is a known minor friction point (existing) |
| 10 | Wait through transcription → evaluation, then read feedback | Speaking Result screen (existing, async status-tracked) | See concrete per-criterion feedback | The async wait (transcribing → evaluating) needs a visible in-progress state so the learner doesn't think it's stuck — existing risk, already designed around (status-tracked processing) |
| 11 | Return to Daily Overview | Daily Overview screen | See all 4 skills marked complete for today | Low — this is the payoff moment |
| 12 | (Optional) Review any mistakes auto-logged from wrong Reading/Listening answers | Mistake Review screen (existing) | Confirm the loop closes — today's mistakes will shape tomorrow's lesson | Low, but if nothing ever visibly changes tomorrow because of today's mistakes, personalization trust erodes over repeated days (a slow-burn risk, not a single-session one) |

## Emotional Arc
Opens neutral-to-hopeful (will today's content actually be ready and relevant?). Reading/Listening give quick, objective wins — low-friction, fast feedback loop, builds early momentum. Listening carries real risk of a hard failure (audio) that would sour the whole session if it happens — this is the single highest-stakes moment in the journey precisely because it's new. Writing/Speaking are the effortful middle — composing a response, then an anxious wait for AI judgment — resolving into relief/insight once specific, actionable feedback arrives (already validated territory from Epic-7/8). The journey closes on accomplishment: all 4 skills done, no external material sourced, and a felt sense that today's mistakes will inform tomorrow's practice.

## Success Criteria
- The learner completes practice across all 4 skills in one sitting (roughly 45–60 minutes) without ever leaving the app to find or prepare material, and without any skill being unusable due to a generation or audio failure.
- At least one of the day's Reading/Listening/Writing exercises is visibly connected to a specific recent mistake or a vocabulary word due for review, so personalization is felt, not just claimed.

## Candidate Screens
- Daily Overview (today's lesson across 4 skills, per-skill ready/generating state)
- Reading Exercise
- Reading Result
- Listening Exercise (with audio player)
- Listening Result
- Writing Submission (existing)
- Writing Result (existing)
- Speaking Submission (existing)
- Speaking Result (existing)
- Mistake Review (existing, now also auto-populated from Reading/Listening misses)
