from datetime import date

from app.ai.schemas import (
    CriterionFeedback,
    SentenceCorrection,
    WritingEvaluationResult,
)
from app.ai.testing import FakeAIProvider
from app.models.daily_lesson_plan import DailyFocus
from app.schemas.writing_submission import WritingSubmissionCreate
from app.services.writing_coach import create_and_evaluate, get_submission_list


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


def test_create_and_evaluate_passes_the_days_focus_level_to_the_provider(
    db_session_factory,
):
    session = db_session_factory()
    try:
        session.add(
            DailyFocus(
                day=date(2026, 7, 30), skill="writing", focus_kind="default",
                target_band=4.5, phase="foundation",
            )
        )
        session.commit()
        payload = WritingSubmissionCreate(
            response_text="Essay", task_type="task2", question_text="Prompt",
            day=date(2026, 7, 30),
        )
        provider = _provider()

        create_and_evaluate(session, payload, provider)

        assert provider.writing_requests[0].target_band == 4.5
        assert provider.writing_requests[0].phase == "foundation"
    finally:
        session.close()


def test_create_and_evaluate_has_no_level_context_without_a_matching_focus(
    db_session_factory,
):
    session = db_session_factory()
    try:
        payload = WritingSubmissionCreate(
            response_text="Essay", task_type="task2", question_text="Prompt",
            day=date(2026, 7, 30),
        )
        provider = _provider()

        create_and_evaluate(session, payload, provider)

        assert provider.writing_requests[0].target_band is None
        assert provider.writing_requests[0].phase is None
    finally:
        session.close()


def test_create_and_evaluate_allows_a_second_submission_for_the_same_day(
    db_session_factory,
):
    session = db_session_factory()
    try:
        payload = WritingSubmissionCreate(
            response_text="First attempt", task_type="task2", question_text="Prompt",
            day=date(2026, 7, 30),
        )
        first = create_and_evaluate(session, payload, _provider())
        second = create_and_evaluate(
            session,
            WritingSubmissionCreate(
                response_text="Second attempt", task_type="task2",
                question_text="Prompt", day=date(2026, 7, 30),
            ),
            _provider(),
        )

        assert first.id != second.id
        assert get_submission_list(session, day=date(2026, 7, 30)) == [second, first]
    finally:
        session.close()


def test_get_submission_list_filters_by_day_when_given(db_session_factory):
    session = db_session_factory()
    try:
        create_and_evaluate(
            session,
            WritingSubmissionCreate(
                response_text="Essay A", task_type="task2", question_text="Prompt",
                day=date(2026, 7, 30),
            ),
            _provider(),
        )
        create_and_evaluate(
            session,
            WritingSubmissionCreate(
                response_text="Essay B", task_type="task2", question_text="Prompt",
                day=date(2026, 7, 31),
            ),
            _provider(),
        )

        only_30th = get_submission_list(session, day=date(2026, 7, 30))

        assert len(only_30th) == 1
        assert only_30th[0].response_text == "Essay A"
    finally:
        session.close()


def test_get_submission_list_returns_everything_when_no_day_given(
    db_session_factory,
):
    session = db_session_factory()
    try:
        create_and_evaluate(
            session,
            WritingSubmissionCreate(
                response_text="Essay A", task_type="task2", question_text="Prompt",
                day=date(2026, 7, 30),
            ),
            _provider(),
        )
        create_and_evaluate(
            session,
            WritingSubmissionCreate(
                response_text="Essay B", task_type="task2", question_text="Prompt",
            ),
            _provider(),
        )

        assert len(get_submission_list(session)) == 2
    finally:
        session.close()
