from sqlalchemy import func

from app.db.seed_study_plan import seed_if_empty
from app.models.study_plan import PlanState, StudySkill, Task


def test_seed_populates_all_180_days_and_allowed_skills(db_session):
    seed_if_empty(db_session)

    assert db_session.query(func.count(func.distinct(Task.day_number))).scalar() == 180
    assert db_session.query(Task).count() == 180 * len(StudySkill)
    assert {task.skill for task in db_session.query(Task).all()} == set(StudySkill)

    state = db_session.get(PlanState, 1)
    assert state.current_day_number == 1
    assert state.total_days == 180


def test_seed_is_idempotent_and_preserves_existing_plan_state(db_session):
    seed_if_empty(db_session)
    initial_count = db_session.query(Task).count()
    state = db_session.get(PlanState, 1)
    state.current_day_number = 17
    db_session.commit()

    seed_if_empty(db_session)

    assert db_session.query(Task).count() == initial_count
    assert db_session.get(PlanState, 1).current_day_number == 17
    assert db_session.get(PlanState, 1).total_days == 180
