from app.ai.schemas import CriterionFeedback, SpeakingEvaluationResult
from app.ai.testing import FakeAIProvider
from app.data.speaking_questions_seed import seed_questions
from app.services.speech_to_text import (
    FakeSpeechToText,
    TranscriptionResult,
)
from app.services.speaking_coach import (
    create_submission,
    run_evaluation,
    run_transcription,
)


def _speaking_success():
    criterion = CriterionFeedback(
        band_score=7,
        feedback="Specific transcript-based feedback.",
        strengths=["Clear response"],
        weaknesses=["Use more linking phrases"],
    )
    return SpeakingEvaluationResult(
        status="ok",
        fluency_and_coherence=criterion,
        lexical_resource=criterion,
        grammatical_range_and_accuracy=criterion,
    )


def test_step_tracked_happy_path(db_session):
    seed_questions(db_session)
    question = db_session.query(__import__(
        "app.models.speaking_question", fromlist=["SpeakingQuestion"]
    ).SpeakingQuestion).first()
    submission = create_submission(db_session, question.id, "audio/demo.webm", 30)
    assert submission.status == "PROCESSING"
    assert submission.transcript is None

    stt = FakeSpeechToText(TranscriptionResult(status="ok", transcript="My answer."))
    run_transcription(db_session, submission.id, stt)
    assert submission.transcript == "My answer."
    assert submission.status == "PROCESSING"

    run_evaluation(
        db_session,
        submission.id,
        FakeAIProvider(speaking_result=_speaking_success()),
    )
    assert submission.status == "COMPLETED"
    assert submission.fluency_and_coherence["band_score"] == 7


def test_failures_are_distinct_and_retryable(db_session):
    seed_questions(db_session)
    question = db_session.query(__import__(
        "app.models.speaking_question", fromlist=["SpeakingQuestion"]
    ).SpeakingQuestion).first()
    submission = create_submission(db_session, question.id, "audio/demo.webm", 30)
    failed_stt = FakeSpeechToText(
        TranscriptionResult(status="error", error_message="not clear")
    )
    run_transcription(db_session, submission.id, failed_stt)
    assert submission.status == "TRANSCRIPTION_FAILED"

    failed_stt.result = TranscriptionResult(status="ok", transcript="Recovered.")
    run_transcription(db_session, submission.id, failed_stt)
    failed_ai = FakeAIProvider(
        speaking_result=SpeakingEvaluationResult(
            status="error", error_message="provider unavailable"
        )
    )
    run_evaluation(db_session, submission.id, failed_ai)
    assert submission.status == "EVALUATION_FAILED"
    assert submission.transcript == "Recovered."
