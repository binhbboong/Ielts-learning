from types import SimpleNamespace

import pytest

from app.services.practice_trend import (
    average_score_percentage,
    compute_trend,
    rank_missed_question_types,
    threshold_status,
    trend_direction,
)


def test_average_score_normalizes_results_with_different_totals():
    rows = [
        SimpleNamespace(score=30, total=40),
        SimpleNamespace(score=15, total=20),
    ]

    assert average_score_percentage(rows) == pytest.approx(75.0)


def test_average_score_returns_none_for_zero_rows():
    assert average_score_percentage([]) is None


@pytest.mark.parametrize(
    "recent_score,expected",
    [(52.5, "up"), (52.49, "steady"), (47.5, "down")],
)
def test_trend_direction_uses_two_point_five_percentage_point_threshold(
    recent_score, expected
):
    rows = [
        SimpleNamespace(score=5000, total=10000, logged_at=1),
        SimpleNamespace(score=5000, total=10000, logged_at=2),
        SimpleNamespace(
            score=int(recent_score * 100), total=10000, logged_at=3
        ),
        SimpleNamespace(
            score=int(recent_score * 100), total=10000, logged_at=4
        ),
    ]

    assert trend_direction(rows) == expected


def test_trend_direction_assigns_odd_session_to_recent_half():
    rows = [
        SimpleNamespace(score=50, total=100, logged_at=1),
        SimpleNamespace(score=50, total=100, logged_at=2),
        SimpleNamespace(score=55, total=100, logged_at=3),
        SimpleNamespace(score=55, total=100, logged_at=4),
        SimpleNamespace(score=55, total=100, logged_at=5),
    ]

    assert trend_direction(rows) == "up"


@pytest.mark.parametrize(
    "count,remaining",
    [(0, 4), (1, 3), (2, 2)],
)
def test_threshold_reports_insufficient_below_three(count, remaining):
    status = threshold_status(count)

    assert status.sufficient is False
    assert status.count == count
    assert status.remaining == remaining


def test_threshold_exactly_three_is_insufficient():
    status = threshold_status(3)

    assert status.sufficient is False
    assert status.count == 3
    assert status.remaining == 1


def test_threshold_exactly_four_is_sufficient():
    status = threshold_status(4)

    assert status.sufficient is True
    assert status.count == 4
    assert status.remaining == 0


def test_breakdown_groups_and_ranks_all_occurrences():
    rows = [
        SimpleNamespace(
            missed_question_types=["matching_headings", "multiple_choice"]
        ),
        SimpleNamespace(
            missed_question_types=["matching_headings", "sentence_completion"]
        ),
        SimpleNamespace(missed_question_types=["multiple_choice"]),
    ]

    breakdown = rank_missed_question_types(rows)

    assert [(entry.key, entry.count) for entry in breakdown] == [
        ("matching_headings", 2),
        ("multiple_choice", 2),
        ("sentence_completion", 1),
    ]


def test_breakdown_works_below_threshold_and_for_zero_rows():
    one_row = [
        SimpleNamespace(missed_question_types=["short_answer_questions"])
    ]

    assert [
        (entry.key, entry.count)
        for entry in rank_missed_question_types(one_row)
    ] == [("short_answer_questions", 1)]
    assert rank_missed_question_types([]) == []


@pytest.mark.parametrize("count", [0, 3, 4, 8])
def test_combined_trend_always_contains_threshold_and_breakdown(count):
    rows = [
        SimpleNamespace(
            score=20 + index,
            total=40,
            logged_at=index,
            missed_question_types=["multiple_choice"],
        )
        for index in range(count)
    ]

    result = compute_trend(rows)

    assert result.threshold.count == count
    assert result.breakdown == (
        [] if count == 0 else [result.breakdown[0]]
    )
    if count < 4:
        assert result.direction is None
    else:
        assert result.direction in {"up", "steady", "down"}
