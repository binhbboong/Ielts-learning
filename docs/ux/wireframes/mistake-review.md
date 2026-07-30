# Wireframe: Mistake Review
Supports journey: docs/ux/journeys/solo-ielts-learner-mistake-tracking.md (steps 7-9)

## Purpose
Let the solo learner, in one deliberate weekly sitting, see which mistake-reason categories recur across the week's logged mistakes and recall concrete examples behind each one — turning a pile of individual misses into a small set of named, evidence-backed patterns worth correcting.

## Notes on scope
This one screen absorbs all three candidate-screen names from the journey's candidate list:
- "Mistake Review / Log screen (chronological list)" -> **List view** (a view-mode)
- "Grouped-by-reason view" -> **Grouped view** (the other view-mode, and the default)
- "Category detail / expanded entries view" -> **Category Detail** (a drill-down state reached by selecting one category from Grouped view, not a separate screen)

The header, view-toggle, and period selector are shared chrome; only the main content region changes shape depending on view mode / drill-down depth.

## Layout

### Shared chrome (all view modes)
```
+------------------------------------------------------------------+
| Header: "Mistake Review"        Period: [This week v]  [Refresh] |
| View toggle:  ( List )  ( Grouped by reason )   <- default: Grouped |
+------------------------------------------------------------------+
| Main content region (shape depends on view mode/state below)     |
|                                                                    |
+------------------------------------------------------------------+
```

### Variant A — Grouped view (default, high priority — journey step 8-9)
```
+------------------------------------------------------------------+
| Header / period selector / view toggle (shared chrome)           |
+------------------------------------------------------------------+
| Top recurring reasons this period (ranked, no filtering needed)  |
|                                                                    |
|  1. Misread the question .............. 7 mistakes  [>]          |
|  2. Missed a paraphrase ............... 5 mistakes  [>]          |
|  3. Didn't know the vocabulary ......... 3 mistakes  [>]          |
|  ---------------------------------------------------------------  |
|  Other categories (lower count, still visible, not hidden):      |
|  4. Misheard audio detail .............. 2 mistakes  [>]          |
|  5. Time pressure / rushed .............. 1 mistake  [>]          |
|                                                                    |
| (selecting any row, or its [>] , opens Category Detail)          |
+------------------------------------------------------------------+
```

### Variant B — List view (chronological, secondary)
```
+------------------------------------------------------------------+
| Header / period selector / view toggle (shared chrome)           |
+------------------------------------------------------------------+
| Sort: Newest first                                                |
|                                                                    |
|  Jul 28  Reading   "Misread the question"     [View]              |
|  Jul 27  Listening "Didn't know the vocab"    [View]              |
|  Jul 25  Reading   "Missed a paraphrase"       [View]              |
|  Jul 24  Writing   "Misread the question"     [View]              |
|  Jul 22  Listening "Misheard audio detail"     [View]              |
|  ...                                                              |
+------------------------------------------------------------------+
```

### Variant C — Category Detail (drill-down from a Grouped-view row; journey step 9, the payoff)
```
+------------------------------------------------------------------+
| < Back to Grouped view                                            |
| Category: "Misread the question"  --  7 mistakes this period      |
+------------------------------------------------------------------+
| Concrete examples (the evidence behind the pattern):              |
|                                                                    |
|  Jul 28 - Reading, Q12 (True/False/Not Given)                     |
|    Your answer: "True"   Correct: "Not Given"                     |
|    Note: "Assumed detail was stated, it wasn't in the passage"    |
|                                                                    |
|  Jul 24 - Writing Task 1, prompt interpretation                   |
|    Your answer: [summary of response]   Correct: [expected focus] |
|    Note: "Answered the wrong sub-question"                        |
|                                                                    |
|  ... (remaining 5 examples, same format, scrollable)               |
|                                                                    |
|  [Jump to skill breakdown: Reading 4 · Writing 2 · Listening 1]   |
+------------------------------------------------------------------+
```

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| View toggle (List / Grouped by reason) | Lets the learner switch between raw chronological log and pattern view; Grouped is default per step 8's risk that grouping must be "immediately visible," not something the learner has to dig for | High |
| Period selector (e.g. "This week") | Scopes the review to a deliberate, bounded chunk matching the weekly review habit from step 7 | Medium |
| Ranked reason-category list (Grouped view) | Surfaces recurring reasons up front with counts, with no manual filtering required — directly answers step 8's risk | High |
| Category row count + drill-down affordance ([>]) | Signals which categories are worth investigating and provides the one-tap path to supporting examples (step 9 payoff) | High |
| "Other categories" sub-list | Keeps low-count categories visible rather than hidden, so a category isn't silently dropped just because it's not top-3 | Medium |
| Category Detail: example list with own answer / correct answer / reason note | Delivers the "concrete examples" the learner needs to recall specifics and act on the pattern, not just a vague label (step 9 success criterion) | High |
| Category Detail: skill breakdown (e.g. Reading 4 · Writing 2) | Lets the learner see whether a reason is skill-specific or cross-skill, adding one more layer of actionable insight | Medium |
| Back-to-Grouped-view link | Keeps the drill-down feeling like a state of this screen, not a navigational dead end | Medium |
| List view rows (date, skill, reason, [View]) | Supports quick chronological scanning / spot-checking a specific recent entry, a lower-priority alternate lens vs. the default Grouped view | Low-Medium |
| Refresh control | Re-pulls the current period's data (relevant since this is a client-only app with local data ownership) | Low |
| Row-level [View] (List view) | Opens the single mistake's full logged detail (same underlying entry data as Category Detail examples) | Low |

## States
- **Empty**: No mistakes logged in the selected period (or ever). Shown as a positive, reassuring message — not an error — e.g. "No mistakes logged this week — nothing to review yet. Keep practicing, or widen the period to see earlier entries." No ranked list, no chart; period-selector remains available to check a different range. This matters because step 7 frames review as unhurried and calm; an empty state should read as "you're clean," not "something's broken."
- **Loading**: Shared chrome (header, toggle, period selector) renders immediately; main content region shows a lightweight placeholder (e.g. "Loading mistakes...") in place of the ranked list or timeline. View toggle stays interactive-looking but content swap is deferred until data resolves.
- **Error**: Main content region shows a short, plain-language message (e.g. "Couldn't load your mistake log for this period.") plus a retry action. Chrome (header/toggle/period selector) stays visible and usable so the learner isn't fully blocked from trying a different period or retrying. Since this is a client-only app with local data ownership, this state most likely maps to a local read/storage failure rather than a network error — message should stay agnostic to cause.
- **Populated**: Default entry is Grouped view (Variant A) ranked by count, matching the priority that pattern-visibility comes first (step 8). Learner may toggle to List view (Variant B) for a chronological pass, or drill into any category row to reach Category Detail (Variant C) for the example-backed payoff (step 9). Back-navigation from Category Detail returns to Grouped view, preserving the selected period.
