from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.daily_lesson_plan import DailyFocus
from app.models.user import User
from app.schemas.daily_lesson_plan import (
    CheckpointStatus,
    DailyOverviewResponse,
    SkillOverviewEntry,
)
from app.services import daily_lesson_plan as service
from app.services.text_to_speech import TextToSpeech, get_text_to_speech

router = APIRouter(
    prefix="/api/daily-lesson",
    dependencies=[Depends(require_learner)],
)


@router.get("/overview", response_model=DailyOverviewResponse)
def overview(
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    tts: TextToSpeech = Depends(get_text_to_speech),
    user: User = Depends(require_learner),
) -> DailyOverviewResponse:
    today = date.today()
    profile = service.get_or_create_profile(db, user.id, today)
    week, phase, target_band = service.plan_context(profile, today)
    result = service.get_overview(db, today, provider, tts, user.id)
    return DailyOverviewResponse(
        exam_type=profile.exam_type,
        week=week,
        phase=phase,
        target_band=target_band,
        total_minutes=profile.daily_minutes,
        review_minutes=10,
        effective_day=result.effective_day,
        checkpoint=CheckpointStatus(
            day=result.checkpoint.day,
            skills=result.checkpoint.skills,
            vocabulary_quiz=result.checkpoint.vocabulary_quiz,
            passed_count=result.checkpoint.passed_count,
            required_count=result.checkpoint.required_count,
            all_passed=result.checkpoint.all_passed,
        ),
        skills=[
            SkillOverviewEntry(
                day=entry.day,
                skill=entry.skill,
                status=entry.status,
                focus_reference=entry.focus_reference,
                target_band=entry.target_band,
                estimated_minutes=entry.estimated_minutes,
                priority=entry.priority,
                phase=entry.phase,
                rationale=entry.rationale,
                generated_prompt_text=entry.generated_prompt_text,
                task_type=entry.task_type,
                writing_level=entry.writing_level,
                exercise_type=entry.exercise_type,
                exercise_label=entry.exercise_label,
                objective=entry.objective,
                min_sentences=entry.min_sentences,
                max_sentences=entry.max_sentences,
                min_words=entry.min_words,
                max_words=entry.max_words,
                sentence_frames=list(entry.sentence_frames),
                show_ielts_band=entry.show_ielts_band,
            )
            for entry in result.entries
        ]
    )


@router.post("/{skill}/retry", response_model=SkillOverviewEntry)
def retry(
    skill: str,
    day: date | None = None,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    tts: TextToSpeech = Depends(get_text_to_speech),
    user: User = Depends(require_learner),
) -> SkillOverviewEntry:
    target_day = day or date.today()
    service.retry_skill(db, target_day, skill, provider, tts, user.id)
    status = service.get_skill_status(db, target_day, skill, user.id)
    focus = db.query(DailyFocus).filter_by(
        user_id=user.id, day=target_day, skill=skill
    ).one()
    config = (
        service.writing_level_config(focus.phase, focus.task_type)
        if skill == "writing"
        else None
    )
    return SkillOverviewEntry(
        day=target_day,
        skill=skill,
        status=status,
        focus_reference=focus.focus_reference,
        target_band=focus.target_band,
        estimated_minutes=focus.estimated_minutes,
        priority=focus.priority,
        phase=focus.phase,
        rationale=focus.rationale,
        generated_prompt_text=focus.generated_prompt_text,
        task_type=focus.task_type,
        writing_level=config.level if config else None,
        exercise_type=config.exercise_type if config else None,
        exercise_label=config.label if config else None,
        objective=config.objective if config else None,
        min_sentences=config.min_sentences if config else None,
        max_sentences=config.max_sentences if config else None,
        min_words=config.min_words if config else None,
        max_words=config.max_words if config else None,
        sentence_frames=list(config.sentence_frames) if config else [],
        show_ielts_band=config.show_ielts_band if config else False,
    )
