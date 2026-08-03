from datetime import date

from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.models.speaking_submission import SpeakingSubmission
from app.models.writing_submission import WritingSubmission


def test_writing_submission_accepts_an_optional_day(db_session_factory):
    session = db_session_factory()
    submission = WritingSubmission(
        question_text="Prompt",
        task_type="task2",
        response_text="Essay",
        status="complete",
        day=date(2026, 7, 30),
    )
    session.add(submission)
    session.commit()
    submission_id = submission.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(WritingSubmission).filter_by(id=submission_id).one()
    assert reloaded.day == date(2026, 7, 30)
    fresh.close()


def test_speaking_submission_allows_a_null_question_id_with_a_prompt_text_instead(
    db_session_factory,
):
    session = db_session_factory()
    submission = SpeakingSubmission(
        question_id=None,
        prompt_text="Describe a memorable trip.",
        audio_storage_ref="ref",
        audio_duration_seconds=10,
        status="PROCESSING",
        day=date(2026, 7, 30),
    )
    session.add(submission)
    session.commit()
    submission_id = submission.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(SpeakingSubmission).filter_by(id=submission_id).one()
    assert reloaded.question_id is None
    assert reloaded.prompt_text == "Describe a memorable trip."
    assert reloaded.day == date(2026, 7, 30)
    fresh.close()
