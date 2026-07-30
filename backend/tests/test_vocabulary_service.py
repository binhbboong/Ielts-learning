from datetime import date, datetime, timedelta, timezone

import pytest

from app.core import clock
from app.models.vocabulary import (
    ReviewSessionItem,
    VocabularyWord,
)
from app.schemas.vocabulary import ReviewOutcome, VocabularyWordCreate
from app.services.vocabulary import (
    add_word,
    assess_current_item,
    get_current_item,
    get_due_summary,
    get_review_complete_summary,
    reschedule,
    start_or_resume_review,
)


def test_add_word_minimal_fields_sets_initial_schedule(db_session):
    today = date(2026, 7, 29)
    created = add_word(
        db_session,
        VocabularyWordCreate(word="ubiquitous", meaning="found everywhere"),
        today=today,
    )
    db_session.expire_all()
    stored = db_session.get(VocabularyWord, created.id)

    assert stored.word == "ubiquitous"
    assert stored.example is None
    assert stored.topic is None
    assert stored.interval_index == 0
    assert stored.next_due_date == today + timedelta(days=1)


def test_add_word_default_schedule_uses_learner_local_date(
    db_session, monkeypatch
):
    instant = datetime(2026, 7, 29, 17, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "utc_now", lambda: instant)

    created = add_word(
        db_session,
        VocabularyWordCreate(word="boundary", meaning="local date"),
    )

    assert created.next_due_date == date(2026, 7, 31)


def test_due_summary_counts_and_breaks_down_due_words(db_session):
    today = date(2026, 7, 29)
    db_session.add_all(
        [
            VocabularyWord(
                word="a",
                meaning="A",
                topic="Environment",
                interval_index=0,
                next_due_date=today,
            ),
            VocabularyWord(
                word="b",
                meaning="B",
                topic="Environment",
                interval_index=2,
                next_due_date=today - timedelta(days=1),
            ),
            VocabularyWord(
                word="c",
                meaning="C",
                topic=None,
                interval_index=0,
                next_due_date=today,
            ),
            VocabularyWord(
                word="future",
                meaning="Later",
                interval_index=1,
                next_due_date=today + timedelta(days=1),
            ),
        ]
    )
    db_session.commit()

    summary = get_due_summary(db_session, today=today)

    assert summary.total_due == 3
    assert summary.by_interval == {"1_day": 2, "7_days": 1}
    assert summary.by_topic == {"Environment": 2, "Uncategorized": 1}
    assert get_due_summary(
        db_session, today=today - timedelta(days=30)
    ).total_due == 0


@pytest.mark.parametrize(
    "current,expected_index,days",
    [(0, 1, 3), (1, 2, 7), (2, 3, 14), (3, 4, 30), (4, 4, 30)],
)
def test_reschedule_remembered(current, expected_index, days):
    today = date(2026, 7, 29)
    assert reschedule(current, ReviewOutcome.remembered, today=today) == (
        expected_index,
        today + timedelta(days=days),
    )


@pytest.mark.parametrize("current", range(5))
def test_reschedule_forgot_resets_to_step_zero_from_any_step(current):
    today = date(2026, 7, 29)
    assert reschedule(current, ReviewOutcome.forgot, today=today) == (
        0,
        today + timedelta(days=1),
    )


def _due_word(label: str, today: date) -> VocabularyWord:
    return VocabularyWord(
        word=label,
        meaning=f"{label} meaning",
        interval_index=0,
        next_due_date=today,
    )


def test_start_or_resume_snapshots_due_queue_without_rewriting_it(db_session):
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today)])
    db_session.commit()

    first = start_or_resume_review(db_session, today=today)
    initial = [
        (item.word_id, item.position, item.outcome)
        for item in db_session.query(ReviewSessionItem)
        .order_by(ReviewSessionItem.position)
        .all()
    ]
    resumed = start_or_resume_review(db_session, today=today)

    assert resumed.id == first.id
    assert initial == [
        (item.word_id, item.position, item.outcome)
        for item in db_session.query(ReviewSessionItem)
        .order_by(ReviewSessionItem.position)
        .all()
    ]


def test_resume_returns_exact_first_unassessed_item(db_session):
    today = date(2026, 7, 29)
    db_session.add_all(
        [_due_word("a", today), _due_word("b", today), _due_word("c", today)]
    )
    db_session.commit()
    session = start_or_resume_review(db_session, today=today)
    items = (
        db_session.query(ReviewSessionItem)
        .filter_by(session_id=session.id)
        .order_by(ReviewSessionItem.position)
        .all()
    )
    items[0].outcome = ReviewOutcome.remembered.value
    db_session.commit()
    db_session.expire_all()

    current = get_current_item(db_session, today=today)

    assert current.kind == "item"
    assert current.item.item_id == items[1].id
    assert current.item.position == 1
    assert current.item.total == 3


def test_get_current_item_distinguishes_nothing_due(db_session):
    result = get_current_item(db_session, today=date(2026, 7, 29))
    assert result.kind == "nothing_due"
    assert result.item is None


def test_assessment_commits_reschedule_and_advances_then_completes(db_session):
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today)])
    db_session.commit()
    session = start_or_resume_review(db_session, today=today)

    first = get_current_item(db_session, today=today)
    next_result = assess_current_item(
        db_session, ReviewOutcome.remembered, today=today
    )
    db_session.expire_all()
    first_item = db_session.get(ReviewSessionItem, first.item.item_id)
    first_word = db_session.get(VocabularyWord, first.item.word_id)
    assert first_item.outcome == "remembered"
    assert first_word.interval_index == 1
    assert first_word.next_due_date == today + timedelta(days=3)
    assert next_result.kind == "item"

    final = assess_current_item(
        db_session, ReviewOutcome.forgot, today=today
    )
    assert final.kind == "complete"
    db_session.expire_all()
    assert start_or_resume_review(db_session, today=today) is None
    summary = get_review_complete_summary(db_session, session.id)
    assert summary.total_reviewed == 2
    assert summary.remembered == 1
    assert summary.forgot == 1


def test_add_word_during_active_session_does_not_change_snapshot(db_session):
    today = date(2026, 7, 29)
    db_session.add(_due_word("existing", today))
    db_session.commit()
    session = start_or_resume_review(db_session, today=today)
    before = [
        (item.id, item.word_id, item.position, item.outcome)
        for item in db_session.query(ReviewSessionItem)
        .filter_by(session_id=session.id)
        .all()
    ]
    current_before = get_current_item(db_session, today=today)

    add_word(
        db_session,
        VocabularyWordCreate(word="new", meaning="new meaning"),
        today=today,
    )

    after = [
        (item.id, item.word_id, item.position, item.outcome)
        for item in db_session.query(ReviewSessionItem)
        .filter_by(session_id=session.id)
        .all()
    ]
    assert after == before
    assert (
        get_current_item(db_session, today=today).item.item_id
        == current_before.item.item_id
    )
