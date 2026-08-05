// Mirrors _BEGINNER_PHASES in backend/app/services/daily_lesson_plan.py — see
// docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md. Beginner-tier
// Reading/Listening exercises show no countdown timer; standard/advanced do.
const BEGINNER_PHASES = new Set(['foundation', 'core_skills']);

export function isBeginnerPhase(phase: string | null): boolean {
  return phase !== null && BEGINNER_PHASES.has(phase);
}
