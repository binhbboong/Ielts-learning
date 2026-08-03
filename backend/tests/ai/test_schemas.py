import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    ChatRequest,
    ChatResult,
    CriterionFeedback,
    GeneratedQuestion,
    ListeningScriptGenerationRequest,
    ListeningScriptGenerationResult,
    QuizGenerationRequest,
    QuizGenerationResult,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
    SentenceCorrection,
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
    WritingEvaluationRequest,
    WritingEvaluationResult,
    level_context_line,
)


def _criterion(score: float = 7.0) -> CriterionFeedback:
    return CriterionFeedback(
        band_score=score,
        feedback="Specific feedback",
        strengths=["Clear position"],
        weaknesses=["Develop examples further"],
    )


def test_writing_request_requires_task_type_question_and_response():
    request = WritingEvaluationRequest(
        response_text="A complete essay",
        task_type="task2",
        question_text="Discuss both views.",
    )

    assert request.task_type == "task2"
    assert request.target_band is None
    assert request.phase is None
    with pytest.raises(ValidationError):
        WritingEvaluationRequest(
            response_text=" ",
            task_type="task2",
            question_text="Question",
        )


def test_writing_and_speaking_requests_accept_optional_level_context():
    writing = WritingEvaluationRequest(
        response_text="A complete essay",
        task_type="task2",
        question_text="Discuss both views.",
        target_band=4.5,
        phase="foundation",
    )
    speaking = SpeakingEvaluationRequest(
        transcript="I would like to describe...",
        question_text="Describe a memorable journey.",
        target_band=6.5,
        phase="exam_readiness",
    )

    assert writing.target_band == 4.5
    assert writing.phase == "foundation"
    assert speaking.target_band == 6.5
    assert speaking.phase == "exam_readiness"


def test_level_context_line_empty_when_no_level_known():
    assert level_context_line(None, None) == ""
    assert level_context_line(4.5, None) == ""
    assert level_context_line(None, "foundation") == ""


def test_level_context_line_includes_band_and_readable_phase_when_known():
    line = level_context_line(4.5, "foundation")

    assert "4.5" in line
    assert "foundation phase" in line
    assert "not a flat band-9 standard" in line


def test_writing_result_discriminates_complete_success_from_error():
    success = WritingEvaluationResult(
        status="ok",
        task_response=_criterion(7.0),
        coherence_and_cohesion=_criterion(6.5),
        lexical_resource=_criterion(7.5),
        grammatical_range_and_accuracy=_criterion(6.0),
        overall_band=7.0,
        corrections=[
            SentenceCorrection(
                original="People is affected.",
                corrected="People are affected.",
                explanation="Subject-verb agreement.",
            )
        ],
    )
    failure = WritingEvaluationResult(
        status="error", error_message="provider timeout"
    )

    assert success.task_response.band_score == 7.0
    assert failure.task_response is None
    with pytest.raises(ValidationError):
        WritingEvaluationResult(status="ok")
    with pytest.raises(ValidationError):
        WritingEvaluationResult(status="error")


def test_stub_request_result_pairs_are_typed_and_status_discriminated():
    speaking_request = SpeakingEvaluationRequest(
        transcript="I would like to describe...",
        question_text="Describe a memorable journey.",
    )
    speaking_result = SpeakingEvaluationResult(
        status="error", error_message="not available"
    )
    quiz_request = QuizGenerationRequest(topic="Environment", question_count=3)
    quiz_result = QuizGenerationResult(status="ok", questions=["Question 1"])
    chat_request = ChatRequest(message="How can I improve cohesion?")
    chat_result = ChatResult(status="ok", message="Use explicit transitions.")

    assert speaking_request.transcript.startswith("I would")
    assert speaking_result.status == "error"
    assert quiz_request.question_count == 3
    assert quiz_result.questions == ["Question 1"]
    assert chat_request.message.endswith("?")
    assert chat_result.message.startswith("Use")


def _question(correct_index: int = 2) -> GeneratedQuestion:
    return GeneratedQuestion(
        question_text="According to the passage, what caused the delay?",
        options=["Weather", "Funding", "Staffing", "Regulation"],
        correct_option_index=correct_index,
    )


def test_reading_exercise_request_requires_focus_description():
    request = ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")

    assert request.focus_description == "the word 'nevertheless'"
    with pytest.raises(ValidationError):
        ReadingExerciseGenerationRequest(focus_description=" ")


def test_reading_exercise_result_discriminates_success_from_error():
    success = ReadingExerciseGenerationResult(
        status="ok",
        passage_text="A short passage.",
        questions=[_question()],
    )
    failure = ReadingExerciseGenerationResult(status="error", error_message="provider timeout")

    assert success.passage_text == "A short passage."
    assert success.questions[0].correct_option_index == 2
    assert failure.passage_text is None
    with pytest.raises(ValidationError):
        ReadingExerciseGenerationResult(status="ok")
    with pytest.raises(ValidationError):
        ReadingExerciseGenerationResult(status="error")


def test_listening_script_request_requires_focus_description():
    request = ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")

    assert request.focus_description == "the word 'nevertheless'"
    with pytest.raises(ValidationError):
        ListeningScriptGenerationRequest(focus_description=" ")


def test_listening_script_result_discriminates_success_from_error():
    success = ListeningScriptGenerationResult(
        status="ok",
        script_text="A short script.",
        questions=[_question()],
    )
    failure = ListeningScriptGenerationResult(status="error", error_message="provider timeout")

    assert success.script_text == "A short script."
    assert failure.script_text is None
    with pytest.raises(ValidationError):
        ListeningScriptGenerationResult(status="ok")
    with pytest.raises(ValidationError):
        ListeningScriptGenerationResult(status="error")
