from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.mistake import MistakeCreate, ReasonCategory
from app.models.mistake import Mistake
from app.services.mistake import (
    create_mistake,
    get_category_detail,
    is_incomplete,
    list_grouped_by_reason,
    list_mistakes,
    mistake_to_read,
)


def _full_payload(**overrides):
    values = {
        "skill": "reading",
        "question_type": "matching headings",
        "source": "Cambridge 18 Test 1",
        "own_answer": "A",
        "correct_answer": "B",
        "explanation": "I missed the synonym.",
        "reason_category": ReasonCategory.missed_paraphrase,
    }
    values.update(overrides)
    return MistakeCreate(**values)


def test_create_complete_mistake_persists_every_field(db_session):
    created = create_mistake(db_session, _full_payload())
    db_session.expire_all()
    stored = db_session.get(type(created), created.id)

    assert stored.skill == "reading"
    assert stored.question_type == "matching headings"
    assert stored.source == "Cambridge 18 Test 1"
    assert stored.own_answer == "A"
    assert stored.correct_answer == "B"
    assert stored.explanation == "I missed the synonym."
    assert stored.reason_category == "missed_paraphrase"


def test_schema_accepts_exactly_nine_reason_keys():
    assert len(ReasonCategory) == 9
    for reason in ReasonCategory:
        assert _full_payload(reason_category=reason).reason_category == reason

    with pytest.raises(ValidationError):
        _full_payload(reason_category="invented_reason")


def test_partial_mistakes_are_saved_and_completeness_is_computed(db_session):
    minimal = create_mistake(
        db_session,
        MistakeCreate(skill="listening", source="Practice set"),
    )
    assert minimal.reason_category == "not_sure_other"
    assert is_incomplete(minimal) is True

    missing_answer = create_mistake(
        db_session, _full_payload(correct_answer=None)
    )
    default_reason = create_mistake(
        db_session,
        _full_payload(reason_category=ReasonCategory.not_sure_other),
    )
    complete = create_mistake(db_session, _full_payload())

    assert is_incomplete(missing_answer) is True
    assert is_incomplete(default_reason) is True
    assert is_incomplete(complete) is False
    assert mistake_to_read(minimal).is_incomplete is True


def _row(logged_at, reason="carelessness", **overrides):
    values = {
        "skill": "reading",
        "source": "Practice",
        "own_answer": "A",
        "correct_answer": "B",
        "explanation": "Example",
        "reason_category": reason,
        "logged_at": logged_at,
    }
    values.update(overrides)
    return Mistake(**values)


def test_list_mistakes_filters_inclusive_range_and_sorts_newest_first(
    db_session,
):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _row(now - timedelta(days=8)),
            _row(now - timedelta(days=3)),
            _row(now - timedelta(days=1)),
        ]
    )
    db_session.commit()

    results = list_mistakes(
        db_session, now - timedelta(days=7), now
    )

    assert [row.logged_at for row in results] == sorted(
        [row.logged_at for row in results], reverse=True
    )
    assert len(results) == 2
    assert list_mistakes(
        db_session, now + timedelta(days=1), now + timedelta(days=2)
    ) == []


def test_grouped_counts_are_ranked_and_keep_count_of_one(db_session):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _row(now, "carelessness"),
            _row(now - timedelta(hours=1), "carelessness"),
            _row(now - timedelta(hours=2), "wrong_grammar"),
        ]
    )
    db_session.commit()

    results = list_grouped_by_reason(
        db_session, now - timedelta(days=1), now + timedelta(seconds=1)
    )

    assert [(item.reason_category, item.count) for item in results] == [
        (ReasonCategory.carelessness, 2),
        (ReasonCategory.wrong_grammar, 1),
    ]


def test_category_detail_returns_only_matching_concrete_examples(db_session):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _row(
                now,
                "wrong_grammar",
                own_answer="go",
                correct_answer="went",
                explanation="Past tense",
            ),
            _row(now, "carelessness"),
            _row(now - timedelta(days=10), "wrong_grammar"),
        ]
    )
    db_session.commit()

    results = get_category_detail(
        db_session,
        ReasonCategory.wrong_grammar,
        now - timedelta(days=7),
        now + timedelta(seconds=1),
    )

    assert len(results) == 1
    assert results[0].own_answer == "go"
    assert results[0].correct_answer == "went"
    assert results[0].explanation == "Past tense"
