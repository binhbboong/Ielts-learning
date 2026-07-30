# Specification: Data Portability & Export
Related UX: none yet — the old data-backup-restore-flow.md prototype was designed for the superseded architecture's export/restore UI and should not be assumed correct here without review

## Status
Draft

## Overview
The learner's data now lives as the system of record in server-side storage, not solely in
their own browser — durability of that storage is a given this feature does not need to
re-guarantee. What server-side storage does introduce is dependency: the learner's entire
learning history becomes tied to whichever hosting and database provider happens to run it
today. This feature exists to remove that dependency. At any time, the learner must be able to
produce one complete, self-readable copy of everything they have built up — study plan and task
history, vocabulary, mistake log, practice results, and Writing/Speaking submissions together
with their AI-generated feedback — so that no hosting or database provider, and no AI provider,
ever becomes a permanent lock-in.

Because the data is now reachable over the public Internet and sits behind a login (assumed to
exist per the access-protection epic), this feature also has a boundary to respect: an export
must only ever contain the data belonging to the learner who is currently authenticated, never
another learner's data. This spec covers producing that export on demand and proving it is
complete; it does not cover restoring or importing that data back into any system (see Open
Questions).

## User Scenarios
- As a solo IELTS learner, I want to export the entirety of my learning data in a single action,
  so that I always hold an independent, complete copy and am never dependent on this
  application's hosting or database provider to access my own history.
- As a solo IELTS learner, I want my export to include my Writing/Speaking submissions and the
  AI feedback they received, not just plan/vocabulary/mistakes/results, so that the copy I hold
  is genuinely complete and not missing the data I likely care most about.
- As a solo IELTS learner, I want my exported data to be in a format I can open and read myself
  without this application, so that I am not dependent on this application even to make sense of
  my own exported data.
- As a solo IELTS learner, I want concrete confirmation that an export succeeded and covers
  everything, so that I can trust the copy I just took is actually complete and current, not
  hope that it is.
- As a solo IELTS learner, I want to be absolutely certain that exporting only ever gives me my
  own data and never anyone else's, so that I can trust this capability even though the
  application is now reachable over the public Internet.

## Functional Requirements

### Exporting learner data
- FR-1: The system MUST let the authenticated learner initiate a single action that produces one
  export covering the entirety of their learning data: study plan/task history, vocabulary,
  mistake log, practice results, and Writing/Speaking submissions together with any AI-generated
  feedback those submissions received.
- FR-2: The system MUST NOT offer any partial, selective, or category-by-category export — every
  export produced by this feature MUST include all data categories named in FR-1 in full, for
  every record the learner currently has, with none silently omitted.
- FR-3: The system MUST produce the export in a format the learner can open, read, and process
  themselves using generally available tools, without depending on this application to interpret
  it.
- FR-4: The system MUST make the exported data available to the learner to keep as their own copy
  the moment the export completes — the learner is not required to take any further action for
  the copy to be theirs to keep independent of this application.
- FR-5: The system MUST let the learner produce an export at any time, on demand, regardless of
  how many exports they have produced before, with no limit on how often they may do so.
- FR-6: Upon a successful export, the system MUST present confirmation that identifies the export
  as complete and current — including, at minimum, when it was produced — so the learner has
  concrete evidence the export is real and reflects their present data, not a generic success
  message alone.
- FR-7: If an export attempt does not complete successfully, the system MUST present a failure
  message distinct from the success confirmation and MUST let the learner retry the export
  without any extra step or data loss.

### Data ownership and access boundary
- FR-8: The system MUST only ever include the currently authenticated learner's own data in an
  export — it MUST NOT include any other learner's data under any circumstance.
- FR-9: The system MUST require the learner to be authenticated before permitting any export
  action, and MUST reject an export request from an unauthenticated caller.

## Out of Scope
- Restoring, importing, or otherwise loading previously exported data back into this application
  or any other system — see Open Questions; this spec covers export only unless that question
  resolves otherwise.
- Encrypting, password-protecting, or otherwise restricting access to the exported data once the
  learner has received it — protecting the file after export is the learner's own responsibility.
- Automatic, scheduled, or background exports of any kind — every export is a deliberate,
  learner-initiated action.
- Any indicator, reminder, or nudge about how long it has been since the last export — that
  concern belonged to the superseded backup/restore premise (protecting against data loss with
  no other copy); it does not apply now that server-side storage is the durable system of record.
- Uploading, transmitting, or syncing the exported data to any destination outside the export
  action itself (e.g., cloud-to-cloud transfer to another product) — where the learner keeps or
  sends the exported file afterward is entirely their own choice, outside this feature's control.
- Any in-app viewer or editor for inspecting or modifying the contents of an export after it has
  been produced.
- Recovering or reconstructing data that does not currently exist in server-side storage — this
  feature exports what the learner currently has; it is not a substitute for the durability of
  server-side storage itself.

## Open Questions
- [NEEDS CLARIFICATION: Does this epic require an import/restore capability — the ability to load
  a previously exported copy of data back into this application or a self-hosted successor — or
  is export-only sufficient to satisfy "never locked into this application's hosting or database
  provider"? The PRD scope and Vision goal G-5 both describe the guarantee learners need as being
  able to "get their data back" and "switch providers without losing data," which reasonably
  could be satisfied by a self-readable export alone (the learner or a future tool reads/converts
  it) without this application ever needing to read its own export back in. The old superseded
  spec included restore, but its premise (restore into this same app after local data loss) no
  longer applies. Resolve before planning, since it changes whether this feature has one
  capability or two.]
- [NEEDS CLARIFICATION: Vision goal G-5 and its success criterion both frame portability as
  extending to the AI provider ("không bị khoá vĩnh viễn vào ... một nhà cung cấp hạ tầng hay AI
  cụ thể nào" / "not locked into a specific infrastructure or AI provider"). This spec includes
  AI feedback content as exportable data (FR-1), which addresses not losing that feedback if the
  AI provider changes. Is there any further AI-portability expectation this epic must satisfy —
  for example, the export being structured so feedback could be meaningfully re-interpreted after
  a provider switch — or does including the feedback text/scores as exported data fully satisfy
  the AI-lock-in half of G-5?]

## Acceptance Criteria
- [ ] Triggering the export action as the authenticated learner produces one export containing
  all five data categories (study plan/task history, vocabulary, mistake log, practice results,
  Writing/Speaking submissions with AI feedback), with none omitted, and no selective/partial
  export option exists anywhere (FR-1, FR-2).
- [ ] The produced export can be opened and read using generally available tools, without this
  application (FR-3).
- [ ] Immediately after export completes, the learner has the exported data available to keep as
  their own, with no further required action (FR-4).
- [ ] The learner can trigger a new export at any time, including immediately after a previous
  one, with no cap on frequency (FR-5).
- [ ] A successful export's confirmation states when it was produced and that it is complete,
  distinct from a generic success message (FR-6).
- [ ] A failed export shows a message distinct from success and allows an immediate retry with no
  data loss (FR-7).
- [ ] An export triggered by one authenticated learner never contains another learner's data,
  verified across at least two distinct learner accounts (FR-8).
- [ ] An export request from an unauthenticated caller is rejected and produces no export (FR-9).
