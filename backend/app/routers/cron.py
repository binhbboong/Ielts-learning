from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.db import get_db
from app.schemas.daily_lesson_plan import PregenerationResponse
from app.services import daily_lesson_plan as service
from app.services.text_to_speech import TextToSpeech, get_text_to_speech

router = APIRouter(prefix="/api/cron")


def verify_cron_secret(authorization: str | None = Header(default=None)) -> None:
    if not settings.CRON_SECRET or authorization != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret"
        )


@router.get(
    "/pregenerate-lessons",
    response_model=PregenerationResponse,
    dependencies=[Depends(verify_cron_secret)],
)
def pregenerate_lessons(
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    tts: TextToSpeech = Depends(get_text_to_speech),
) -> PregenerationResponse:
    result = service.pregenerate_for_all_learners(db, provider, tts, date.today())
    return PregenerationResponse(processed=result["processed"], errors=result["errors"])
