from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def learner_today(*, now: datetime | None = None) -> date:
    instant = now or utc_now()
    return instant.astimezone(ZoneInfo(settings.LEARNER_TIMEZONE)).date()


def learner_day_start_utc(day: date) -> datetime:
    local_start = datetime.combine(
        day, time.min, tzinfo=ZoneInfo(settings.LEARNER_TIMEZONE)
    )
    return local_start.astimezone(timezone.utc)
