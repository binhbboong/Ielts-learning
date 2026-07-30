from collections import Counter
from dataclasses import dataclass
from typing import Protocol


class HasMissedQuestionTypes(Protocol):
    missed_question_types: list[str]


class HasScore(Protocol):
    score: int
    total: int
    logged_at: object


@dataclass(frozen=True)
class ThresholdStatus:
    sufficient: bool
    count: int
    remaining: int


@dataclass(frozen=True)
class BreakdownEntry:
    key: str
    count: int


@dataclass(frozen=True)
class CombinedTrend:
    session_count: int
    average_score_percentage: float | None
    direction: str | None
    threshold: ThresholdStatus
    breakdown: list[BreakdownEntry]


def average_score_percentage(rows: list[HasScore]) -> float | None:
    if not rows:
        return None
    return sum(row.score / row.total * 100 for row in rows) / len(rows)


def trend_direction(rows: list[HasScore]) -> str:
    ordered = sorted(rows, key=lambda row: row.logged_at)
    midpoint = len(ordered) // 2
    earlier = average_score_percentage(ordered[:midpoint])
    recent = average_score_percentage(ordered[midpoint:])
    if earlier is None or recent is None:
        return "steady"
    delta = recent - earlier
    if delta >= 2.5 - 1e-9:
        return "up"
    if delta <= -2.5 + 1e-9:
        return "down"
    return "steady"


def threshold_status(count: int) -> ThresholdStatus:
    return ThresholdStatus(
        sufficient=count >= 4,
        count=count,
        remaining=max(0, 4 - count),
    )


def rank_missed_question_types(
    rows: list[HasMissedQuestionTypes],
) -> list[BreakdownEntry]:
    counts = Counter(
        question_type
        for row in rows
        for question_type in row.missed_question_types
    )
    return [
        BreakdownEntry(key=key, count=count)
        for key, count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def compute_trend(rows: list[HasScore]) -> CombinedTrend:
    threshold = threshold_status(len(rows))
    return CombinedTrend(
        session_count=len(rows),
        average_score_percentage=average_score_percentage(rows),
        direction=trend_direction(rows) if threshold.sufficient else None,
        threshold=threshold,
        breakdown=rank_missed_question_types(rows),
    )
