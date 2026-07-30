from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.study_plan import PlanState, StudySkill, Task, TaskStatus


TOTAL_DAYS = 180
DEFAULT_ESTIMATED_MINUTES = 20


def seed_if_empty(session: Session) -> None:
    if session.query(Task.id).first() is not None:
        return

    seeded_at = datetime.now(timezone.utc)
    tasks = [
        Task(
            day_number=day_number,
            skill=skill,
            title=f"{skill.value.capitalize()} practice",
            description=(
                f"Day {day_number} {skill.value} practice session."
            ),
            estimated_minutes=DEFAULT_ESTIMATED_MINUTES,
            status=TaskStatus.not_started,
            note="",
            updated_at=seeded_at,
        )
        for day_number in range(1, TOTAL_DAYS + 1)
        for skill in StudySkill
    ]
    session.add_all(tasks)
    session.add(
        PlanState(id=1, current_day_number=1, total_days=TOTAL_DAYS)
    )
    session.commit()


def main() -> None:
    from app.core.db import SessionLocal

    with SessionLocal() as session:
        seed_if_empty(session)


if __name__ == "__main__":
    main()
