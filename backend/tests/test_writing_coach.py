import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    CriterionFeedback,
    SentenceCorrection,
    WritingEvaluationResult,
)
from app.ai.testing import FakeAIProvider
from app.schemas.writing_submission import WritingSubmissionCreate
from app.services.writing_coach import (
    create_and_evaluate,
    get_submission_detail,
    get_submission_list,
)


def _criterion(text: str) -> CriterionFeedback:
    return CriterionFeedback(
        band_score=7,
        feedback=f"Specific feedback about {text}",
        strengths=[text],
        weaknesses=["Needs clearer support"],
    )


def _success() -> WritingEvaluationResult:
    return WritingEvaluationResult(
        status="ok",
        task_response=_criterion("the opening sentence"),
        coherence_and_cohesion=_criterion("the second paragraph"),
        lexical_resource=_criterion("the phrase public transport"),
        grammatical_range_and_accuracy=_criterion("the final sentence"),
        overall_band=7,
        corrections=[
            SentenceCorrection(
                original="People is affected.",
                corrected="People are affected.",
                explanation="Use a plural verb.",
            )
        ],
    )


def test_create_schema_rejects_blank_required_text():
    with pytest.raises(ValidationError):
        WritingSubmissionCreate(
            task_type="task2", question_text="Prompt", response_text="  "
        )


def test_successful_evaluation_persists_full_feedback_and_log(db_session):
    provider = FakeAIProvider(writing_result=_success())
    payload = WritingSubmissionCreate(
        task_type="task2",
        question_text="Should cities invest in public transport?",
        response_text="People is affected by traffic.",
    )

    created = create_and_evaluate(db_session, payload, provider)
    assert created.status == "complete"
    assert created.task_response["band_score"] == 7
    assert len(provider.writing_requests) == 1
    assert len(get_submission_list(db_session)) == 1
    assert get_submission_detail(db_session, created.id).response_text == payload.response_text


def test_provider_failure_preserves_original_submission(db_session):
    provider = FakeAIProvider(
        writing_result=WritingEvaluationResult(
            status="error", error_message="provider unavailable"
        )
    )
    payload = WritingSubmissionCreate(
        task_type="task1",
        question_text="Describe the chart.",
        response_text="The chart shows a rise.",
    )
    created = create_and_evaluate(db_session, payload, provider)
    assert created.status == "failed"
    assert created.response_text == payload.response_text
    assert created.question_text == payload.question_text


def test_success_without_corrections_is_treated_as_failure(db_session):
    result = _success().model_copy(update={"corrections": []})
    created = create_and_evaluate(
        db_session,
        WritingSubmissionCreate(
            task_type="task2",
            question_text="Discuss both views.",
            response_text="This is my response.",
        ),
        FakeAIProvider(writing_result=result),
    )
    assert created.status == "failed"
