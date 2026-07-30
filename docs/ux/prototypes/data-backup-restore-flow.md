# Prototype: Data Backup & Restore Flow
Journey: docs/ux/journeys/solo-ielts-learner-data-backup-restore.md

## Screen Sequence
1. docs/ux/wireframes/dashboard-overview.md (Populated state) — triggered by: normal app entry; learner notices the "Last backup: N days ago" Backup Status indicator
2. docs/ux/wireframes/backup-restore.md (Populated state) — triggered by: clicking [ Back Up Now ] on the dashboard indicator, or navigating to "Backup & Restore" via the nav bar deliberately (journey step 2)
3. docs/ux/wireframes/backup-restore.md (Export-Confirmation state) — triggered by: clicking [ Export All Data ] on screen 2
4. *(external step, no screen — learner moves the downloaded JSON to their own storage: cloud drive, USB, another machine)*
5. *(external trigger, no screen — a real risk event occurs: new laptop, cleared browser storage, OS reinstall, or a deliberate self-test)*
6. docs/ux/wireframes/dashboard-overview.md (Empty state, post-data-loss) — triggered by: opening the app on the now-empty browser
7. docs/ux/wireframes/backup-restore.md (state — see Open Questions) — triggered by: clicking [ Restore from Backup ] on the dashboard Empty state
8. System file picker (native OS state, not custom app UI) — triggered by: clicking [ Import / Restore ] on screen 7
9. docs/ux/wireframes/backup-restore.md (Restore-Confirmation / overwrite-warning dialog state) — triggered by: selecting the backup JSON file in the file picker, after it passes the app's "Reading file..." validation
10. docs/ux/wireframes/dashboard-overview.md (Populated state) — triggered by: clicking [ Confirm Restore ] on screen 9 — landing back on Dashboard / Today Overview in its normal populated state is the proof-of-restore moment; there is no dedicated "Post-Restore Verification" screen by design (see Readiness checklist and Open Questions)

## Transitions
| From | Trigger | To |
|---|---|---|
| *(app entry)* | Learner opens the app during normal use | Dashboard / Today Overview (Populated) |
| Dashboard / Today Overview (Populated) | Learner clicks [ Back Up Now ] on the Backup Status banner, or navigates to "Backup & Restore" via the nav bar | Backup & Restore (Populated) |
| Backup & Restore (Populated) | Learner clicks [ Export All Data ] | Backup & Restore (Export-Confirmation state) |
| Backup & Restore (Export-Confirmation state) | Learner moves the downloaded JSON file to durable external storage of their own choosing | *(external step — outside app control, no screen)* |
| *(external step)* | Time passes; a real risk event occurs (new laptop, cleared browser, OS reinstall, or deliberate self-test) | *(external trigger — no screen)* |
| *(external trigger)* | Learner opens the app on the now-empty browser | Dashboard / Today Overview (Empty state, post-data-loss) |
| Dashboard / Today Overview (Empty state) | Learner clicks [ Restore from Backup ] | Backup & Restore (state per Open Question below) |
| Backup & Restore | Learner clicks [ Import / Restore ] | System file picker (native OS state, not custom app UI) |
| System file picker | Learner selects the previously exported JSON file; app parses/validates it ("Reading file..." momentary state, validation passes) | Backup & Restore (Restore-Confirmation / overwrite-warning dialog state) |
| Backup & Restore (Restore-Confirmation dialog) | Learner clicks [ Confirm Restore ] | Dashboard / Today Overview (Populated) |
| Backup & Restore (Restore-Confirmation dialog) | Learner clicks [ Cancel ] | Backup & Restore (Populated) — safe back-out, no data changed, learner can retry Import when ready |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow. Steps 1-5 (export half) map to sequence items 1-4; step 6 (external risk event) is correctly represented as a no-screen trigger; steps 7-11 (restore half) map to sequence items 6-10. Step 12 (spot-check verification) is deliberately represented by landing back on Dashboard (Populated) rather than a dedicated screen — see note below.
- [x] Every transition has a clear, unambiguous trigger, including the two non-custom-UI moments (external file relocation, native file picker) which are named as states rather than invented as wireframes.
- [x] No screen exists in this flow without a stated purpose from the journey — both wireframe files are used only for the states they explicitly document (Populated, Empty, Export-Confirmation, Restore-Confirmation), plus Dashboard's own documented Empty state.
- [x] Open UX questions are listed below, not silently resolved.
- [ ] "Post-Restore Verification" (journey step 12: spot-checking vocabulary due count, mistake log entries, progress/analytics) has no dedicated screen, by the journey's own design ("reusing existing dashboard/vocabulary/mistakes/progress views"). Ending the flow at Dashboard (Populated) is judged **adequate but partial**: the Dashboard's own cards already surface two of the three spot-check signals (Vocabulary Due count, weakest-skill/last-score row) as direct proof-of-restore, without navigating anywhere else. Deeper verification (mistake log entries, full progress/analytics detail) requires navigating into the Mistakes and Progress screens via the nav bar already present on Dashboard — those screens exist for other journeys and are correctly out of scope for this prototype file, per the task's framing. This is **not treated as a gap** in this flow, but is flagged as a genuine open question below about whether that reliance on "the learner will separately navigate over” needs any explicit prompt.

## Open Questions
- [NEEDS CLARIFICATION: After a real data-loss event (browser storage cleared/reinstalled), does the Backup & Restore screen's "Last Backup Status" readout show "No backup yet" (per its documented Empty state, since that status is itself client-side local data and was wiped along with everything else) even though a real backup file does exist externally? If so, this could read as contradictory or alarming right after the learner just clicked "Restore from Backup" from the dashboard's empty state — worth deciding whether the Empty-state Backup & Restore screen needs a variant copy change for this specific path (arriving from a data-loss empty state) versus the plain "never backed up" first-run case.]
- [NEEDS CLARIFICATION: Does clicking [ Restore from Backup ] on the Dashboard Empty state land the learner on the Backup & Restore screen (requiring a further click on [ Import / Restore ]), or does it skip ahead and immediately open the native file picker? The dashboard wireframe's phrasing ("leading into Backup & Restore's Import flow") and the journey's step 8 ("Navigates to Backup & Restore and selects Import/Restore") both allow either reading — this flow assumes the two-step version (land on screen, then click Import/Restore) as the safer, more explicit default, but it is not stated unambiguously in either wireframe.]
- [NEEDS CLARIFICATION: Should the flow document an explicit branch for Import validation failure (corrupted JSON / wrong file) before reaching the Restore-Confirmation dialog? The backup-restore.md wireframe defines this Error state, but the source journey's happy-path steps (7-12) don't include a failure case — this prototype omits it as out of scope for the journey being satisfied, but a future spec pass should confirm that omission is intentional rather than overlooked.]
