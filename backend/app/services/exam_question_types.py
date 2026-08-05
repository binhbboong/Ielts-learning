"""Shared grading logic for Reading/Listening questions across the full IELTS
question-type catalog. Reading and Listening questions are duck-typed here
(anything with .question_type, .correct_option_index, .accepted_answers) —
see docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
"""

from app.ai.schemas import TEXT_BASED_QUESTION_TYPES


def is_text_based(question_type: str) -> bool:
    return question_type in TEXT_BASED_QUESTION_TYPES


def normalize_answer_text(value: str) -> str:
    """Case-insensitive, whitespace-normalized comparison key for free-text
    answers — no AI call needed at scoring time (FR-14/FR-18 of
    reading-practice/listening-practice revision 2)."""
    return " ".join(value.strip().lower().split())


def is_correct(question, answer: int | str | None) -> bool:
    if is_text_based(question.question_type):
        if not isinstance(answer, str) or not answer.strip():
            return False
        normalized = normalize_answer_text(answer)
        return any(
            normalized == normalize_answer_text(accepted)
            for accepted in (question.accepted_answers or [])
        )
    return isinstance(answer, int) and question.correct_option_index == answer


def canonical_correct_answer(question) -> int | str | None:
    """A single representative correct answer for display: the option index
    for option-based types, or the first accepted answer for text-based
    types."""
    if is_text_based(question.question_type):
        accepted = question.accepted_answers or []
        return accepted[0] if accepted else None
    return question.correct_option_index
