from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models.study_plan import PlanState, StudySkill, Task, TaskStatus
from app.routers.study_plan import router


def _client(db_session_factory, authenticated=True):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def _seed(db_session_factory):
    with db_session_factory() as session:
        session.add(PlanState(id=1, current_day_number=2, total_days=180))
        session.add_all(
            [
                Task(
                    day_number=day,
                    skill=StudySkill.reading,
                    title=f"Day {day}",
                    description="Read",
                    estimated_minutes=20,
                    status=TaskStatus.not_started,
                    note=None,
                    updated_at=datetime.now(timezone.utc),
                )
                for day in (1, 2)
            ]
        )
        session.commit()


def test_router_requires_authentication(db_session_factory):
    client = _client(db_session_factory, authenticated=False)
    assert client.get("/api/study-plan/state").status_code == 401


def test_router_round_trips_reads_and_mutations(db_session_factory):
    _seed(db_session_factory)
    client = _client(db_session_factory)

    assert client.get("/api/study-plan/state").json()["current_day_number"] == 2
    past = client.get("/api/study-plan/days/1/tasks").json()
    current = client.get("/api/study-plan/days/2/tasks").json()
    task_id = current[0]["id"]
    assert len(past) == 1
    assert client.get(f"/api/study-plan/tasks/{task_id}").status_code == 200

    response = client.patch(
        f"/api/study-plan/tasks/{task_id}/status",
        json={"status": "completed"},
    )
    assert response.json()["status"] == "completed"
    response = client.patch(
        f"/api/study-plan/tasks/{task_id}/note",
        json={"note": "Remember this."},
    )
    assert response.json()["note"] == "Remember this."
    response = client.patch(
        f"/api/study-plan/tasks/{task_id}",
        json={"description": "Edited", "estimated_minutes": 35},
    )
    assert response.json()["description"] == "Edited"
    assert response.json()["estimated_minutes"] == 35

    response = client.post("/api/study-plan/move-to-next-day")
    assert response.status_code == 200
    assert response.json()["current_day_number"] == 3


def test_move_endpoint_returns_conflict_with_unresolved_ids(db_session_factory):
    _seed(db_session_factory)
    client = _client(db_session_factory)
    task_id = client.get("/api/study-plan/days/2/tasks").json()[0]["id"]

    response = client.post("/api/study-plan/move-to-next-day")

    assert response.status_code == 409
    assert response.json()["detail"]["unresolved_task_ids"] == [task_id]
