# Specification: Mistake Tracking & Pattern Insight
Related UX: docs/ux/prototypes/mistake-tracking-flow.md

## Status
Draft

## Overview
A self-directed IELTS learner makes mistakes across all four skills — Reading, Listening, Writing, Speaking — during self-marked practice, but without a structured way to capture them, the specifics fade and the same errors quietly repeat. This feature lets the learner log a mistake in the moment it happens, capturing not just what was missed but why, and then step back roughly a week at a time to see which reasons for getting things wrong recur most, with the concrete examples to back each one up. It corresponds to PRD Epic-3 (`docs/business/PRD.md`) and traces to Vision goal G-2, whose success metric is that the top 3 recurring mistake categories are identifiable by the end of week 4, with concrete examples the learner can cite.

The feature has two halves. The first is fast, in-context logging: reached as an action from wherever the learner is currently studying, designed to take under two minutes and to never block a save just because some detail (the correct answer, or a settled reason) isn't at hand yet. The second is a deliberate, unhurried weekly review: a chronological pass over everything logged, a ranked view grouped by mistake reason with counts, and a drill-down into any one reason to see the actual mistakes that make it up.

## User Scenarios
- As a learner, I want to log a mistake right after I notice it during practice, so the details are still fresh and I don't lose my place in the study session.
- As a learner, I want to save a mistake entry even when I don't have the correct answer yet or haven't settled on why I got it wrong, so an incomplete detail never costs me the whole entry.
- As a learner, I want to pick a reason for why I made the mistake from a short, consistent list, so my mistakes can later be grouped into patterns instead of staying a flat pile of individual misses.
- As a learner, I want to look back over a week's worth of logged mistakes grouped by reason with counts, so I can see what recurs without manually sorting or filtering anything myself.
- As a learner, I want to drill into one recurring reason and see the concrete examples behind it (my answer, the correct answer, and my explanation), so I can cite real evidence for the pattern rather than a vague impression.
- As a learner, I want to also see my mistakes in a plain chronological list, so I can do a quick recency-based scan when I want that instead of the grouped view.

## Functional Requirements
- FR-1: The system MUST allow the learner to start a new mistake log entry as an action available from within whatever study/practice context they are currently in (Reading, Listening, Writing, or Speaking), without requiring them to leave that context to reach a separate area of the app first.
- FR-2: When a mistake log entry is started from an active study context, the system MUST pre-fill any of the entry's skill and source fields that can be inferred from that context, leaving them editable by the learner.
- FR-3: The system MUST allow the learner to record, for a mistake entry: the skill (Reading, Listening, Writing, or Speaking), the question type, the source material, the learner's own answer, the correct answer, a free-text explanation, and a mistake-reason category.
- FR-4: The system MUST offer the mistake-reason category as a single choice from exactly this fixed set: "Didn't know the vocabulary," "Missed a paraphrase," "Misread the question," "Missing information," "Used outside knowledge," "Ran out of time," "Carelessness," "Wrong grammar," and "Not sure yet / other."
- FR-5: The system MUST allow the learner to mark that the correct answer is not yet known (in place of entering it), and MUST allow the mistake-reason category to be left as "Not sure yet / other," without either choice preventing the entry from being saved.
- FR-6: The system MUST allow a mistake entry to be saved with only the skill and source recorded and every other field (question type, own answer, correct answer, explanation, reason) left blank or at its default, treating such an entry as incomplete rather than rejecting the save.
- FR-7: The system MUST distinguish, in a form retrievable by the learner, between a complete mistake entry and an incomplete one (missing its correct answer and/or a settled reason category).
- FR-8: The system MUST allow the learner to close out of an in-progress mistake entry at any point without discarding what has been entered so far, preserving it as an incomplete entry rather than losing the data.
- FR-9: The system MUST also allow the learner to explicitly discard an in-progress mistake entry, distinct from closing out with the data preserved.
- FR-10: The system MUST allow the learner to view all logged mistakes in a chronological list, most recent first, showing at minimum the date, skill, and mistake-reason category of each entry.
- FR-11: The system MUST allow the learner to view all logged mistakes grouped by mistake-reason category, with each category showing a count of how many mistakes fall under it for the selected review period.
- FR-12: The system MUST rank the grouped-by-reason view by count (highest first), and MUST continue to display categories with lower counts rather than hiding any category that has at least one logged mistake in the selected period.
- FR-13: The system MUST allow the learner to select any single mistake-reason category from the grouped view and see the individual mistakes contributing to that category's count, each showing at minimum the learner's own answer, the correct answer (or its absence, if not yet known), and the explanation (if any).
- FR-14: The system MUST allow the learner to choose a review period to scope both the chronological view and the grouped-by-reason view, with a default period selected automatically when the review is opened.
- FR-14a: For the MVP, the review-period selector MUST provide exactly three presets: "This
  week", "Last week", and "Last 30 days". "This week" and "Last week" use calendar weeks beginning
  Monday and ending Sunday; "This week" is the default. Arbitrary custom date ranges are out of
  scope for the MVP.
- FR-15: The system MUST re-scope the content of whichever view (chronological or grouped) is currently displayed whenever the learner selects a different review period, without requiring a separate reload action.
- FR-16: The system MUST persist all logged mistake entries, complete or incomplete, across sessions, so closing and reopening the app does not lose any previously logged mistake.

## Out of Scope
- Automatic detection or grading of mistakes from practice sessions — every entry is logged manually by the learner; the system does not infer that a mistake occurred.
- AI-suggested or automatically-assigned mistake-reason categorization — the learner always selects the reason themselves from the fixed set.
- Any mistake-reason category beyond the fixed set in FR-4; adding, removing, or customizing categories is not part of this feature.
- Aggregation or cross-referencing with other epics' data (e.g. linking a mistake to a vocabulary entry it stems from, or to a practice-result trend) — that belongs to other epics if pursued.
- Notifications, reminders, or scheduling nudges prompting the learner to log a mistake or to run a weekly review.
- Multi-user, shared, or exported views of mistake data (export/backup is Epic-5's responsibility, not this feature's).
- Editing or resolving an already-saved mistake entry from any screen other than what FR-7's "retrievable form" resolves to — the specific mechanics of that editing/completion path are covered by the Open Questions below, not assumed here.

## Open Questions
- [NEEDS CLARIFICATION: How is an incomplete entry (missing correct answer and/or an unsettled reason category) later resolved or completed? Can the learner edit it afterward directly from the Mistake Review screen, and if so, does that reopen the same logging form in an edit mode, or a separate read-only-then-editable detail view? The source prototype flags this as unresolved.]
- [NEEDS CLARIFICATION: How should an incomplete entry's missing fields render inside the grouped-by-reason category detail and the chronological list — shown as-is with a blank/placeholder "correct answer," visibly flagged as incomplete, or excluded from category counts until completed? The source prototype flags this as unresolved.]
- Resolved 2026-07-29: the default is a fixed Monday-Sunday calendar week. The MVP selector uses
  the three presets "This week", "Last week", and "Last 30 days"; arbitrary/custom ranges are out
  of scope.

## Acceptance Criteria
- [ ] The learner can start a mistake log entry as an in-context action while in a Reading, Listening, Writing, or Speaking study context, and the entry opens with skill/source pre-filled where inferable.
- [ ] The learner can fill in skill, question type, source, own answer, correct answer, explanation, and a mistake-reason category chosen from the fixed nine-option set (FR-4), and save the entry.
- [ ] The learner can save an entry after checking "I don't have the correct answer yet" and/or leaving the reason as "Not sure yet / other," and the entry is saved without error.
- [ ] The learner can save an entry with only skill and source filled in, and it is retrievable afterward, marked as incomplete.
- [ ] Closing an in-progress entry (without explicit discard) preserves everything typed so far as an incomplete entry; explicitly discarding does not preserve it.
- [ ] The Mistake Review view shows a chronological list of logged mistakes, most recent first, with date, skill, and reason visible per entry.
- [ ] The Mistake Review view shows a grouped-by-reason view, ranked by count descending, with every category that has at least one mistake visible (not just the top few).
- [ ] Selecting a mistake-reason category from the grouped view shows the individual example mistakes behind it, each with own answer, correct answer (or its absence), and explanation.
- [ ] Changing the review period re-scopes whichever view is open to the new period's data.
- [ ] All logged mistakes, complete or incomplete, are still present after closing and reopening the app.
