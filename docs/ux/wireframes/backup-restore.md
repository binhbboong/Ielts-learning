# Wireframe: Backup & Restore
Supports journey: docs/ux/journeys/solo-ielts-learner-data-backup-restore.md

## Purpose
Give the learner one settings-style screen to deliberately export all their client-only data to a file, or restore it from a previously exported file, with no guided flow and no ambiguity at the two highest-risk moments (export confirmation, overwrite warning).

## Layout
```
+---------------------------------------------------------------+
| Header: Personal IELTS Learning Dashboard                      |
+---------------------------------------------------------------+
| Nav: [Dashboard] [Today's Plan] [Vocabulary] [Mistakes]         |
|      [Progress] [Backup & Restore]                             |
+---------------------------------------------------------------+
| Main:                                                          |
|                                                                 |
|  1. Last Backup Status readout                                 |
|     "Last backup: 9 days ago (2026-07-20, 14:32)"               |
|     (plain text, no action here — action lives in section 2)   |
|                                                                 |
|  2. Export section                                             |
|     "Export All Data"                                          |
|     One JSON file: study plan, vocabulary, mistakes,            |
|     practice results. No partial/selective export.             |
|     -> [ Export All Data ]                                     |
|                                                                 |
|     (on click, screen shows the Export-Confirmation state       |
|      described below, in place or as an inline panel)          |
|                                                                 |
|  3. Import / Restore section                                   |
|     "Import / Restore from Backup"                             |
|     Restores a previously exported JSON file.                  |
|     Warning line (always visible, not just on click):           |
|       "This will overwrite any existing data on this device."   |
|     -> [ Import / Restore ]                                    |
|                                                                 |
|     (on click: native file-picker state, then                  |
|      Restore-Confirmation/overwrite-warning dialog state)      |
|                                                                 |
+---------------------------------------------------------------+
```
(ASCII sketch — structure and priority, not pixels)

## Key Elements
| Element | Purpose | Priority |
|---|---|---|
| Last Backup Status readout | Answer step 1/step 2's implicit question ("am I current?") the instant the learner lands, without requiring them to trigger an export just to check | High |
| "Export All Data" action | Single, findable action matching step 2/3 — high-proficiency persona expects no wizard, one button that does the whole job | High |
| Export scope note ("one file... no partial exports") | Sets expectation up front that there is nothing to configure or track, so the learner doesn't hunt for options that don't exist | Medium |
| Export-Confirmation panel (filename + timestamp + save location) | Directly answers step 4's Medium risk: if it's unclear the file exists and where it went, the learner can't trust the backup is real — this is a named state, not a transient toast | High |
| "Import / Restore" action | Findable, parallel-structured counterpart to Export, matching step 8's goal of locating the restore path as easily as export was found | High |
| Persistent overwrite-warning line in the Import section (before any click) | Sets expectation early rather than surprising the learner only at the confirmation dialog, reducing the chance the dialog itself reads as a last-second ambush | Medium |
| Native file-picker step (OS-level, not custom UI) | Lets the learner select their own JSON file with no in-app format guesswork, per step 9 — intentionally undesigned here since it is outside the app's UI surface | Low |
| Restore-Confirmation Dialog (overwrite warning) | Directly answers step 10's Medium risk of stall/abandonment — must state plainly what will be overwritten and give an explicit, low-ambiguity way to proceed or back out | High |
| Cancel/back-out control on the Restore-Confirmation Dialog | Gives the hesitant learner (per step 10's emotional-arc note) a safe, obvious exit instead of forcing a binary confirm-or-stuck choice | High |

## States
- **Empty**: no backup has ever been taken on this device (fresh install, never exported). Last Backup Status reads "No backup yet" instead of a stale or blank date — distinct from "0 days ago" or an empty string, so the learner isn't left guessing whether the app is broken. Export and Import sections remain fully visible and actionable; nothing here is gated behind having backed up before.
- **Loading**: Export button shows a brief in-progress state ("Exporting...") while the app serializes local data to a file; Import button shows "Reading file..." while the selected JSON is parsed and validated before the Restore-Confirmation Dialog appears. Both are momentary (client-side, no network) but must not be skipped, since an instant jump straight to confirmation could read as if nothing happened.
- **Error**: (a) Export fails (e.g., browser blocks the download) — show an explicit message distinct from success ("Export failed — try again" ) and leave the "Export All Data" action re-triggerable; last-backup status stays unchanged so a failed attempt never falsely updates it. (b) Import fails validation (not a recognized backup file, corrupted JSON, wrong shape) — show a clear rejection message before ever reaching the overwrite-warning dialog, so the learner is never asked to confirm overwriting good data with a bad file. No partial/silent restore is possible in the error state.
- **Populated (default)**: the happy-path layout above — Last Backup Status shows a real date, Export and Import sections both actionable, warning line visible under Import at rest.
- **Export-Confirmation** (named state, addresses step 4's Medium risk): after a successful export, show filename (e.g. `ielts-backup-2026-07-29-1432.json`), timestamp, and an explicit statement of where the browser saved it (e.g. "Saved to your Downloads folder as..."); also updates the Last Backup Status readout in place so step 1's dashboard indicator has fresh data to reflect. This directly closes the "not sure the backup is real" gap the journey flags.
- **Restore-Confirmation / overwrite-warning dialog** (named state, addresses step 10's Medium risk): modal or inline dialog stating plainly what will happen — e.g. "Restoring will overwrite all current data on this device with the contents of [filename]. This cannot be undone." — with two clearly weighted actions: a default/neutral `[ Cancel ]` and a deliberate `[ Confirm Restore ]` that is not pre-focused or accidentally easy to trigger. Purpose is to let the learner proceed with confidence, and equally to let them back out cleanly without feeling forced, per the journey's stall/abandonment risk.
