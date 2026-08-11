from datetime import date, datetime, timedelta, timezone

import pytest

from app.core import clock
from app.models.vocabulary import (
    ReviewSession,
    ReviewSessionItem,
    VocabularyQuizItem,
    VocabularyWord,
)
from app.schemas.vocabulary import ReviewOutcome, VocabularyWordCreate
from app.services import vocabulary as vocabulary_service
from app.services.vocabulary import (
    DAILY_REVIEW_TARGET,
    QUIZ_PASS_THRESHOLD,
    _LEVEL_VOCABULARY,
    add_word,
    answer_current_quiz_item,
    assess_current_item,
    get_current_item,
    get_due_summary,
    get_history,
    get_level_recommendations,
    get_or_start_quiz_item,
    get_quiz_result,
    get_review_complete_summary,
    reschedule,
    add_level_recommendation,
    start_or_resume_review,
)


def test_level_recommendations_follow_profile_and_exclude_existing(db_session):
    today = date(2026, 7, 30)
    feed = get_level_recommendations(db_session, today=today)
    assert feed["current_band"] == 4.5
    assert feed["cefr_level"] == "B1"
    assert feed["phase"] == "foundation"
    assert len(feed["recommendations"]) == 20

    saved = add_level_recommendation(
        db_session, "4.5:essential", today=today
    )
    assert saved.target_band == 4.5
    assert saved.cefr_level == "B1"
    assert saved.source == "level_recommendation"

    refreshed = get_level_recommendations(db_session, today=today)
    assert "essential" not in {
        item["word"] for item in refreshed["recommendations"]
    }
    assert len(refreshed["recommendations"]) == 19


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


def test_due_summary_reports_daily_target_and_backfill_preview(db_session):
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today), _due_word("c", today)])
    db_session.commit()

    summary = get_due_summary(db_session, today=today)

    assert summary.total_due == 3
    assert summary.daily_target == DAILY_REVIEW_TARGET
    assert summary.backfill_count == DAILY_REVIEW_TARGET - 3
    assert summary.shortfall is False


def test_backfill_reports_shortfall_when_band_recommendations_exhausted(db_session):
    today = date(2026, 7, 29)
    for word, meaning, example, topic in _LEVEL_VOCABULARY[4.5]:
        db_session.add(
            VocabularyWord(
                word=word,
                meaning=meaning,
                example=example,
                topic=topic,
                source="level_recommendation",
                interval_index=2,
                next_due_date=today + timedelta(days=30),
            )
        )
    db_session.commit()

    summary = get_due_summary(db_session, today=today)

    assert summary.total_due == 0
    assert summary.backfill_count == 0
    assert summary.shortfall is True


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


def test_start_or_resume_backfills_to_daily_target_when_due_below_target(db_session):
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today), _due_word("c", today)])
    db_session.commit()

    session_row = start_or_resume_review(db_session, today=today)

    items = (
        db_session.query(ReviewSessionItem)
        .filter_by(session_id=session_row.id)
        .order_by(ReviewSessionItem.position)
        .all()
    )
    assert len(items) == DAILY_REVIEW_TARGET
    assert {item.word.word for item in items[:3]} == {"a", "b", "c"}
    backfilled_words = [item.word for item in items[3:]]
    assert len(backfilled_words) == DAILY_REVIEW_TARGET - 3
    assert all(word.source == "daily_backfill" for word in backfilled_words)
    assert all(word.next_due_date == today for word in backfilled_words)
    assert all(word.interval_index == 0 for word in backfilled_words)
    assert len({word.word for word in backfilled_words}) == len(backfilled_words)


def test_backfilled_word_is_persisted_source_daily_backfill_due_today(db_session):
    today = date(2026, 7, 29)

    session_row = start_or_resume_review(db_session, today=today)

    stored = (
        db_session.query(VocabularyWord)
        .filter_by(source="daily_backfill")
        .all()
    )
    assert len(stored) == DAILY_REVIEW_TARGET
    assert all(word.next_due_date == today for word in stored)
    assert all(word.interval_index == 0 for word in stored)
    assert session_row is not None


def test_start_or_resume_does_not_backfill_again_same_day_after_completion(db_session):
    today = date(2026, 7, 29)
    db_session.add(_due_word("a", today))
    db_session.commit()

    start_or_resume_review(db_session, today=today)
    while True:
        current = get_current_item(db_session, today=today)
        if current.kind != "item":
            break
        assess_current_item(db_session, ReviewOutcome.remembered, today=today)

    again = start_or_resume_review(db_session, today=today)

    assert again is None
    total_backfilled = (
        db_session.query(VocabularyWord).filter_by(source="daily_backfill").count()
    )
    assert total_backfilled == DAILY_REVIEW_TARGET - 1


def test_start_or_resume_snapshots_due_queue_without_rewriting_it(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 2)
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


def test_review_sessions_can_stay_active_for_two_different_days(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
    missed_day = date(2026, 7, 29)
    today = date(2026, 7, 30)
    db_session.add(_due_word("make-up", missed_day))
    db_session.commit()

    missed_session = start_or_resume_review(db_session, today=missed_day)
    today_session = start_or_resume_review(db_session, today=today)

    assert missed_session.id != today_session.id
    assert missed_session.day == missed_day
    assert today_session.day == today
    assert get_current_item(db_session, today=missed_day).item.session_id == missed_session.id
    assert get_current_item(db_session, today=today).item.session_id == today_session.id


def test_missed_day_prefers_fresh_progressive_words_over_reusing_library(
    db_session, monkeypatch
):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
    monkeypatch.setattr(vocabulary_service, "_backfill_daily_words", lambda *_args, **_kwargs: [])
    missed_day = clock.learner_today() - timedelta(days=1)
    db_session.add(
        VocabularyWord(
            word="reusable",
            meaning="available to study again",
            interval_index=2,
            next_due_date=missed_day + timedelta(days=30),
        )
    )
    db_session.commit()

    review_session = start_or_resume_review(db_session, today=missed_day)

    assert review_session is not None
    current = get_current_item(db_session, today=missed_day)
    assert current.kind == "item"
    assert current.item.word != "reusable"
    stored = db_session.get(VocabularyWord, current.item.word_id)
    assert stored.source == "make_up_backfill"
    assert stored.target_band == 4.5


def test_old_duplicate_queue_replaces_only_unanswered_words_on_resume(
    db_session, monkeypatch
):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 2)
    missed_day = clock.learner_today() - timedelta(days=1)
    answered_word = VocabularyWord(
        word="answered-duplicate",
        meaning="already answered on the make-up day",
        interval_index=2,
        next_due_date=missed_day + timedelta(days=30),
    )
    unanswered_word = VocabularyWord(
        word="unanswered-duplicate",
        meaning="not answered on the make-up day",
        interval_index=2,
        next_due_date=missed_day + timedelta(days=30),
    )
    previous = ReviewSession(
        day=missed_day - timedelta(days=1),
        completed_at=datetime.now(timezone.utc),
    )
    active = ReviewSession(day=missed_day)
    db_session.add_all([answered_word, unanswered_word, previous, active])
    db_session.flush()
    db_session.add_all(
        [
            ReviewSessionItem(
                session_id=previous.id,
                word_id=answered_word.id,
                position=0,
                outcome="remembered",
                assessed_at=datetime.now(timezone.utc),
            ),
            ReviewSessionItem(
                session_id=previous.id,
                word_id=unanswered_word.id,
                position=1,
                outcome="remembered",
                assessed_at=datetime.now(timezone.utc),
            ),
            ReviewSessionItem(
                session_id=active.id,
                word_id=answered_word.id,
                position=0,
                outcome="remembered",
                assessed_at=datetime.now(timezone.utc),
            ),
            ReviewSessionItem(
                session_id=active.id,
                word_id=unanswered_word.id,
                position=1,
            ),
        ]
    )
    db_session.commit()

    resumed = start_or_resume_review(db_session, today=missed_day)
    current = get_current_item(db_session, today=missed_day)

    assert resumed.id == active.id
    assert current.item.position == 1
    assert current.item.word != "unanswered-duplicate"
    replacement = db_session.get(VocabularyWord, current.item.word_id)
    assert replacement.source == "make_up_backfill"
    answered_item = (
        db_session.query(ReviewSessionItem)
        .filter_by(session_id=active.id, position=0)
        .one()
    )
    assert answered_item.word_id == answered_word.id
    assert answered_item.outcome == "remembered"


def test_resume_returns_exact_first_unassessed_item(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 3)
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


def test_zero_due_with_backfill_available_is_not_started_not_nothing_due(db_session):
    result = get_current_item(db_session, today=date(2026, 7, 29))
    assert result.kind == "not_started"
    assert result.item is None


def test_zero_due_and_zero_backfill_is_nothing_due(db_session):
    today = date(2026, 7, 29)
    for word, meaning, example, topic in _LEVEL_VOCABULARY[4.5]:
        db_session.add(
            VocabularyWord(
                word=word,
                meaning=meaning,
                example=example,
                topic=topic,
                source="level_recommendation",
                interval_index=2,
                next_due_date=today + timedelta(days=30),
            )
        )
    db_session.commit()

    result = get_current_item(db_session, today=today)

    assert result.kind == "nothing_due"
    assert result.item is None


def test_assessment_commits_reschedule_and_advances_then_completes(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 2)
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


def test_review_complete_summary_reports_new_words_included(db_session):
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today)])
    db_session.commit()
    session_row = start_or_resume_review(db_session, today=today)

    while True:
        current = get_current_item(db_session, today=today)
        if current.kind != "item":
            break
        assess_current_item(db_session, ReviewOutcome.remembered, today=today)

    summary = get_review_complete_summary(db_session, session_row.id)

    assert summary.total_reviewed == DAILY_REVIEW_TARGET
    assert summary.new_words_included == DAILY_REVIEW_TARGET - 2


def test_add_word_during_active_session_does_not_change_snapshot(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
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


def test_history_groups_added_and_reviewed_words_by_day_most_recent_first(
    db_session, monkeypatch,
):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
    # created_at/assessed_at come from real wall-clock (DB server_default / datetime.now()),
    # so "today" here must be the real learner-local day, not an arbitrary simulated date,
    # for the history buckets asserted below to line up.
    today = clock.learner_today()
    db_session.add(_due_word("yesterdaysword", today - timedelta(days=1)))
    added_today = add_word(
        db_session,
        VocabularyWordCreate(word="todaysword", meaning="added today"),
        today=today,
    )
    db_session.commit()
    older = db_session.get(VocabularyWord, db_session.query(VocabularyWord).filter_by(
        word="yesterdaysword"
    ).one().id)
    older.created_at = datetime.combine(
        today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )
    db_session.commit()

    session = start_or_resume_review(db_session, today=today)
    assess_current_item(db_session, ReviewOutcome.remembered, today=today)

    days = get_history(db_session)

    assert [d.day for d in days] == sorted(
        {d.day for d in days}, reverse=True
    )
    today_bucket = next(d for d in days if d.day == today)
    assert {w.word for w in today_bucket.words_added} == {"todaysword"}
    assert len(today_bucket.words_reviewed) == 1
    assert today_bucket.words_reviewed[0].outcome == "remembered"

    yesterday_bucket = next(d for d in days if d.day == today - timedelta(days=1))
    assert {w.word for w in yesterday_bucket.words_added} == {"yesterdaysword"}


def test_history_is_scoped_per_user(db_session):
    other_user_id = "00000000-0000-0000-0000-000000000099"
    from app.models.user import User

    db_session.add(
        User(
            id=other_user_id, email="other@example.com",
            display_name="Other", password_hash="unused",
        )
    )
    db_session.commit()
    add_word(
        db_session,
        VocabularyWordCreate(word="mine", meaning="mine"),
        today=date(2026, 7, 30),
    )
    add_word(
        db_session,
        VocabularyWordCreate(word="theirs", meaning="theirs"),
        today=date(2026, 7, 30),
        user_id=other_user_id,
    )

    days = get_history(db_session)

    all_words = {w.word for d in days for w in d.words_added}
    assert "mine" in all_words
    assert "theirs" not in all_words


def _complete_review(db_session, today):
    start_or_resume_review(db_session, today=today)
    while True:
        current = get_current_item(db_session, today=today)
        if current.kind != "item":
            break
        assess_current_item(db_session, ReviewOutcome.remembered, today=today)


def test_quiz_not_ready_before_review_session_completes(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 3)
    today = date(2026, 7, 29)
    db_session.add_all([_due_word("a", today), _due_word("b", today), _due_word("c", today)])
    db_session.commit()
    start_or_resume_review(db_session, today=today)

    result = get_or_start_quiz_item(db_session, day=today)

    assert result.kind == "not_ready"


def test_quiz_builds_items_and_answering_all_finalizes_score(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 3)
    today = date(2026, 7, 29)
    db_session.add_all(
        [
            VocabularyWord(word="a", meaning="meaning-a", cefr_level="B1", interval_index=0, next_due_date=today),
            VocabularyWord(word="b", meaning="meaning-b", cefr_level="B1", interval_index=0, next_due_date=today),
            VocabularyWord(word="c", meaning="meaning-c", cefr_level="B1", interval_index=0, next_due_date=today),
        ]
    )
    db_session.commit()
    _complete_review(db_session, today)

    first = get_or_start_quiz_item(db_session, day=today)
    assert first.kind == "item"
    assert first.item.total == 3
    assert len(first.item.options) >= 2
    assert first.item.word in {"a", "b", "c"}

    seen_words = set()
    result = first
    while result.kind == "item":
        seen_words.add(result.item.word)
        correct_meaning = f"meaning-{result.item.word}"
        correct_index = result.item.options.index(correct_meaning)
        result = answer_current_quiz_item(
            db_session, correct_index, day=today
        )

    assert result.kind == "complete"
    assert seen_words == {"a", "b", "c"}
    assert result.summary.total == 3
    assert result.summary.correct == 3
    assert result.summary.passed is True

    stored = get_quiz_result(db_session, today)
    assert stored is not None
    assert stored.correct == 3
    assert stored.total == 3


def test_quiz_below_threshold_is_not_passed(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 5)
    today = date(2026, 7, 29)
    db_session.add_all(
        [
            VocabularyWord(word=w, meaning=f"meaning-{w}", cefr_level="B1", interval_index=0, next_due_date=today)
            for w in ["a", "b", "c", "d", "e"]
        ]
    )
    db_session.commit()
    _complete_review(db_session, today)

    result = get_or_start_quiz_item(db_session, day=today)
    while result.kind == "item":
        wrong_index = next(
            i for i, opt in enumerate(result.item.options)
            if opt != f"meaning-{result.item.word}"
        )
        result = answer_current_quiz_item(db_session, wrong_index, day=today)

    assert result.kind == "complete"
    assert result.summary.correct == 0
    assert result.summary.total == 5
    assert result.summary.passed is False
    assert 0 / 5 < QUIZ_PASS_THRESHOLD


def test_failed_quiz_can_be_retried_and_clears_previous_answers(
    db_session, monkeypatch
):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 2)
    today = date(2026, 7, 29)
    db_session.add_all(
        [
            VocabularyWord(
                word=word,
                meaning=f"meaning-{word}",
                interval_index=0,
                next_due_date=today,
            )
            for word in ["a", "b"]
        ]
    )
    db_session.commit()
    _complete_review(db_session, today)

    result = get_or_start_quiz_item(db_session, day=today)
    while result.kind == "item":
        wrong_index = next(
            index
            for index, option in enumerate(result.item.options)
            if option != f"meaning-{result.item.word}"
        )
        result = answer_current_quiz_item(db_session, wrong_index, day=today)
    assert result.summary.passed is False

    retried = get_or_start_quiz_item(
        db_session, day=today, retry_failed=True
    )

    assert retried.kind == "item"
    assert retried.item.position == 0
    assert all(
        item.selected_option_index is None
        for item in db_session.query(VocabularyQuizItem).all()
    )


def test_quiz_result_is_none_before_submission(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
    today = date(2026, 7, 29)
    db_session.add(_due_word("solo", today))
    db_session.commit()
    _complete_review(db_session, today)
    get_or_start_quiz_item(db_session, day=today)

    assert get_quiz_result(db_session, today) is None


def test_quiz_cannot_be_rebuilt_once_submitted(db_session, monkeypatch):
    monkeypatch.setattr(vocabulary_service, "DAILY_REVIEW_TARGET", 1)
    today = date(2026, 7, 29)
    db_session.add(_due_word("solo", today))
    db_session.commit()
    _complete_review(db_session, today)

    result = get_or_start_quiz_item(db_session, day=today)
    while result.kind == "item":
        result = answer_current_quiz_item(db_session, 0, day=today)
    first_quiz_id = result.summary.quiz_id

    again = get_or_start_quiz_item(db_session, day=today)

    assert again.kind == "complete"
    assert again.summary.quiz_id == first_quiz_id
