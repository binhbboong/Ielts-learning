from sqlalchemy import inspect

from app.models.practice_result import PracticeResult


def test_practice_result_schema_has_documented_columns_and_index(db_session):
    inspector = inspect(db_session.bind)

    columns = {
        column["name"]: column for column in inspector.get_columns("practice_results")
    }
    assert set(columns) == {
        "id",
        "skill",
        "source",
        "score",
        "total",
        "time_taken_seconds",
        "missed_question_types",
        "note",
        "logged_at",
    }
    assert columns["note"]["nullable"] is True
    assert columns["logged_at"]["nullable"] is False
    assert any(
        index["name"] == "ix_practice_results_skill_logged_at"
        and index["column_names"] == ["skill", "logged_at"]
        for index in inspector.get_indexes("practice_results")
    )


def test_practice_result_round_trips_empty_missed_types_and_null_note(db_session):
    result = PracticeResult(
        skill="Reading",
        source="Cambridge IELTS 18 Test 1",
        score=32,
        total=40,
        time_taken_seconds=3600,
        missed_question_types=[],
        note=None,
    )
    db_session.add(result)
    db_session.commit()
    result_id = result.id
    db_session.expire_all()

    stored = db_session.get(PracticeResult, result_id)

    assert stored.skill == "Reading"
    assert stored.source == "Cambridge IELTS 18 Test 1"
    assert stored.score == 32
    assert stored.total == 40
    assert stored.time_taken_seconds == 3600
    assert stored.missed_question_types == []
    assert stored.note is None
    assert stored.logged_at is not None
