# User Journey: Mistake Logging & Weekly Pattern Review
Persona: docs/business/personas/solo-ielts-learner.md

## Scenario
The learner is partway through an evening practice session (e.g. a Reading passage or Listening section) and gets a question wrong. They want to log that mistake with enough detail while it's still fresh, then — about a week later, once several mistakes have piled up — come back to review them grouped by reason to spot what's recurring before it becomes a habit. Traces to Vision goal G-2 (future spec slug: `mistake-tracking`, per `docs/business/PRD.md` Epic-3).

## Steps
| # | Action | Touchpoint | Persona's goal at this step | Risk of drop-off |
|---|---|---|---|---|
| 1 | Gets a question wrong during self-marked practice (Reading/Listening/Writing/Speaking) | External study material (book, past paper, mock test) | Notice the miss while still in context, before moving on | Low — this is the trigger, not yet an app interaction |
| 2 | Opens "Log Mistake" from the current study context | Log Mistake entry point (e.g. action on today's task) | Capture the mistake without losing their place in the session | Medium — if logging feels like a detour from the task at hand, the learner may decide to "log it later" and never return |
| 3 | Records skill, question type, and source | Mistake logging form (step 1: what/where) | Give the mistake enough context to be findable later | Low — short, factual fields, low cognitive load |
| 4 | Enters their own answer and the correct answer | Mistake logging form (step 2: answers) | Preserve the concrete specifics needed to later "cite concrete examples" (Vision success metric) | Low-Medium — if the correct answer isn't at hand (e.g. answer key elsewhere), the learner may abandon the entry half-filled |
| 5 | Writes a short explanation and picks a mistake-reason category (e.g. missed a paraphrase, misread the question, didn't know the vocabulary) | Mistake logging form (step 3: why + reason category) | Name the *why*, not just the *what*, so it can later be grouped into a pattern | High — right after getting something wrong is exactly when the learner is least motivated to stop and reflect; this step feels the most like homework and is the most likely to be skipped or rushed with a generic reason |
| 6 | Saves the mistake and returns to the practice session | Mistake logging form (save) → back to prior study context | Resume real study with the mistake now safely captured | Low — a fast save-and-return preserves session momentum |
| 7 | *(Time jump: about a week later, several mistakes have accumulated)* Opens the Mistake Review view | Mistake Review / Log screen | Look back over the week's mistakes rather than losing track of them between sessions | Low — deliberate, unhurried entry point, unlike step 5 |
| 8 | Views mistakes grouped or filterable by mistake-reason category | Mistake Review screen (grouped-by-reason view) | See which reasons recur across skills, not just a flat list of individual misses | Medium — if grouping isn't immediately visible or requires manual filtering, the pattern may stay hidden and the review feels like it wasted time |
| 9 | Identifies the top recurring reason categories and recalls concrete examples behind them | Mistake Review screen (category detail / expanded entries) | Walk away with named, evidence-backed patterns to actually correct in future sessions | This is the payoff step — if the categories don't clearly surface with supporting examples, the whole review yields a vague feeling instead of an actionable insight |

## Emotional Arc
Starts with a small sting of getting something wrong (step 1), dips further at step 5 — the "why did I get this wrong" reflection is the most effortful and least rewarding moment, right when frustration is already elevated from the missed question — then relief at step 6 once the mistake is safely captured and the learner can return to studying. The arc resets calm and reflective at step 7 (a week later, no longer in the heat of a miss), builds anticipation through step 8, and should land on a genuine "aha" of recognition at step 9, seeing the same reasons repeat across entries — the moment that makes the whole logging habit feel worth the earlier friction.

## Success Criteria
- The learner logs a mistake with skill, question type, source, both answers, an explanation, and a reason category in under 2 minutes per entry, without the logging effort discouraging them from continuing the practice session it interrupted.
- By the end of week 4, the learner can open the Mistake Review view and name their top 3 recurring mistake-reason categories with concrete example mistakes cited for each — directly meeting the Vision G-2 success metric.

## Candidate Screens
- Log Mistake entry point (in-context action from a study/practice screen)
- Mistake logging form (what/where, answers, why + reason category)
- Mistake Review / Log screen (chronological list)
- Grouped-by-reason view (mistakes clustered by mistake-reason category)
- Category detail / expanded entries view
