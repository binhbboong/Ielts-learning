from sqlalchemy import inspect, text

from app.models.mistake import Mistake


def test_mistakes_schema_has_required_columns_defaults_and_indexes(db_session):
    inspector = inspect(db_session.bind)
    columns = {column["name"]: column for column in inspector.get_columns("mistakes")}

    assert set(columns) == {
        "id",
        "user_id",
        "skill",
        "question_type",
        "source",
        "own_answer",
        "correct_answer",
        "explanation",
        "reason_category",
        "logged_at",
    }
    assert columns["reason_category"]["nullable"] is False
    assert "not_sure_other" in columns["reason_category"]["default"]
    assert columns["logged_at"]["default"] is not None
    indexed_columns = {
        tuple(index["column_names"]) for index in inspector.get_indexes("mistakes")
    }
    assert ("logged_at",) in indexed_columns
    assert ("reason_category",) in indexed_columns


def test_minimal_mistake_uses_database_defaults(db_session):
    db_session.execute(
        text("INSERT INTO mistakes (skill, source) VALUES (:skill, :source)"),
        {"skill": "reading", "source": "Cambridge 18"},
    )
    db_session.commit()
    db_session.expire_all()

    mistake = db_session.query(Mistake).one()
    assert mistake.id is not None
    assert mistake.reason_category == "not_sure_other"
    assert mistake.logged_at is not None
    assert mistake.correct_answer is None
