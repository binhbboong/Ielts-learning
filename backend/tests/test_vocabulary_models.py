from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models.vocabulary import (
    ReviewSession,
    ReviewSessionItem,
    VocabularyWord,
)


def test_vocabulary_schema_has_foreign_keys_constraints_and_indexes(db_session):
    inspector = inspect(db_session.bind)
    assert {
        "vocabulary_words",
        "review_sessions",
        "review_session_items",
    }.issubset(inspector.get_table_names())

    foreign_keys = inspector.get_foreign_keys("review_session_items")
    assert {
        (fk["referred_table"], tuple(fk["constrained_columns"]))
        for fk in foreign_keys
    } == {
        ("review_sessions", ("session_id",)),
        ("vocabulary_words", ("word_id",)),
    }
    unique_columns = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints("review_session_items")
    }
    assert ("session_id", "position") in unique_columns
    assert ("session_id", "word_id") in unique_columns
    assert any(
        index["name"] == "ix_vocabulary_words_next_due_date"
        for index in inspector.get_indexes("vocabulary_words")
    )
    active_index = next(
        index
        for index in inspector.get_indexes("review_sessions")
        if index["name"] == "uq_review_sessions_single_active"
    )
    assert active_index["unique"] is True
    assert "completed_at IS NULL" in str(
        active_index["dialect_options"]["postgresql_where"]
    )


def test_constraints_reject_duplicate_items_and_second_active_session(db_session):
    word = VocabularyWord(
        word="notwithstanding",
        meaning="despite",
        interval_index=0,
        next_due_date=date.today(),
    )
    session = ReviewSession(started_at=datetime.now(timezone.utc))
    db_session.add_all([word, session])
    db_session.commit()
    db_session.add(
        ReviewSessionItem(session_id=session.id, word_id=word.id, position=0)
    )
    db_session.commit()

    db_session.add(
        ReviewSessionItem(session_id=session.id, word_id=word.id, position=1)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(ReviewSession(started_at=datetime.now(timezone.utc)))
    with pytest.raises(IntegrityError):
        db_session.commit()
