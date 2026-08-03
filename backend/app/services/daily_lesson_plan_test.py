from datetime import date, datetime, timezone

from app.ai.schemas import ChatResult
from app.ai.testing import FakeAIProvider
from app.models.daily_lesson_plan import DailyFocus
from app.models.listening_practice import ListeningExercise, ListeningSubmission
from app.models.mistake import Mistake
from app.models.reading_practice import ReadingExercise, ReadingSubmission
from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.models.speaking_submission import SpeakingSubmission
from app.models.vocabulary import VocabularyWord
from app.models.writing_submission import WritingSubmission
from app.ai.schemas import (
    GeneratedQuestion,
    ListeningScriptGenerationResult,
    ReadingExerciseGenerationResult,
)
from app.services.daily_lesson_plan import (
    ensure_today_generated,
    generate_prompt_text,
    get_or_create_focus,
    get_overview,
    get_skill_status,
    retry_skill,
)
from app.services.text_to_speech import FakeTextToSpeech, SynthesisResult


def test_selects_a_recent_mistake_for_the_skill_when_one_exists(db_session_factory):
    session = db_session_factory()
    session.add(
        Mistake(
            skill="reading",
            source="Cambridge 17",
            explanation="missed a paraphrase of 'nevertheless'",
            reason_category="missed_paraphrase",
            logged_at=datetime.now(timezone.utc),
        )
    )
    session.commit()

    focus = get_or_create_focus(session, date(2026, 7, 30), "reading")

    assert focus.focus_kind == "mistake"
    assert "nevertheless" in focus.focus_reference
    session.close()


def test_falls_back_to_due_vocabulary_when_no_mistake_exists_for_the_skill(
    db_session_factory,
):
    session = db_session_factory()
    session.add(
        VocabularyWord(
            word="nevertheless",
            meaning="in spite of that",
            next_due_date=date(2026, 7, 29),
        )
    )
    session.commit()

    focus = get_or_create_focus(session, date(2026, 7, 30), "reading")

    assert focus.focus_kind == "vocabulary"
    assert "nevertheless" in focus.focus_reference
    session.close()


def test_falls_back_to_default_when_no_mistake_or_vocabulary_exists(db_session_factory):
    session = db_session_factory()

    focus = get_or_create_focus(session, date(2026, 7, 30), "reading")

    assert focus.focus_kind == "default"
    session.close()


def test_second_call_same_day_and_skill_returns_identical_row(db_session_factory):
    session = db_session_factory()

    first = get_or_create_focus(session, date(2026, 7, 30), "reading")
    second = get_or_create_focus(session, date(2026, 7, 30), "reading")

    assert first.id == second.id
    assert session.query(DailyFocus).count() == 1
    session.close()


def test_deleting_the_source_mistake_does_not_change_an_already_generated_focus(
    db_session_factory,
):
    session = db_session_factory()
    mistake = Mistake(
        skill="reading",
        source="Cambridge 17",
        explanation="missed a paraphrase of 'nevertheless'",
        reason_category="missed_paraphrase",
        logged_at=datetime.now(timezone.utc),
    )
    session.add(mistake)
    session.commit()

    focus = get_or_create_focus(session, date(2026, 7, 30), "reading")
    original_reference = focus.focus_reference

    session.delete(mistake)
    session.commit()

    reloaded = session.query(DailyFocus).filter_by(day=date(2026, 7, 30), skill="reading").one()
    assert reloaded.focus_reference == original_reference
    session.close()


def test_generate_prompt_text_calls_chat_with_an_instruction_referencing_the_focus(
    db_session_factory,
):
    session = db_session_factory()
    focus = get_or_create_focus(session, date(2026, 7, 30), "writing")
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="Some people believe...")
    )

    result = generate_prompt_text(provider, focus)

    assert result.status == "ok"
    assert result.message == "Some people believe..."
    assert len(provider.chat_requests) == 1
    assert "writing" in provider.chat_requests[0].message.lower()
    session.close()


def test_generate_prompt_text_propagates_chat_failure(db_session_factory):
    session = db_session_factory()
    focus = get_or_create_focus(session, date(2026, 7, 30), "speaking")
    provider = FakeAIProvider(
        chat_result=ChatResult(status="error", error_message="provider timeout")
    )

    result = generate_prompt_text(provider, focus)

    assert result.status == "error"
    session.close()


def test_reading_status_generating_when_no_exercise_exists_yet(db_session_factory):
    session = db_session_factory()
    try:
        assert get_skill_status(session, date(2026, 7, 30), "reading") == "generating"
    finally:
        session.close()


def test_reading_status_ready_then_done_after_submission(db_session_factory):
    session = db_session_factory()
    try:
        exercise = ReadingExercise(
            day=date(2026, 7, 30), passage_text="Passage.", focus_reference=None,
            status="ready",
        )
        session.add(exercise)
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "reading") == "ready"

        session.add(
            ReadingSubmission(exercise_id=exercise.id, answers=[0], score=1)
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "reading") == "done"
    finally:
        session.close()


def test_reading_status_failed(db_session_factory):
    session = db_session_factory()
    try:
        session.add(
            ReadingExercise(
                day=date(2026, 7, 30), passage_text="", focus_reference=None,
                status="failed",
            )
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "reading") == "failed"
    finally:
        session.close()


def test_listening_status_generating_while_mid_pipeline(db_session_factory):
    session = db_session_factory()
    try:
        session.add(
            ListeningExercise(
                day=date(2026, 7, 30), script_text="", audio_bytes=None,
                audio_content_type=None, focus_reference=None,
                status="script_generating",
            )
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "generating"
    finally:
        session.close()


def test_listening_status_ready_then_done_after_submission(db_session_factory):
    session = db_session_factory()
    try:
        exercise = ListeningExercise(
            day=date(2026, 7, 30), script_text="Script.", audio_bytes=b"a",
            audio_content_type="audio/mpeg", focus_reference=None, status="ready",
        )
        session.add(exercise)
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "ready"

        session.add(
            ListeningSubmission(exercise_id=exercise.id, answers=[0], score=1)
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "done"
    finally:
        session.close()


def test_listening_status_failed_for_either_failure_state(db_session_factory):
    session = db_session_factory()
    try:
        session.add(
            ListeningExercise(
                day=date(2026, 7, 30), script_text="Script.", audio_bytes=None,
                audio_content_type=None, focus_reference=None, status="audio_failed",
            )
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "failed"
    finally:
        session.close()


def test_writing_status_failed_when_focus_exists_with_no_generated_prompt(
    db_session_factory,
):
    session = db_session_factory()
    try:
        get_or_create_focus(session, date(2026, 7, 30), "writing")
        assert get_skill_status(session, date(2026, 7, 30), "writing") == "failed"
    finally:
        session.close()


def test_writing_status_ready_then_done_after_submission(db_session_factory):
    session = db_session_factory()
    try:
        focus = get_or_create_focus(session, date(2026, 7, 30), "writing")
        focus.generated_prompt_text = "Some people believe..."
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "writing") == "ready"

        session.add(
            WritingSubmission(
                question_text="Some people believe...", task_type="task2",
                response_text="Essay", status="complete", day=date(2026, 7, 30),
            )
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "writing") == "done"
    finally:
        session.close()


def test_speaking_status_ready_then_done_after_submission(db_session_factory):
    session = db_session_factory()
    try:
        focus = get_or_create_focus(session, date(2026, 7, 30), "speaking")
        focus.generated_prompt_text = "Describe a memorable trip."
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "speaking") == "ready"

        session.add(
            SpeakingSubmission(
                question_id=None, prompt_text="Describe a memorable trip.",
                day=date(2026, 7, 30), audio_storage_ref="ref",
                audio_duration_seconds=10, status="PROCESSING",
            )
        )
        session.commit()
        assert get_skill_status(session, date(2026, 7, 30), "speaking") == "done"
    finally:
        session.close()


def _full_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="ok", passage_text="A passage.",
            questions=[GeneratedQuestion(
                question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
            )],
        ),
        listening_script_result=ListeningScriptGenerationResult(
            status="ok", script_text="A script.",
            questions=[GeneratedQuestion(
                question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
            )],
        ),
        chat_result=ChatResult(status="ok", message="A generated prompt."),
    )


def test_ensure_today_generated_creates_two_allocated_skills_on_first_call(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        ensure_today_generated(session, date(2026, 7, 30), provider, tts)

        assert get_skill_status(session, date(2026, 7, 30), "listening") == "ready"
        assert get_skill_status(session, date(2026, 7, 30), "speaking") == "ready"
        focuses = session.query(DailyFocus).filter_by(day=date(2026, 7, 30)).all()
        assert {focus.skill for focus in focuses} == {"listening", "speaking"}
        assert sum(focus.estimated_minutes for focus in focuses) == 50
    finally:
        session.close()


def test_ensure_today_generated_is_idempotent_and_triggers_no_further_generation(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        ensure_today_generated(session, date(2026, 7, 30), provider, tts)
        ensure_today_generated(session, date(2026, 7, 30), provider, tts)

        assert len(provider.reading_exercise_requests) == 0
        assert len(provider.listening_script_requests) == 1
        assert len(provider.chat_requests) == 1
    finally:
        session.close()


def test_get_overview_includes_allocated_skills_for_today(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        entries = get_overview(session, date(2026, 7, 30), provider, tts)

        skills_seen = {entry.skill for entry in entries}
        assert skills_seen == {"listening", "speaking"}
        assert all(entry.day == date(2026, 7, 30) for entry in entries)
    finally:
        session.close()


def test_get_overview_carries_over_an_earlier_incomplete_skill(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        # Generate an earlier day, but never submit anything for it.
        get_overview(session, date(2026, 7, 29), provider, tts)

        entries = get_overview(session, date(2026, 7, 30), provider, tts)

        carried_over = [e for e in entries if e.day == date(2026, 7, 29)]
        assert len(carried_over) == 2
        today_entries = [e for e in entries if e.day == date(2026, 7, 30)]
        assert len(today_entries) == 2
    finally:
        session.close()


def test_get_overview_does_not_carry_over_a_completed_earlier_skill(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        get_overview(session, date(2026, 7, 29), provider, tts)
        exercise = session.query(ReadingExercise).filter_by(day=date(2026, 7, 29)).one()
        session.add(ReadingSubmission(exercise_id=exercise.id, answers=[0], score=1))
        session.commit()

        entries = get_overview(session, date(2026, 7, 30), provider, tts)

        carried_over_reading = [
            e for e in entries if e.day == date(2026, 7, 29) and e.skill == "reading"
        ]
        assert carried_over_reading == []
    finally:
        session.close()


def _failing_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="error", error_message="x"
        ),
        listening_script_result=ListeningScriptGenerationResult(
            status="error", error_message="x"
        ),
        chat_result=ChatResult(status="error", error_message="x"),
    )


def test_retry_skill_recovers_a_failed_reading_exercise(db_session_factory):
    session = db_session_factory()
    try:
        failing_tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"a", content_type="audio/mpeg")
        )
        target_day = date(2026, 7, 27)
        ensure_today_generated(session, target_day, _failing_provider(), failing_tts)
        assert get_skill_status(session, target_day, "reading") == "failed"

        retry_skill(session, target_day, "reading", _full_provider(), failing_tts)

        assert get_skill_status(session, target_day, "reading") == "ready"
    finally:
        session.close()


def test_retry_skill_recovers_a_failed_writing_prompt(db_session_factory):
    session = db_session_factory()
    try:
        failing_tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"a", content_type="audio/mpeg")
        )
        target_day = date(2026, 7, 29)
        ensure_today_generated(session, target_day, _failing_provider(), failing_tts)
        assert get_skill_status(session, target_day, "writing") == "failed"

        retry_skill(session, target_day, "writing", _full_provider(), failing_tts)

        assert get_skill_status(session, target_day, "writing") == "ready"
    finally:
        session.close()


def test_retry_skill_on_listening_only_retries_the_failed_step(db_session_factory):
    session = db_session_factory()
    try:
        succeeding_script_failing_audio = FakeAIProvider(
            listening_script_result=ListeningScriptGenerationResult(
                status="ok", script_text="A script.",
                questions=[GeneratedQuestion(
                    question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
                )],
            ),
        )
        failing_tts = FakeTextToSpeech(
            SynthesisResult(status="error", error_message="tts down")
        )
        # Only run listening generation directly (avoid requiring reading/writing/speaking fakes).
        focus = get_or_create_focus(session, date(2026, 7, 30), "listening")
        from app.services import listening_practice
        listening_practice.get_or_create_exercise(
            session, date(2026, 7, 30), focus.focus_reference,
            succeeding_script_failing_audio, failing_tts,
        )
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "failed"

        succeeding_tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"a", content_type="audio/mpeg")
        )
        retry_skill(
            session, date(2026, 7, 30), "listening",
            succeeding_script_failing_audio, succeeding_tts,
        )

        assert get_skill_status(session, date(2026, 7, 30), "listening") == "ready"
        # The script provider must not have been called a second time.
        assert len(succeeding_script_failing_audio.listening_script_requests) == 1
    finally:
        session.close()
