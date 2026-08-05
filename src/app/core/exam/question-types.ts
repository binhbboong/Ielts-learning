// Mirrors the IELTS question-type catalog in backend/app/ai/schemas.py — see
// docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md. Only a subset is
// actually generated at the beginner tier (multiple_choice/true_false_not_given
// for Reading, multiple_choice/note_completion for Listening); the rest is
// reserved for the standard/advanced-tier rollout stages.
const TEXT_BASED_QUESTION_TYPES = new Set([
  'sentence_completion',
  'summary_completion',
  'table_completion',
  'flow_chart_completion',
  'short_answer',
  'form_completion',
  'note_completion',
]);

export function isTextBasedQuestionType(questionType: string): boolean {
  return TEXT_BASED_QUESTION_TYPES.has(questionType);
}
