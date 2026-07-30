from datetime import datetime, timezone

from app.core.clock import learner_today


def test_learner_today_uses_ho_chi_minh_day_at_utc_boundary():
    instant = datetime(2026, 7, 29, 17, 30, tzinfo=timezone.utc)

    assert learner_today(now=instant) == datetime(2026, 7, 30).date()
