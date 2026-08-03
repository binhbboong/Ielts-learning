from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.daily_lesson_plan import DailyFocus
from app.models.user import User
from app.schemas.daily_lesson_plan import DailyOverviewResponse, SkillOverviewEntry
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
    entries = service.get_overview(db, today, provider, tts, user.id)
    return DailyOverviewResponse(
        exam_type=profile.exam_type,
        week=week,
        phase=phase,
        target_band=target_band,
        total_minutes=profile.daily_minutes,
        review_minutes=10,
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
            )
            for entry in entries
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
    )
