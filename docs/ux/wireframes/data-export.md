# Wireframe: Data Export
Supports journey: none yet — this epic has no journey mapped; grounded directly in docs/specs/data-portability/Specification.md

## Purpose
Let the authenticated learner produce, on demand, one complete self-readable export of all their learning data and get concrete confirmation it succeeded — this screen only ever renders for an already-authenticated learner (FR-9).

## Layout
```
+----------------------------------------------------------------+
| Header: Personal IELTS Learning Dashboard                        |
+----------------------------------------------------------------+
| Nav: [Dashboard] [Today's Plan] [Vocabulary] [Mistakes]           |
|      [Progress] [Data Export]                                    |
+----------------------------------------------------------------+
| Main:                                                            |
|                                                                   |
|  Export All Data                                                 |
|  One file containing your study plan/task history, vocabulary,   |
|  mistake log, practice results, and Writing/Speaking submissions |
|  with their AI feedback. Always everything — no partial export.  |
|                                                                   |
|  -> [ Export All Data ]                                          |
|                                                                   |
|  Status region (shows Loading / Export-Confirmation / Error      |
|  state below, in place, once the action is triggered)            |
|                                                                   |
+----------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| "Export All Data" action button | The single action FR-1/FR-5 requires — one button that produces the whole export, triggerable at any time with no limit | High |
| Export scope description | States up front that the export always covers all five data categories in full (FR-1, FR-2), so the learner doesn't look for category options that intentionally don't exist | Medium |
| Status region | Single place the button's result renders (loading, confirmation, or error) so the learner never has to guess whether the click did anything | High |
| Export-Confirmation content (timestamp + completeness statement) | Directly satisfies FR-6: concrete evidence — not a generic "Success" — that the export is complete and reflects the learner's current data | High |
| Retry control (Error state only) | Directly satisfies FR-7: lets the learner immediately retry after a failed export with no data loss and no extra steps | High |

## States
- **Empty**: N/A — this screen has no data to be "empty" of; the action is always available regardless of export history, so there is no distinct empty state beyond the default populated layout above.
- **Loading**: button shows an in-progress state (e.g. "Exporting...") and is disabled to prevent duplicate concurrent requests; status region shows a brief in-progress indicator while the server assembles the export.
- **Error** (FR-7): status region shows a failure message clearly distinct from the success confirmation (e.g. "Export failed. Your data is unchanged — try again."), explicitly reassuring the learner no data was lost, with the "Export All Data" button immediately re-triggerable — no extra step, no page reload required.
- **Populated** (default / Export-Confirmation, FR-6): the happy-path layout above; after a successful export, the status region shows a named confirmation stating the export is complete and exactly when it was produced (e.g. "Export complete — produced 2026-07-29 at 14:32."), plus that the file is now available to keep (FR-4). This is a persistent, concrete statement, not a transient toast, and the learner may immediately trigger another export (FR-5) which replaces this confirmation with a fresh one.
