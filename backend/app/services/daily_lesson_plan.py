from dataclasses import dataclass
from datetime import date, timedelta
import uuid

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import ChatRequest, ChatResult
from app.models.daily_lesson_plan import DailyFocus
from app.models.study_profile import StudyProfile
from app.models.user import LEGACY_USER_ID
from app.models.listening_practice import ListeningExercise, ListeningSubmission
from app.models.mistake import Mistake
from app.models.reading_practice import ReadingExercise, ReadingSubmission
from app.models.speaking_submission import SpeakingSubmission
from app.models.vocabulary import VocabularyWord
from app.models.writing_submission import WritingSubmission
from app.services import listening_practice, reading_practice
from app.services.text_to_speech import TextToSpeech

_LISTENING_FAILED_STATES = {"script_failed", "audio_failed"}
_DAILY_ROTATION = {
    0: (("reading", 35, "primary"), ("listening", 15, "support")),
    1: (("listening", 35, "primary"), ("speaking", 15, "support")),
    2: (("writing", 40, "primary"), ("reading", 10, "support")),
    3: (("speaking", 35, "primary"), ("listening", 15, "support")),
    4: (("reading", 25, "primary"), ("writing", 25, "support")),
    5: (("listening", 25, "primary"), ("speaking", 25, "support")),
    6: (("writing", 25, "primary"), ("reading", 25, "support")),
}
_PHASES = (
    ("foundation", 4.5),
    ("core_skills", 5.0),
    ("development", 5.5),
    ("consolidation", 6.0),
    ("exam_readiness", 6.5),
    ("peak_performance", 6.5),
)

_PROMPT_INSTRUCTION = {
    "writing": (
        "Write one IELTS Writing Task 2-style prompt (a single essay question) "
        "targeting: {focus}"
    ),
    "speaking": (
        "Write one IELTS Speaking Part 2-style cue card prompt targeting: {focus}"
    ),
}


def get_or_create_profile(
    db: Session, user_id: uuid.UUID, today: date
) -> StudyProfile:
    profile = db.get(StudyProfile, user_id)
    if profile is not None:
        return profile
    profile = StudyProfile(
        user_id=user_id,
        exam_type="ielts_academic",
        baseline_band=3.5,
        target_band=6.5,
        minimum_skill_band=6.0,
        start_date=today,
        target_date=today + timedelta(weeks=24),
        daily_minutes=60,
        study_days_per_week=5,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def plan_context(profile: StudyProfile, day: date) -> tuple[int, str, float]:
    week = max(1, min(24, ((day - profile.start_date).days // 7) + 1))
    phase_index = min(5, (week - 1) // 4)
    phase, phase_band = _PHASES[phase_index]
    return week, phase, min(profile.target_band, phase_band)


def _select_focus(
    db: Session, skill: str, day: date, user_id: uuid.UUID
) -> tuple[str, str | None]:
    mistake = (
        db.query(Mistake)
        .filter(Mistake.user_id == user_id, Mistake.skill == skill)
        .order_by(Mistake.logged_at.desc())
        .first()
    )
    if mistake is not None:
        detail = mistake.explanation or mistake.reason_category.replace("_", " ")
        return "mistake", f"a recent {skill} mistake: {detail}"

    word = (
        db.query(VocabularyWord)
        .filter(
            VocabularyWord.user_id == user_id,
            VocabularyWord.next_due_date <= day,
        )
        .order_by(VocabularyWord.next_due_date)
        .first()
    )
    if word is not None:
        return "vocabulary", f"the word '{word.word}'"

    return "default", None


def get_or_create_focus(
    db: Session,
    day: date,
    skill: str,
    user_id: uuid.UUID = LEGACY_USER_ID,
    estimated_minutes: int = 25,
    priority: str = "support",
) -> DailyFocus:
    existing = (
        db.query(DailyFocus)
        .filter_by(user_id=user_id, day=day, skill=skill)
        .one_or_none()
    )
    if existing is not None:
        return existing

    profile = get_or_create_profile(db, user_id, day)
    _, phase, target_band = plan_context(profile, day)
    focus_kind, focus_reference = _select_focus(db, skill, day, user_id)
    rationale = (
        f"Targets {focus_reference}"
        if focus_reference
        else f"{priority.title()} skill in the IELTS Academic {phase.replace('_', ' ')} phase"
    )
    focus = DailyFocus(
        user_id=user_id,
        day=day,
        skill=skill,
        focus_kind=focus_kind,
        focus_reference=focus_reference,
        target_band=target_band,
        estimated_minutes=estimated_minutes,
        priority=priority,
        phase=phase,
        rationale=rationale,
    )
    db.add(focus)
    db.commit()
    db.refresh(focus)
    return focus


def generate_prompt_text(provider: AIProvider, focus: DailyFocus) -> ChatResult:
    focus_description = focus.focus_reference or f"general IELTS {focus.skill} practice"
    instruction = (
        _PROMPT_INSTRUCTION[focus.skill].format(focus=focus_description)
        + f". This is IELTS Academic practice targeting band {focus.target_band} "
        + f"during the {focus.phase.replace('_', ' ')} phase. "
        + f"Design it for about {focus.estimated_minutes} minutes."
    )
    return provider.chat(ChatRequest(message=instruction))


def _reading_or_listening_status(
    db: Session, day: date, exercise_model, submission_model, failed_statuses: set[str],
    user_id: uuid.UUID,
) -> str:
    exercise = db.query(exercise_model).filter_by(user_id=user_id, day=day).one_or_none()
    if exercise is None:
        return "generating"
    if exercise.status in failed_statuses:
        return "failed"
    if exercise.status != "ready":
        return "generating"
    has_submission = (
        db.query(submission_model).filter_by(exercise_id=exercise.id).first()
        is not None
    )
    return "done" if has_submission else "ready"


def _writing_or_speaking_status(
    db: Session, day: date, skill: str, submission_model, user_id: uuid.UUID
) -> str:
    focus = (
        db.query(DailyFocus)
        .filter_by(user_id=user_id, day=day, skill=skill)
        .one_or_none()
    )
    if focus is None:
        return "generating"
    if not focus.generated_prompt_text:
        return "failed"
    has_submission = (
        db.query(submission_model).filter_by(user_id=user_id, day=day).first() is not None
    )
    return "done" if has_submission else "ready"


def get_skill_status(
    db: Session, day: date, skill: str, user_id: uuid.UUID = LEGACY_USER_ID
) -> str:
    if skill == "reading":
        return _reading_or_listening_status(
            db, day, ReadingExercise, ReadingSubmission, {"failed"}, user_id
        )
    if skill == "listening":
        return _reading_or_listening_status(
            db, day, ListeningExercise, ListeningSubmission, _LISTENING_FAILED_STATES, user_id
        )
    if skill == "writing":
        return _writing_or_speaking_status(db, day, "writing", WritingSubmission, user_id)
    if skill == "speaking":
        return _writing_or_speaking_status(db, day, "speaking", SpeakingSubmission, user_id)
    raise ValueError(f"unknown skill: {skill}")


def ensure_today_generated(
    db: Session,
    day: date,
    provider: AIProvider,
    tts: TextToSpeech,
    user_id: uuid.UUID = LEGACY_USER_ID,
) -> None:
    for skill, minutes, priority in _DAILY_ROTATION[day.weekday()]:
        existing = (
            db.query(DailyFocus)
            .filter_by(user_id=user_id, day=day, skill=skill)
            .one_or_none()
        )
        if existing is not None:
            continue

        focus = get_or_create_focus(
            db, day, skill, user_id, estimated_minutes=minutes, priority=priority
        )
        generation_focus = (
            f"IELTS Academic band {focus.target_band}; {focus.phase.replace('_', ' ')} phase; "
            f"{focus.estimated_minutes}-minute {focus.priority} activity; "
            f"{focus.focus_reference or 'general skill development for a software engineer'}"
        )

        if skill == "reading":
            reading_practice.get_or_create_exercise(
                db, day, generation_focus, provider, user_id
            )
        elif skill == "listening":
            listening_practice.get_or_create_exercise(
                db, day, generation_focus, provider, tts, user_id
            )
        else:
            result = generate_prompt_text(provider, focus)
            if result.status == "ok":
                focus.generated_prompt_text = result.message
                db.commit()


def retry_skill(
    db: Session, day: date, skill: str, provider: AIProvider, tts: TextToSpeech,
    user_id: uuid.UUID = LEGACY_USER_ID,
) -> None:
    focus = db.query(DailyFocus).filter_by(user_id=user_id, day=day, skill=skill).one()

    if skill == "reading":
        reading_practice.retry_exercise(db, day, provider, user_id)
    elif skill == "listening":
        exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
        if exercise.status == "script_failed":
            exercise = listening_practice.retry_script(db, day, provider, user_id)
            if exercise.status == "script_generated":
                listening_practice.retry_audio(db, day, tts, user_id)
        elif exercise.status == "audio_failed":
            listening_practice.retry_audio(db, day, tts, user_id)
    else:
        result = generate_prompt_text(provider, focus)
        if result.status == "ok":
            focus.generated_prompt_text = result.message
            db.commit()


@dataclass
class SkillOverviewEntry:
    day: date
    skill: str
    status: str
    focus_reference: str | None
    target_band: float
    estimated_minutes: int
    priority: str
    phase: str
    rationale: str


def get_overview(
    db: Session, today: date, provider: AIProvider, tts: TextToSpeech,
    user_id: uuid.UUID = LEGACY_USER_ID,
) -> list[SkillOverviewEntry]:
    ensure_today_generated(db, today, provider, tts, user_id)

    entries: list[SkillOverviewEntry] = []
    focuses = (
        db.query(DailyFocus)
        .filter(DailyFocus.user_id == user_id, DailyFocus.day <= today)
        .order_by(DailyFocus.day, DailyFocus.skill)
        .all()
    )
    for focus in focuses:
        status = get_skill_status(db, focus.day, focus.skill, user_id)
        if focus.day == today or status != "done":
            entries.append(
                SkillOverviewEntry(
                    day=focus.day,
                    skill=focus.skill,
                    status=status,
                    focus_reference=focus.focus_reference,
                    target_band=focus.target_band,
                    estimated_minutes=focus.estimated_minutes,
                    priority=focus.priority,
                    phase=focus.phase,
                    rationale=focus.rationale,
                )
            )
    return entries
