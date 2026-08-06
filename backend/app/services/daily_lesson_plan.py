from dataclasses import dataclass, field
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
from app.services import listening_practice, reading_practice, vocabulary as vocabulary_service
from app.services.text_to_speech import TextToSpeech

_LISTENING_FAILED_STATES = {"script_failed", "audio_failed"}
# Speaking was removed from the daily rotation/checkpoint per
# docs/adr/2026-08-05-remove-speaking-from-daily-checkpoint.md — it remains a
# standalone, learner-initiated feature (Speaking Coach) outside this daily plan.
# The per-skill helper functions below still recognize "speaking" for that
# standalone flow; they are simply never called with it from ALL_SKILLS-driven
# daily generation/checkpoint loops anymore.
ALL_SKILLS = ("reading", "listening", "writing")
CHECKPOINT_PASS_RATIO = 0.8
# Kept as the beginner-tier default (used as a fallback and by any caller that
# doesn't go through _skill_minutes_and_priority's tier lookup).
PRIMARY_SKILL_MINUTES = 20
SUPPORT_SKILL_MINUTES = 10
# Per-tier (primary, support) minutes, per docs/adr/2026-08-05-ielts-exam-
# structure-band-scaling.md revision 6.
_MINUTES_BY_TIER = {
    "beginner": (PRIMARY_SKILL_MINUTES, SUPPORT_SKILL_MINUTES),
    "standard": (38, 18),
}
# Advanced tier approaches real exam duration, which varies by skill (Reading
# ~60 min, Listening ~30-40 min, Writing ~60 min) rather than one shared
# number — support days stay a reduced, not full-length, version.
_ADVANCED_PRIMARY_MINUTES_BY_SKILL = {"reading": 60, "listening": 40, "writing": 60}
_ADVANCED_SUPPORT_MINUTES = 25
_PRIMARY_SKILL_BY_WEEKDAY = {
    0: "reading",
    1: "listening",
    2: "writing",
    3: "reading",
    4: "listening",
    5: "writing",
    6: "reading",
}
_PHASES = (
    ("foundation", 4.5),
    ("core_skills", 5.0),
    ("development", 5.5),
    ("consolidation", 6.0),
    ("exam_readiness", 6.5),
    ("peak_performance", 6.5),
)

# Phase -> exam part/complexity tier. Foundation/core_skills learners are true
# beginners: Speaking gets simple Part 1-style personal questions, Writing gets a
# short concrete question, not the full essay/long-turn format. Complexity steps up
# through development/consolidation (the pre-existing default) to exam_readiness/
# peak_performance (harder, more abstract). See
# docs/adr/2026-08-03-writing-speaking-level-adaptation.md.
_BEGINNER_PHASES = {"foundation", "core_skills"}
_ADVANCED_PHASES = {"exam_readiness", "peak_performance"}

_PROMPT_INSTRUCTION = {
    # Beginner tier stays a single short question (no Task 1/2 split — see
    # docs/adr/2026-08-03-writing-speaking-level-adaptation.md). From the
    # standard tier onward, Writing alternates Task 1 (data description) and
    # Task 2 (essay) by day — see docs/adr/2026-08-05-ielts-exam-structure-
    # band-scaling.md revision 4 (writing-coach spec).
    "writing": {
        "beginner": (
            "Write one short, concrete IELTS-style writing question suitable for a true "
            "beginner (around band 4.5) — an everyday, personal-experience topic (e.g. a "
            "place, a routine, a preference), not an abstract policy or argumentative "
            "essay question. State clearly that the expected response is about 100-150 "
            "words in simple, everyday vocabulary and sentence structure, targeting: {focus}"
        ),
        "standard": {
            "task1": (
                "Write one IELTS Academic Writing Task 1 prompt: ask the learner to "
                "summarize/describe the key trends, comparisons, or stages shown in a "
                "chart, graph, table, or process, in about 150 words. This app has no "
                "image-rendering capability, so include the underlying data directly as "
                "readable text inside the prompt itself (e.g. a short data table or a "
                "bullet list of figures) — sufficient for the learner to write a "
                "complete response with no external image. Targeting: {focus}"
            ),
            "task2": (
                "Write one IELTS Writing Task 2-style prompt (a single essay question) "
                "targeting: {focus}"
            ),
        },
        "advanced": {
            "task1": (
                "Write one IELTS Academic Writing Task 1 prompt on a more complex chart, "
                "graph, table, or process (e.g. multiple data series, a multi-stage "
                "process) than an intermediate learner would see, asking the learner to "
                "summarize/describe it in about 150 words. This app has no image-"
                "rendering capability, so include the underlying data directly as "
                "readable text inside the prompt itself — sufficient for the learner to "
                "write a complete response with no external image. Targeting: {focus}"
            ),
            "task2": (
                "Write one IELTS Writing Task 2-style prompt (a single essay question) on a "
                "more abstract or policy-oriented topic (e.g. society, technology, the "
                "environment, government) targeting: {focus}"
            ),
        },
    },
    "speaking": {
        "beginner": (
            "Write one IELTS Speaking Part 1-style short personal question (a simple, "
            "concrete question about the learner's own life, expecting a short spoken "
            "answer of a few sentences, not a 2-minute long turn) targeting: {focus}"
        ),
        "standard": (
            "Write one IELTS Speaking Part 2-style cue card prompt targeting: {focus}"
        ),
        "advanced": (
            "Write one IELTS Speaking Part 3-style abstract discussion question (following "
            "on from a Part 2 topic, expecting analysis and opinion, not just description) "
            "targeting: {focus}"
        ),
    },
}


def _prompt_complexity_tier(phase: str) -> str:
    if phase in _BEGINNER_PHASES:
        return "beginner"
    if phase in _ADVANCED_PHASES:
        return "advanced"
    return "standard"


def _content_tier(phase: str) -> str:
    """Reading/Listening structural generation tier (beginner=1 passage/
    section, standard=2, advanced=3 passages/4 sections with the full
    question-type catalog) — same phase mapping as Writing/Speaking prompt
    complexity."""
    return _prompt_complexity_tier(phase)


def _writing_task_for_day(day: date) -> str:
    """Alternates Task 1 (data description) / Task 2 (essay) by calendar day —
    deterministic so a retry on the same day reuses the same task."""
    return "task1" if day.toordinal() % 2 == 0 else "task2"


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
    tier = _prompt_complexity_tier(focus.phase)
    template = _PROMPT_INSTRUCTION[focus.skill][tier]
    if isinstance(template, dict):
        # Writing, standard/advanced tier: alternates Task 1/Task 2 by day.
        focus.task_type = _writing_task_for_day(focus.day)
        template = template[focus.task_type]
    instruction = (
        template.format(focus=focus_description)
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


def _skill_minutes_and_priority(day: date, skill: str, phase: str) -> tuple[int, str]:
    primary_skill = _PRIMARY_SKILL_BY_WEEKDAY[day.weekday()]
    tier = _prompt_complexity_tier(phase)
    if tier == "advanced":
        primary_minutes = _ADVANCED_PRIMARY_MINUTES_BY_SKILL.get(skill, 60)
        support_minutes = _ADVANCED_SUPPORT_MINUTES
    else:
        primary_minutes, support_minutes = _MINUTES_BY_TIER.get(
            tier, _MINUTES_BY_TIER["standard"]
        )
    if skill == primary_skill:
        return primary_minutes, "primary"
    return support_minutes, "support"


def ensure_today_generated(
    db: Session,
    day: date,
    provider: AIProvider,
    tts: TextToSpeech,
    user_id: uuid.UUID = LEGACY_USER_ID,
) -> None:
    profile = get_or_create_profile(db, user_id, day)
    _, phase, _ = plan_context(profile, day)
    content_tier = _content_tier(phase)

    for skill in ALL_SKILLS:
        minutes, priority = _skill_minutes_and_priority(day, skill, phase)
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
                db, day, generation_focus, provider, user_id, tier=content_tier
            )
        elif skill == "listening":
            listening_practice.get_or_create_exercise(
                db, day, generation_focus, provider, tts, user_id, tier=content_tier
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
    content_tier = _content_tier(focus.phase)

    if skill == "reading":
        reading_practice.retry_exercise(db, day, provider, user_id, tier=content_tier)
    elif skill == "listening":
        exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
        if exercise.status == "script_failed":
            exercise = listening_practice.retry_script(
                db, day, provider, user_id, tier=content_tier
            )
            if exercise.status == "script_generated":
                listening_practice.retry_audio(db, day, tts, user_id)
        elif exercise.status == "audio_failed":
            listening_practice.retry_audio(db, day, tts, user_id)
    else:
        result = generate_prompt_text(provider, focus)
        if result.status == "ok":
            focus.generated_prompt_text = result.message
            db.commit()


def _reading_or_listening_checkpoint(
    db: Session, day: date, exercise_model, get_questions_fn, submission_model,
    user_id: uuid.UUID,
) -> bool:
    exercise = db.query(exercise_model).filter_by(user_id=user_id, day=day).one_or_none()
    if exercise is None:
        return False
    submission = (
        db.query(submission_model).filter_by(exercise_id=exercise.id).one_or_none()
    )
    if submission is None:
        return False
    total = len(get_questions_fn(db, exercise.id))
    if not total:
        return False
    return (submission.score / total) >= CHECKPOINT_PASS_RATIO


def _writing_checkpoint(
    db: Session, day: date, user_id: uuid.UUID, required_band: float
) -> bool:
    return (
        db.query(WritingSubmission)
        .filter(
            WritingSubmission.user_id == user_id,
            WritingSubmission.day == day,
            WritingSubmission.overall_band.isnot(None),
            WritingSubmission.overall_band >= required_band,
        )
        .first()
        is not None
    )


def _speaking_checkpoint(
    db: Session, day: date, user_id: uuid.UUID, required_band: float
) -> bool:
    submissions = (
        db.query(SpeakingSubmission).filter_by(user_id=user_id, day=day).all()
    )
    for submission in submissions:
        criteria = (
            submission.fluency_and_coherence,
            submission.lexical_resource,
            submission.grammatical_range_and_accuracy,
        )
        if not all(criteria):
            continue
        average = sum(c["band_score"] for c in criteria) / len(criteria)
        if average >= required_band:
            return True
    return False


def evaluate_skill_checkpoint(
    db: Session, day: date, skill: str, user_id: uuid.UUID, required_band: float
) -> bool:
    """`required_band` is the same phase-scaled band plan_context() uses to
    generate that day's content (e.g. 4.5 for a foundation-phase learner) —
    not the profile's fixed minimum_skill_band, which stays constant
    regardless of phase and previously made the writing/speaking checkpoint
    impossible to pass for early-phase learners (their content is
    intentionally easier than the target they'd be graded against)."""
    if skill == "reading":
        return _reading_or_listening_checkpoint(
            db, day, ReadingExercise, reading_practice.get_questions, ReadingSubmission,
            user_id,
        )
    if skill == "listening":
        return _reading_or_listening_checkpoint(
            db, day, ListeningExercise, listening_practice.get_questions,
            ListeningSubmission, user_id,
        )
    if skill == "writing":
        return _writing_checkpoint(db, day, user_id, required_band)
    if skill == "speaking":
        return _speaking_checkpoint(db, day, user_id, required_band)
    raise ValueError(f"unknown skill: {skill}")


@dataclass
class CheckpointStatus:
    day: date
    skills: dict = field(default_factory=dict)
    vocabulary_quiz: bool = False
    passed_count: int = 0
    required_count: int = len(ALL_SKILLS) + 1
    all_passed: bool = False


def evaluate_checkpoint(
    db: Session, day: date, user_id: uuid.UUID = LEGACY_USER_ID
) -> CheckpointStatus:
    profile = get_or_create_profile(db, user_id, day)
    _, _, required_band = plan_context(profile, day)
    skills = {
        skill: evaluate_skill_checkpoint(db, day, skill, user_id, required_band)
        for skill in ALL_SKILLS
    }
    quiz_result = vocabulary_service.get_quiz_result(db, day, user_id)
    vocabulary_passed = quiz_result is not None and quiz_result.passed
    passed_count = sum(skills.values()) + (1 if vocabulary_passed else 0)
    return CheckpointStatus(
        day=day,
        skills=skills,
        vocabulary_quiz=vocabulary_passed,
        passed_count=passed_count,
        all_passed=passed_count == len(ALL_SKILLS) + 1,
    )


def get_effective_day(
    db: Session, user_id: uuid.UUID, today: date
) -> date:
    profile = get_or_create_profile(db, user_id, today)
    day = profile.start_date
    while day < today:
        if not evaluate_checkpoint(db, day, user_id).all_passed:
            return day
        day += timedelta(days=1)
    return today


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
    generated_prompt_text: str | None = None
    task_type: str | None = None


@dataclass
class DailyOverviewResult:
    entries: list[SkillOverviewEntry]
    effective_day: date
    checkpoint: CheckpointStatus


def get_overview(
    db: Session, today: date, provider: AIProvider, tts: TextToSpeech,
    user_id: uuid.UUID = LEGACY_USER_ID,
) -> DailyOverviewResult:
    effective_day = get_effective_day(db, user_id, today)
    ensure_today_generated(db, effective_day, provider, tts, user_id)

    entries: list[SkillOverviewEntry] = []
    focuses = (
        db.query(DailyFocus)
        .filter(DailyFocus.user_id == user_id, DailyFocus.day <= effective_day)
        .order_by(DailyFocus.day, DailyFocus.skill)
        .all()
    )
    for focus in focuses:
        status = get_skill_status(db, focus.day, focus.skill, user_id)
        if focus.day == effective_day or status != "done":
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
                    generated_prompt_text=focus.generated_prompt_text,
                    task_type=focus.task_type,
                )
            )
    checkpoint = evaluate_checkpoint(db, effective_day, user_id)
    return DailyOverviewResult(
        entries=entries, effective_day=effective_day, checkpoint=checkpoint
    )


PREGENERATE_LOOKAHEAD_DAYS = 2


def pregenerate_upcoming_days(
    db: Session,
    provider: AIProvider,
    tts: TextToSpeech,
    user_id: uuid.UUID,
    today: date,
) -> list[date]:
    effective_day = get_effective_day(db, user_id, today)
    processed = []
    for offset in range(PREGENERATE_LOOKAHEAD_DAYS):
        day = effective_day + timedelta(days=offset)
        ensure_today_generated(db, day, provider, tts, user_id)
        processed.append(day)
    return processed


def pregenerate_for_all_learners(
    db: Session, provider: AIProvider, tts: TextToSpeech, today: date
) -> dict:
    processed_by_user: dict = {}
    errors_by_user: dict = {}
    profiles = db.query(StudyProfile).all()
    for profile in profiles:
        user_key = str(profile.user_id)
        try:
            processed_by_user[user_key] = pregenerate_upcoming_days(
                db, provider, tts, profile.user_id, today
            )
        except Exception as exc:  # noqa: BLE001 - one learner's failure must not abort the batch
            db.rollback()
            errors_by_user[user_key] = str(exc)
    return {"processed": processed_by_user, "errors": errors_by_user}
