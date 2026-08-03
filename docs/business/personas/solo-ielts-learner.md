# Persona: Solo Software Engineer, Self-Studying IELTS

## Summary
A software engineer with no prior IELTS preparation, studying continuously (no fixed end date) to reach working proficiency in professional English. Wants to open the app each day and get straight to practicing — not spend time finding or preparing material first. Builds and uses their own tool rather than adopting a generic IELTS app, because they want practice that targets their own actual weaknesses and full ownership of their learning data.

## Goals
- Prepare specifically for IELTS Academic, improving from approximately band 3.5 to overall
  6.5 with no skill below 6.0 within 24 weeks.
- Complete a coherent 60-minute daily session whose workload is allocated by priority rather
  than receiving four unrelated exercises every day.
- See the target band, phase, time allocation, and reason each activity was selected.
- Open the app and immediately have a full day's practice ready across all four skills (Reading, Listening, Writing, Speaking) — no external material to find or prepare first.
- Have that practice actually target their own recurring mistakes and vocabulary gaps, not a generic curriculum everyone gets.
- Catch and fix recurring mistakes before they become habits.
- Keep vocabulary review on schedule via spaced repetition, without relying on memory or willpower alone.
- See tangible progress over time across all four skills.
- Keep full ownership and control of their own learning data, with no vendor or platform lock-in.

## Pain Points
- Even with a progress tracker, still had to personally source a Reading passage, find Listening audio, and invent Writing/Speaking prompts every single day — tracking what was done never solved the harder problem of *having something to do*.
- Practice material that isn't tailored to their own mistakes wastes time on things they've already mastered while missing what actually needs work.
- Recurring mistakes go unnoticed and get repeated because there's no structured place to log and review them, let alone feed them back into future practice.
- Vocabulary review lapses without a system that surfaces exactly what's due.
- No clear signal over time on whether skills are actually improving.
- Reluctant to hand personal study data and submissions to a third-party SaaS — wants a tool they can inspect, export from, and fully control.

## Context of Use
- Each learner has an individual account; all goals, generated lessons, answers, feedback,
  vocabulary, mistakes, and progress belong only to that account.
- Daily, self-scheduled study sessions — typically fit around a full-time engineering job (e.g. evenings), so picking up today's ready-made practice with minimal friction matters more than a guided onboarding flow.
- Primarily a desktop/laptop browser. The app is now a hosted client-server product (Angular frontend + FastAPI backend + Postgres), reached over the network — unlike the original client-only design, daily use now requires connectivity and a login.
- Sessions can be interrupted, so all progress must persist reliably server-side without the learner needing to remember to save.

## Technical Proficiency
- High. Comfortable with technology, willing to inspect exported data, and could read/modify the app's own source if needed.
- UX implication: no need for heavy onboarding, tutorials, or hand-holding — direct manipulation is fine. That said, high technical skill doesn't mean the learner wants a cluttered screen while trying to concentrate on English — the actual study surfaces (today's lesson, Reading/Listening exercises, vocabulary, mistakes) should stay low-friction and low-cognitive-load during a study session, distinct from how much configuration/inspection they'd tolerate elsewhere in the app.

## Relationship to Vision/PRD
- The sole persona for this product — Vision's non-goals explicitly exclude multi-user features, so there is intentionally no second persona.
- Primary persona for every PRD epic: Epic-1 (Daily Personalized Lesson Plan), Epic-2 (Vocabulary & Spaced Repetition), Epic-3 (Mistake Tracking), Epic-4 (Practice Result Tracking & Progress), Epic-5 (Data Portability), Epic-6 (Access Protection), Epic-7 (Writing Coaching), Epic-8 (Speaking Coaching), Epic-9 (Reading Practice), Epic-10 (Listening Practice).
- Maps directly to Vision's Target Users/Market and goals G-1 through G-8.
