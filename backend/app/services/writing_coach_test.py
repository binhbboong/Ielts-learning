from datetime import date

from app.ai.schemas import (
    CriterionFeedback,
    SentenceCorrection,
    WritingEvaluationResult,
)
from app.ai.testing import FakeAIProvider
from app.schemas.writing_submission import WritingSubmissionCreate
from app.services.writing_coach import create_and_evaluate


def _criterion() -> CriterionFeedback:
    return CriterionFeedback(
        band_score=7, feedback="Specific feedback", strengths=["Clear"], weaknesses=["Expand"]
    )


def _provider() -> FakeAIProvider:
    criterion = _criterion()
    return FakeAIProvider(
        writing_result=WritingEvaluationResult(
            status="ok",
            task_response=criterion,
            coherence_and_cohesion=criterion,
            lexical_resource=criterion,
            grammatical_range_and_accuracy=criterion,
            overall_band=7,
            corrections=[
                SentenceCorrection(original="a", corrected="b", explanation="c")
            ],
        )
    )


def test_create_and_evaluate_persists_the_optional_day(db_session_factory):
    session = db_session_factory()
    try:
        payload = WritingSubmissionCreate(
            response_text="Essay", task_type="task2", question_text="Prompt",
            day=date(2026, 7, 30),
        )

        submission = create_and_evaluate(session, payload, _provider())

        assert submission.day == date(2026, 7, 30)
    finally:
        session.close()


def test_create_and_evaluate_defaults_day_to_none_for_ad_hoc_submissions(
    db_session_factory,
):
    session = db_session_factory()
    try:
        payload = WritingSubmissionCreate(
            response_text="Essay", task_type="task2", question_text="Prompt",
        )

        submission = create_and_evaluate(session, payload, _provider())

        assert submission.day is None
    finally:
        session.close()
