from datetime import date, datetime, timedelta, timezone

from app.ai.schemas import ChatResult
from app.ai.testing import FakeAIProvider
from app.models.daily_lesson_plan import DailyFocus
from app.models.listening_practice import ListeningExercise, ListeningSubmission
from app.models.mistake import Mistake
from app.models.reading_practice import ReadingExercise, ReadingSubmission
from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.models.speaking_submission import SpeakingSubmission
from app.models.user import LEGACY_USER_ID
from app.models.vocabulary import VocabularyQuiz, VocabularyWord
from app.models.writing_submission import WritingSubmission
from app.ai.schemas import (
    GeneratedPassage,
    GeneratedQuestion,
    GeneratedSection,
    ListeningScriptGenerationResult,
    ReadingExerciseGenerationResult,
)
from app.services.daily_lesson_plan import (
    ensure_today_generated,
    evaluate_checkpoint,
    generate_prompt_text,
    get_effective_day,
    get_or_create_focus,
    get_or_create_profile,
    get_overview,
    get_skill_status,
    pregenerate_for_all_learners,
    pregenerate_upcoming_days,
    retry_skill,
)
from app.services.text_to_speech import FakeTextToSpeech, SynthesisResult


def _pass_all_checkpoints(session, day, provider, tts) -> None:
    """Generate and fully pass all 3 daily skills + vocabulary quiz for `day`, so
    get_effective_day() advances past it. Speaking is no longer part of the daily
    rotation/checkpoint (docs/adr/2026-08-05-remove-speaking-from-daily-checkpoint.md)."""
    ensure_today_generated(session, day, provider, tts)
    reading_exercise = session.query(ReadingExercise).filter_by(day=day).one()
    session.add(ReadingSubmission(exercise_id=reading_exercise.id, answers=[0], score=1))
    listening_exercise = session.query(ListeningExercise).filter_by(day=day).one()
    session.add(
        ListeningSubmission(exercise_id=listening_exercise.id, answers=[0], score=1)
    )
    session.add(
        WritingSubmission(
            question_text="Some people believe...", task_type="task2",
            response_text="Essay", status="complete", day=day, overall_band=6.5,
        )
    )
    session.add(
        VocabularyQuiz(
            day=day, submitted_at=datetime.now(timezone.utc), correct=1, total=1
        )
    )
    session.commit()


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


def _focus_at_phase(
    skill: str, phase: str, target_band: float, day: date = date(2026, 7, 30)
) -> DailyFocus:
    return DailyFocus(
        day=day, skill=skill, focus_kind="default",
        target_band=target_band, phase=phase, estimated_minutes=20,
    )


def test_beginner_phase_gets_part_1_speaking_and_short_writing_prompts():
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )

    generate_prompt_text(provider, _focus_at_phase("speaking", "foundation", 4.5))
    generate_prompt_text(provider, _focus_at_phase("writing", "core_skills", 5.0))

    speaking_instruction = provider.chat_requests[0].message
    writing_instruction = provider.chat_requests[1].message
    assert "Part 1" in speaking_instruction
    assert "Part 2" not in speaking_instruction
    assert "100-150 words" in writing_instruction
    assert "Task 2" not in writing_instruction


def test_standard_phase_keeps_part_2_speaking_and_full_essay_writing_prompts():
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )

    generate_prompt_text(provider, _focus_at_phase("speaking", "development", 5.5))
    generate_prompt_text(provider, _focus_at_phase("writing", "consolidation", 6.0))

    assert "Part 2" in provider.chat_requests[0].message
    assert "Task 2" in provider.chat_requests[1].message
    assert "100-150 words" not in provider.chat_requests[1].message


def test_advanced_phase_gets_part_3_speaking_and_abstract_writing_prompts():
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )

    generate_prompt_text(provider, _focus_at_phase("speaking", "exam_readiness", 6.5))
    generate_prompt_text(provider, _focus_at_phase("writing", "peak_performance", 6.5))

    assert "Part 3" in provider.chat_requests[0].message
    assert "abstract or policy-oriented" in provider.chat_requests[1].message


def test_beginner_tier_writing_never_sets_a_task_type(db_session_factory):
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )
    focus = _focus_at_phase("writing", "foundation", 4.5)

    generate_prompt_text(provider, focus)

    assert focus.task_type is None


def test_standard_tier_writing_alternates_task_1_and_task_2_by_day(db_session_factory):
    provider = FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )
    task2_focus = _focus_at_phase(
        "writing", "consolidation", 6.0, day=date(2026, 7, 30)
    )
    task1_focus = _focus_at_phase(
        "writing", "consolidation", 6.0, day=date(2026, 7, 31)
    )

    generate_prompt_text(provider, task2_focus)
    generate_prompt_text(provider, task1_focus)

    assert task2_focus.task_type == "task2"
    assert task1_focus.task_type == "task1"
    assert "Task 2" in provider.chat_requests[0].message
    assert "no image-rendering capability" in provider.chat_requests[1].message
    assert "Task 2" not in provider.chat_requests[1].message


def test_reading_status_generating_when_no_exercise_exists_yet(db_session_factory):
    session = db_session_factory()
    try:
        assert get_skill_status(session, date(2026, 7, 30), "reading") == "generating"
    finally:
        session.close()


def test_reading_status_ready_then_done_after_submission(db_session_factory):
    session = db_session_factory()
    try:
        exercise = ReadingExercise(day=date(2026, 7, 30), focus_reference=None, status="ready")
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
            ReadingExercise(day=date(2026, 7, 30), focus_reference=None, status="failed")
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
                day=date(2026, 7, 30), focus_reference=None, status="script_generating",
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
            day=date(2026, 7, 30), focus_reference=None, status="ready",
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
                day=date(2026, 7, 30), focus_reference=None, status="audio_failed",
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
            status="ok",
            passages=[GeneratedPassage(
                passage_text="A passage.",
                questions=[GeneratedQuestion(
                    question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
                )],
            )],
        ),
        listening_script_result=ListeningScriptGenerationResult(
            status="ok",
            sections=[GeneratedSection(
                script_text="A script.",
                questions=[GeneratedQuestion(
                    question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
                )],
            )],
        ),
        chat_result=ChatResult(status="ok", message="A generated prompt."),
    )


def test_ensure_today_generated_creates_all_three_daily_skills_on_first_call(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        ensure_today_generated(session, date(2026, 7, 30), provider, tts)

        assert get_skill_status(session, date(2026, 7, 30), "reading") == "ready"
        assert get_skill_status(session, date(2026, 7, 30), "listening") == "ready"
        assert get_skill_status(session, date(2026, 7, 30), "writing") == "ready"
        focuses = session.query(DailyFocus).filter_by(day=date(2026, 7, 30)).all()
        assert {focus.skill for focus in focuses} == {"reading", "listening", "writing"}
        assert sum(focus.estimated_minutes for focus in focuses) == 40
        assert sum(1 for f in focuses if f.priority == "primary") == 1
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

        assert len(provider.reading_exercise_requests) == 1
        assert len(provider.listening_script_requests) == 1
        assert len(provider.chat_requests) == 1
    finally:
        session.close()


def test_ensure_today_generated_at_advanced_phase_requests_advanced_tier_and_skill_minutes(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        target_day = date(2026, 7, 30)
        # Week 18 (17 weeks after start) lands in the exam_readiness phase per
        # _PHASES — see plan_context().
        get_or_create_profile(session, LEGACY_USER_ID, target_day - timedelta(weeks=17))

        ensure_today_generated(session, target_day, provider, tts)

        assert provider.reading_exercise_requests[0].tier == "advanced"
        assert provider.listening_script_requests[0].tier == "advanced"
        focuses = {
            f.skill: f
            for f in session.query(DailyFocus).filter_by(day=target_day).all()
        }
        assert focuses["reading"].phase == "exam_readiness"
        advanced_primary_minutes = {"reading": 60, "listening": 40, "writing": 60}
        primary_skill = next(
            skill for skill, focus in focuses.items() if focus.priority == "primary"
        )
        assert focuses[primary_skill].estimated_minutes == (
            advanced_primary_minutes[primary_skill]
        )
        for skill, focus in focuses.items():
            if skill != primary_skill:
                assert focus.estimated_minutes == 25
    finally:
        session.close()


def test_get_overview_includes_all_three_daily_skills_for_the_effective_day(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        result = get_overview(session, date(2026, 7, 30), provider, tts)

        skills_seen = {entry.skill for entry in result.entries}
        assert skills_seen == {"reading", "listening", "writing"}
        assert all(entry.day == date(2026, 7, 30) for entry in result.entries)
        assert result.effective_day == date(2026, 7, 30)
        assert result.checkpoint.passed_count == 0
        assert result.checkpoint.all_passed is False
    finally:
        session.close()


def test_effective_day_does_not_advance_past_an_incomplete_checkpoint(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        # Day 29 generated but nothing submitted -> its checkpoint is incomplete.
        get_overview(session, date(2026, 7, 29), provider, tts)

        result = get_overview(session, date(2026, 7, 30), provider, tts)

        # Effective day stays pinned to the unfinished 29th — the 30th never generates.
        assert result.effective_day == date(2026, 7, 29)
        assert {e.day for e in result.entries} == {date(2026, 7, 29)}
        assert session.query(DailyFocus).filter_by(day=date(2026, 7, 30)).count() == 0
    finally:
        session.close()


def test_effective_day_advances_once_checkpoint_fully_passed(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        _pass_all_checkpoints(session, date(2026, 7, 29), provider, tts)

        assert get_effective_day(session, LEGACY_USER_ID, date(2026, 7, 30)) == date(
            2026, 7, 30
        )

        result = get_overview(session, date(2026, 7, 30), provider, tts)

        assert result.effective_day == date(2026, 7, 30)
        today_entries = [e for e in result.entries if e.day == date(2026, 7, 30)]
        assert {e.skill for e in today_entries} == {"reading", "listening", "writing"}
        # The now-fully-passed prior day's skills do not carry over into the view.
        assert all(e.day == date(2026, 7, 30) for e in result.entries)
    finally:
        session.close()


def test_evaluate_checkpoint_reports_per_skill_and_vocabulary_quiz_pass(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        _pass_all_checkpoints(session, date(2026, 7, 29), provider, tts)

        checkpoint = evaluate_checkpoint(session, date(2026, 7, 29))

        assert checkpoint.skills == {
            "reading": True, "listening": True, "writing": True,
        }
        assert checkpoint.vocabulary_quiz is True
        assert checkpoint.passed_count == 4
        assert checkpoint.all_passed is True
    finally:
        session.close()


def test_evaluate_checkpoint_fails_writing_below_the_days_phase_target_band(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        # Day 1 of a fresh profile is the "foundation" phase (plan_context ->
        # target_band 4.5, see _PHASES) — 4.0 is below that.
        _pass_all_checkpoints(session, date(2026, 7, 29), provider, tts)
        low_band_submission = (
            session.query(WritingSubmission).filter_by(day=date(2026, 7, 29)).one()
        )
        low_band_submission.overall_band = 4.0
        session.commit()

        checkpoint = evaluate_checkpoint(session, date(2026, 7, 29))

        assert checkpoint.skills["writing"] is False
        assert checkpoint.all_passed is False
    finally:
        session.close()


def test_evaluate_checkpoint_passes_writing_at_the_foundation_phase_target_band(
    db_session_factory,
):
    """Regression test: the checkpoint used to require profile.minimum_skill_band
    (a fixed 6.0 for every learner) regardless of phase, so a foundation-phase
    learner writing exactly at the ~4.5 band their content is intentionally
    scoped to (see _PROMPT_INSTRUCTION's beginner tier) could never pass the
    daily checkpoint and would be stuck on day 1 forever. It must now compare
    against that day's own phase-scaled target_band instead."""
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        _pass_all_checkpoints(session, date(2026, 7, 29), provider, tts)
        submission = (
            session.query(WritingSubmission).filter_by(day=date(2026, 7, 29)).one()
        )
        submission.overall_band = 4.5
        session.commit()

        checkpoint = evaluate_checkpoint(session, date(2026, 7, 29))

        assert checkpoint.skills["writing"] is True
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
                status="ok",
                sections=[GeneratedSection(
                    script_text="A script.",
                    questions=[GeneratedQuestion(
                        question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
                    )],
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


class _RaisingProvider(FakeAIProvider):
    def generate_reading_exercise(self, request):
        raise RuntimeError("simulated provider outage")


def test_pregenerate_upcoming_days_generates_effective_day_and_the_next(
    db_session_factory,
):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        today = date(2026, 7, 30)

        processed = pregenerate_upcoming_days(session, provider, tts, LEGACY_USER_ID, today)

        assert processed == [today, today + timedelta(days=1)]
        for day in processed:
            focuses = session.query(DailyFocus).filter_by(day=day).all()
            assert {f.skill for f in focuses} == {"reading", "listening", "writing"}
    finally:
        session.close()


def test_pregenerate_upcoming_days_skips_already_generated_content(db_session_factory):
    session = db_session_factory()
    try:
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        today = date(2026, 7, 30)

        pregenerate_upcoming_days(session, provider, tts, LEGACY_USER_ID, today)
        pregenerate_upcoming_days(session, provider, tts, LEGACY_USER_ID, today)

        # Each of the 2 days generates reading once, listening once, and writing's
        # chat-based prompt once; a second run must not trigger further generation.
        assert len(provider.reading_exercise_requests) == 2
        assert len(provider.listening_script_requests) == 2
        assert len(provider.chat_requests) == 2
    finally:
        session.close()


def test_pregenerate_for_all_learners_only_processes_existing_profiles(
    db_session_factory,
):
    session = db_session_factory()
    try:
        from app.models.user import User

        other_user_id = "00000000-0000-0000-0000-000000000099"
        session.add(
            User(
                id=other_user_id, email="other@example.com",
                display_name="Other", password_hash="unused",
            )
        )
        session.commit()
        today = date(2026, 7, 30)
        get_or_create_profile(session, LEGACY_USER_ID, today)
        provider = _full_provider()
        tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )

        result = pregenerate_for_all_learners(session, provider, tts, today)

        assert str(LEGACY_USER_ID) in result["processed"]
        assert str(other_user_id) not in result["processed"]
        assert result["errors"] == {}
        from app.models.study_profile import StudyProfile
        assert session.get(StudyProfile, other_user_id) is None
    finally:
        session.close()


def test_pregenerate_for_all_learners_continues_after_one_learner_fails(
    db_session_factory,
):
    session = db_session_factory()
    try:
        from app.models.user import User

        other_user_id = "00000000-0000-0000-0000-000000000098"
        session.add(
            User(
                id=other_user_id, email="second@example.com",
                display_name="Second", password_hash="unused",
            )
        )
        session.commit()
        today = date(2026, 7, 30)
        working_tts = FakeTextToSpeech(
            SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
        )
        # LEGACY_USER_ID is fully pre-generated with a working provider, so the
        # raising provider below is never actually called for them (every skill
        # already exists -> skipped) - a genuine mixed success/failure batch.
        pregenerate_upcoming_days(session, _full_provider(), working_tts, LEGACY_USER_ID, today)
        get_or_create_profile(session, other_user_id, today)

        result = pregenerate_for_all_learners(session, _RaisingProvider(), working_tts, today)

        assert str(LEGACY_USER_ID) in result["processed"]
        assert str(LEGACY_USER_ID) not in result["errors"]
        assert str(other_user_id) in result["errors"]
    finally:
        session.close()
