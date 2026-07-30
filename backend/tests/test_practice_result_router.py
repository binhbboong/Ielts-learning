from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models.practice_result import PracticeResult
from app.routers.practice_result import router


def _client(db_session_factory, *, authenticated=True):
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


def test_taxonomy_route_requires_authentication(db_session_factory):
    response = _client(
        db_session_factory, authenticated=False
    ).get("/api/practice-results/taxonomy")

    assert response.status_code == 401


def test_taxonomy_route_returns_canonical_reading_and_listening_lists(
    db_session_factory,
):
    response = _client(db_session_factory).get(
        "/api/practice-results/taxonomy"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["Reading"]) == 11
    assert len(body["Listening"]) == 6
    assert body["Reading"][0] == {
        "key": "multiple_choice",
        "label": "Multiple choice",
    }
    assert body["Reading"] != body["Listening"]


def test_post_result_requires_every_core_field(db_session_factory):
    payload = {
        "skill": "Reading",
        "source": "Cambridge IELTS 18 Test 1",
        "score": 32,
        "total": 40,
        "time_taken_seconds": 3600,
    }

    for field in payload:
        invalid = payload.copy()
        invalid.pop(field)
        response = _client(db_session_factory).post(
            "/api/practice-results", json=invalid
        )
        assert response.status_code == 422, field

    with db_session_factory() as session:
        assert session.query(PracticeResult).count() == 0


def test_post_result_accepts_empty_optional_fields_and_persists(
    db_session_factory,
):
    response = _client(db_session_factory).post(
        "/api/practice-results",
        json={
            "skill": "Listening",
            "source": "Cambridge IELTS 18 Test 2",
            "score": 35,
            "total": 40,
            "time_taken_seconds": 1800,
            "missed_question_types": [],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["skill"] == "Listening"
    assert body["missed_question_types"] == []
    assert body["note"] is None
    with db_session_factory() as session:
        assert session.query(PracticeResult).count() == 1


def test_post_result_rejects_question_type_from_wrong_skill(
    db_session_factory,
):
    response = _client(db_session_factory).post(
        "/api/practice-results",
        json={
            "skill": "Listening",
            "source": "Practice test",
            "score": 30,
            "total": 40,
            "time_taken_seconds": 1800,
            "missed_question_types": ["matching_headings"],
        },
    )

    assert response.status_code == 422
    with db_session_factory() as session:
        assert session.query(PracticeResult).count() == 0


def test_post_result_rejects_score_above_total(db_session_factory):
    response = _client(db_session_factory).post(
        "/api/practice-results",
        json={
            "skill": "Reading",
            "source": "Practice test",
            "score": 41,
            "total": 40,
            "time_taken_seconds": 3600,
        },
    )

    assert response.status_code == 422


def test_history_returns_complete_rows_and_supports_skill_filter_and_sort(
    db_session_factory,
):
    with db_session_factory() as session:
        session.add_all(
            [
                PracticeResult(
                    skill="Reading",
                    source="Older reading",
                    score=30,
                    total=40,
                    time_taken_seconds=3600,
                    missed_question_types=["matching_headings"],
                    note="Review headings",
                    logged_at=datetime(
                        2026, 7, 20, 8, 0, tzinfo=timezone.utc
                    ),
                ),
                PracticeResult(
                    skill="Listening",
                    source="Newer listening",
                    score=35,
                    total=40,
                    time_taken_seconds=1800,
                    missed_question_types=[],
                    note=None,
                    logged_at=datetime(
                        2026, 7, 21, 8, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )
        session.commit()

    client = _client(db_session_factory)
    newest = client.get("/api/practice-results?sort=newest")
    reading = client.get(
        "/api/practice-results?skill=Reading&sort=oldest"
    )

    assert newest.status_code == 200
    assert [row["source"] for row in newest.json()] == [
        "Newer listening",
        "Older reading",
    ]
    assert reading.status_code == 200
    assert reading.json() == [
        {
            **reading.json()[0],
            "skill": "Reading",
            "source": "Older reading",
            "score": 30,
            "total": 40,
            "time_taken_seconds": 3600,
            "missed_question_types": ["matching_headings"],
            "note": "Review headings",
        }
    ]


def test_trend_route_filters_skill_and_period_and_returns_combined_shape(
    db_session_factory,
):
    now = datetime.now(timezone.utc)
    with db_session_factory() as session:
        session.add_all(
            [
                PracticeResult(
                    skill="Reading",
                    source=f"Recent {index}",
                    score=30 + index,
                    total=40,
                    time_taken_seconds=3600,
                    missed_question_types=["matching_headings"],
                    logged_at=now,
                )
                for index in range(4)
            ]
            + [
                PracticeResult(
                    skill="Listening",
                    source="Other skill",
                    score=35,
                    total=40,
                    time_taken_seconds=1800,
                    missed_question_types=["matching"],
                    logged_at=now,
                ),
                PracticeResult(
                    skill="Reading",
                    source="Older than four weeks",
                    score=20,
                    total=40,
                    time_taken_seconds=3600,
                    missed_question_types=["multiple_choice"],
                    logged_at=now - timedelta(days=35),
                ),
            ]
        )
        session.commit()

    response = _client(db_session_factory).get(
        "/api/practice-results/trend?skill=Reading&period=4_weeks"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_count"] == 4
    assert body["threshold"]["sufficient"] is True
    assert body["direction"] in {"up", "steady", "down"}
    assert body["breakdown"] == [
        {"key": "matching_headings", "count": 4}
    ]


def test_trend_route_distinguishes_empty_success_from_database_failure(
    db_session_factory, monkeypatch
):
    client = _client(db_session_factory)
    empty = client.get(
        "/api/practice-results/trend?skill=Both&period=8_weeks"
    )
    assert empty.status_code == 200
    assert empty.json()["session_count"] == 0

    def fail(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.routers.practice_result.service.get_trend", fail
    )
    failed = client.get(
        "/api/practice-results/trend?skill=Both&period=8_weeks"
    )
    assert failed.status_code == 503
    assert "session_count" not in failed.json()
from datetime import datetime, timedelta, timezone
