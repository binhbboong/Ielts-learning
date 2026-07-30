# Wireframe: Listening Exercise & Result
Supports journey: docs/ux/journeys/solo-ielts-learner-daily-lesson.md

## Purpose
Let the learner play an AI-generated (text-to-speech) audio clip targeted at their own recent mistakes/vocabulary, answer comprehension questions, and get an objective score immediately — while explicitly surfacing audio load/playback failure, the journey's single highest-risk moment.

## Layout

**A — Answering (populated)**
```
+---------------------------------------------------------------+
| Header: Listening — Today's Clip                [ Back to Today]|
+---------------------------------------------------------------+
| Section: Why this clip                                          |
|   "Targets: numbers/dates, the phrase 'as opposed to'"          |
+---------------------------------------------------------------+
| Section: Audio player                                           |
|   [ >  Play ]   0:00 / 1:45   [============------------]        |
|   [ Replay ]                                                    |
|   (no transcript shown before answering, matching real          |
|    Listening conditions; replay allowed, unlimited)              |
+---------------------------------------------------------------+
| Section: Questions (revealed once ready; can answer while       |
|   listening or after)                                            |
|   Q1. What time does the event start?                            |
|       ( ) 9:00   ( ) 9:30   ( ) 10:00   ( ) 10:30                |
|   Q2. ...                                                        |
|   ... (5-8 questions typical)                                    |
+---------------------------------------------------------------+
| Footer:                                   [ Submit Answers ]     |
+---------------------------------------------------------------+
```

**B — Result (after submission) — primary payoff**
```
+---------------------------------------------------------------+
| Header: Listening — Result                      [ Back to Today]|
+---------------------------------------------------------------+
| Score: 5 / 7 correct                                             |
+---------------------------------------------------------------+
| Section: Per-question review                                     |
|   Q1. [correct]  Your answer: 9:30                               |
|   Q2. [wrong]    Your answer: 10:00   Correct: 10:30              |
|       -> [ Add to Mistake Notebook ]                              |
|   ... (same shape per question)                                  |
+---------------------------------------------------------------+
| Section: Transcript (revealed only after submission)             |
|   [ full script text, for review ]                               |
+---------------------------------------------------------------+
| Footer:                              [ Back to Today's Lesson ]  |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| "Why this clip" personalization note | Same rationale as Reading — makes personalization felt during the exercise | High |
| Audio player (play/pause, position, replay) | The core new interaction this screen introduces; must be unmistakable whether audio is loading, playing, or has failed (journey's #1 flagged risk) | High |
| Play/loading/failed state on the player itself | If Text-to-Speech generation or audio delivery fails, the player must show a distinct, actionable failure state right where the learner is looking — not a generic screen-level error the learner has to hunt for | High |
| Questions | Objectively scorable comprehension check | High |
| Submit Answers action | Triggers immediate, local scoring — same no-AI-wait property as Reading | High |
| Score summary + per-question review | Same as Reading | High |
| "Add to Mistake Notebook" quick action | Same as Reading, closes the loop into Epic-3 | High |
| Transcript, shown only after submission | Lets the learner review what they actually heard without letting it leak into the answering phase (would defeat the exercise) | Medium |
| Back to Today's Lesson | Same as Reading | Medium |

## States
- **Empty**: should not occur — audio/questions are generated before this screen is reachable (Daily Overview gates entry on "Ready" state).
- **Loading**: two distinct moments — (1) the screen itself loading the exercise metadata/questions, brief; (2) the audio player's own loading state before the clip is playable, which must be visibly different from "ready to play" so the learner doesn't think a click did nothing.
- **Error**: the journey's highest-risk case — audio fails to load or errors mid-playback despite Daily Overview showing "Ready" for Listening. The player itself shows "Couldn't load audio — [ Retry ]" scoped to the player, distinct from a full-screen error, since the questions/passage-equivalent context may still be worth showing. If retry also fails, offer a path back to Daily Overview without losing the rest of the day's progress.
- **Populated**: layout A while answering (transcript hidden), layout B after submission (transcript revealed) — B receives the most layout priority, same rationale as Reading.
