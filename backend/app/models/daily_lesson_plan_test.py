from datetime import date

from app.models.daily_lesson_plan import DailyFocus


def test_daily_focus_round_trips_through_a_fresh_session(db_session_factory):
    session = db_session_factory()
    try:
        focus = DailyFocus(
            day=date(2026, 7, 30),
            skill="reading",
            focus_kind="mistake",
            focus_reference="the word 'nevertheless'",
        )
        session.add(focus)
        session.commit()
        focus_id = focus.id
    finally:
        session.close()

    fresh = db_session_factory()
    try:
        reloaded = fresh.query(DailyFocus).filter_by(id=focus_id).one()
        assert reloaded.day == date(2026, 7, 30)
        assert reloaded.skill == "reading"
        assert reloaded.focus_kind == "mistake"
        assert reloaded.focus_reference == "the word 'nevertheless'"
        assert reloaded.generated_prompt_text is None
    finally:
        fresh.close()


def test_daily_focus_allows_null_focus_reference_for_default_kind(db_session_factory):
    session = db_session_factory()
    try:
        focus = DailyFocus(
            day=date(2026, 7, 30),
            skill="writing",
            focus_kind="default",
            focus_reference=None,
        )
        session.add(focus)
        session.commit()
    finally:
        session.close()


def test_daily_focus_day_and_skill_combination_is_unique(db_session_factory):
    session = db_session_factory()
    try:
        session.add(
            DailyFocus(day=date(2026, 8, 1), skill="reading", focus_kind="default", focus_reference=None)
        )
        session.commit()
    finally:
        session.close()

    session2 = db_session_factory()
    try:
        session2.add(
            DailyFocus(day=date(2026, 8, 1), skill="reading", focus_kind="default", focus_reference=None)
        )
        try:
            session2.commit()
            raised = False
        except Exception:
            session2.rollback()
            raised = True
        assert raised is True
    finally:
        session2.close()

    session3 = db_session_factory()
    try:
        session3.add(
            DailyFocus(day=date(2026, 8, 1), skill="listening", focus_kind="default", focus_reference=None)
        )
        session3.commit()
    finally:
        session3.close()


def test_daily_focus_stores_generated_prompt_text_for_writing_and_speaking(
    db_session_factory,
):
    session = db_session_factory()
    try:
        focus = DailyFocus(
            day=date(2026, 7, 30),
            skill="writing",
            focus_kind="default",
            focus_reference=None,
            generated_prompt_text="Some people believe...",
        )
        session.add(focus)
        session.commit()
        focus_id = focus.id
    finally:
        session.close()

    fresh = db_session_factory()
    try:
        reloaded = fresh.query(DailyFocus).filter_by(id=focus_id).one()
        assert reloaded.generated_prompt_text == "Some people believe..."
    finally:
        fresh.close()
