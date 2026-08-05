from dataclasses import dataclass

from app.services.exam_question_types import (
    canonical_correct_answer,
    is_correct,
    normalize_answer_text,
)


@dataclass
class _Question:
    question_type: str
    correct_option_index: int | None = None
    accepted_answers: list[str] | None = None


def test_option_based_question_is_correct_only_on_exact_index_match():
    question = _Question(question_type="multiple_choice", correct_option_index=1)

    assert is_correct(question, 1) is True
    assert is_correct(question, 0) is False


def test_true_false_not_given_is_graded_as_option_based():
    question = _Question(question_type="true_false_not_given", correct_option_index=2)

    assert is_correct(question, 2) is True
    assert is_correct(question, 0) is False


def test_text_based_question_matches_case_and_whitespace_insensitively():
    question = _Question(
        question_type="note_completion", accepted_answers=["funding", "budget"]
    )

    assert is_correct(question, "  Funding  ") is True
    assert is_correct(question, "BUDGET") is True
    assert is_correct(question, "staffing") is False


def test_text_based_question_rejects_a_non_string_answer():
    question = _Question(question_type="note_completion", accepted_answers=["funding"])

    assert is_correct(question, 0) is False
    assert is_correct(question, None) is False


def test_option_based_question_rejects_a_string_answer():
    question = _Question(question_type="multiple_choice", correct_option_index=0)

    assert is_correct(question, "0") is False


def test_normalize_answer_text_collapses_internal_whitespace():
    assert normalize_answer_text("  a   bicycle  ") == "a bicycle"


def test_canonical_correct_answer_returns_index_for_option_based():
    question = _Question(question_type="multiple_choice", correct_option_index=3)

    assert canonical_correct_answer(question) == 3


def test_canonical_correct_answer_returns_first_accepted_for_text_based():
    question = _Question(
        question_type="note_completion", accepted_answers=["funding", "budget"]
    )

    assert canonical_correct_answer(question) == "funding"
