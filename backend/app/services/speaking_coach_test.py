from datetime import date

from app.ai.schemas import CriterionFeedback, SpeakingEvaluationResult
from app.ai.testing import FakeAIProvider
from app.models.daily_lesson_plan import DailyFocus
from app.services.speaking_coach import create_submission, run_evaluation


def _speaking_provider() -> FakeAIProvider:
    criterion = CriterionFeedback(
        band_score=6.5, feedback="Specific", strengths=["Clear"], weaknesses=["Expand"]
    )
    return FakeAIProvider(
        speaking_result=SpeakingEvaluationResult(
            status="ok",
            fluency_and_coherence=criterion,
            lexical_resource=criterion,
            grammatical_range_and_accuracy=criterion,
        )
    )


def test_create_submission_accepts_a_prompt_text_instead_of_a_question_id(
    db_session_factory,
):
    session = db_session_factory()
    try:
        submission = create_submission(
            session,
            question_id=None,
            audio_storage_ref="ref",
            duration_seconds=10,
            prompt_text="Describe a memorable trip.",
            day=date(2026, 7, 30),
        )

        assert submission.question_id is None
        assert submission.prompt_text == "Describe a memorable trip."
        assert submission.day == date(2026, 7, 30)
    finally:
        session.close()


def test_run_evaluation_uses_prompt_text_when_question_id_is_none(db_session_factory):
    session = db_session_factory()
    try:
        submission = create_submission(
            session,
            question_id=None,
            audio_storage_ref="ref",
            duration_seconds=10,
            prompt_text="Describe a memorable trip.",
        )
        submission.transcript = "I once went on a trip."
        session.commit()

        criterion = CriterionFeedback(
            band_score=6.5, feedback="Specific", strengths=["Clear"], weaknesses=["Expand"]
        )
        provider = FakeAIProvider(
            speaking_result=SpeakingEvaluationResult(
                status="ok",
                fluency_and_coherence=criterion,
                lexical_resource=criterion,
                grammatical_range_and_accuracy=criterion,
            )
        )

        result = run_evaluation(session, submission.id, provider)

        assert result.status == "COMPLETED"
        assert provider.speaking_requests[0].question_text == "Describe a memorable trip."
    finally:
        session.close()


def test_run_evaluation_passes_the_days_focus_level_to_the_provider(db_session_factory):
    session = db_session_factory()
    try:
        session.add(
            DailyFocus(
                day=date(2026, 7, 30), skill="speaking", focus_kind="default",
                target_band=4.5, phase="foundation",
            )
        )
        submission = create_submission(
            session,
            question_id=None,
            audio_storage_ref="ref",
            duration_seconds=10,
            prompt_text="Tell me about your hometown.",
            day=date(2026, 7, 30),
        )
        submission.transcript = "My hometown is..."
        session.commit()
        provider = _speaking_provider()

        run_evaluation(session, submission.id, provider)

        assert provider.speaking_requests[0].target_band == 4.5
        assert provider.speaking_requests[0].phase == "foundation"
    finally:
        session.close()


def test_run_evaluation_has_no_level_context_without_a_matching_focus(db_session_factory):
    session = db_session_factory()
    try:
        submission = create_submission(
            session,
            question_id=None,
            audio_storage_ref="ref",
            duration_seconds=10,
            prompt_text="Tell me about your hometown.",
        )
        submission.transcript = "My hometown is..."
        session.commit()
        provider = _speaking_provider()

        run_evaluation(session, submission.id, provider)

        assert provider.speaking_requests[0].target_band is None
        assert provider.speaking_requests[0].phase is None
    finally:
        session.close()
