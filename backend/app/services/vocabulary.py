import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import learner_today
from app.models.vocabulary import (
    ReviewSession,
    ReviewSessionItem,
    VocabularyWord,
)
from app.schemas.vocabulary import (
    DueQueueSummary,
    ReviewCompleteSummary,
    ReviewCurrentItem,
    ReviewOutcome,
    VocabularyWordCreate,
)
from app.services.export_utils import serialize_all

INTERVAL_DAYS = (1, 3, 7, 14, 30)


@dataclass(frozen=True)
class CurrentItemResult:
    kind: str
    item: ReviewCurrentItem | None = None


def add_word(
    session: Session,
    payload: VocabularyWordCreate,
    *,
    today: date | None = None,
) -> VocabularyWord:
    current_date = today or learner_today()
    word = VocabularyWord(
        **payload.model_dump(),
        interval_index=0,
        next_due_date=current_date + timedelta(days=INTERVAL_DAYS[0]),
    )
    session.add(word)
    session.commit()
    session.refresh(word)
    return word


def get_due_summary(
    session: Session, *, today: date | None = None
) -> DueQueueSummary:
    current_date = today or learner_today()
    due_filter = VocabularyWord.next_due_date <= current_date
    total = session.scalar(
        select(func.count(VocabularyWord.id)).where(due_filter)
    )
    interval_rows = session.execute(
        select(VocabularyWord.interval_index, func.count(VocabularyWord.id))
        .where(due_filter)
        .group_by(VocabularyWord.interval_index)
    )
    topic_name = func.coalesce(VocabularyWord.topic, "Uncategorized")
    topic_rows = session.execute(
        select(topic_name, func.count(VocabularyWord.id))
        .where(due_filter)
        .group_by(topic_name)
    )
    return DueQueueSummary(
        total_due=total or 0,
        by_interval={
            f"{INTERVAL_DAYS[index]}_{'day' if INTERVAL_DAYS[index] == 1 else 'days'}": count
            for index, count in interval_rows
        },
        by_topic={topic: count for topic, count in topic_rows},
    )


def reschedule(
    interval_index: int,
    outcome: ReviewOutcome,
    *,
    today: date | None = None,
) -> tuple[int, date]:
    current_date = today or learner_today()
    next_index = (
        0
        if outcome == ReviewOutcome.forgot
        else min(interval_index + 1, len(INTERVAL_DAYS) - 1)
    )
    return next_index, current_date + timedelta(days=INTERVAL_DAYS[next_index])


def _active_session(session: Session) -> ReviewSession | None:
    return session.scalar(
        select(ReviewSession).where(ReviewSession.completed_at.is_(None))
    )


def start_or_resume_review(
    session: Session, *, today: date | None = None
) -> ReviewSession | None:
    active = _active_session(session)
    if active is not None:
        return active

    current_date = today or learner_today()
    due_words = list(
        session.scalars(
            select(VocabularyWord)
            .where(VocabularyWord.next_due_date <= current_date)
            .order_by(VocabularyWord.next_due_date, VocabularyWord.id)
        )
    )
    if not due_words:
        return None

    review_session = ReviewSession()
    session.add(review_session)
    session.flush()
    session.add_all(
        [
            ReviewSessionItem(
                session_id=review_session.id,
                word_id=word.id,
                position=position,
            )
            for position, word in enumerate(due_words)
        ]
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        active = _active_session(session)
        if active is None:
            raise
        return active
    session.refresh(review_session)
    return review_session


def get_current_item(
    session: Session, *, today: date | None = None
) -> CurrentItemResult:
    active = _active_session(session)
    if active is None:
        due = get_due_summary(session, today=today).total_due
        return CurrentItemResult(
            kind="nothing_due" if due == 0 else "not_started"
        )

    item = session.scalar(
        select(ReviewSessionItem)
        .where(
            ReviewSessionItem.session_id == active.id,
            ReviewSessionItem.outcome.is_(None),
        )
        .order_by(ReviewSessionItem.position)
    )
    if item is None:
        return CurrentItemResult(kind="complete")

    total = session.scalar(
        select(func.count(ReviewSessionItem.id)).where(
            ReviewSessionItem.session_id == active.id
        )
    )
    return CurrentItemResult(
        kind="item",
        item=ReviewCurrentItem(
            session_id=active.id,
            item_id=item.id,
            word_id=item.word.id,
            word=item.word.word,
            meaning=item.word.meaning,
            example=item.word.example,
            position=item.position,
            total=total or 0,
        ),
    )


def assess_current_item(
    session: Session,
    outcome: ReviewOutcome,
    *,
    today: date | None = None,
) -> CurrentItemResult:
    active = _active_session(session)
    current = get_current_item(session, today=today)
    if active is None or current.kind != "item" or current.item is None:
        raise ValueError("There is no current review item")

    item = session.get(ReviewSessionItem, current.item.item_id)
    word = session.get(VocabularyWord, current.item.word_id)
    item.outcome = outcome.value
    item.assessed_at = datetime.now(timezone.utc)
    word.interval_index, word.next_due_date = reschedule(
        word.interval_index, outcome, today=today
    )
    word.last_reviewed_at = item.assessed_at
    session.flush()

    remaining = session.scalar(
        select(func.count(ReviewSessionItem.id)).where(
            ReviewSessionItem.session_id == active.id,
            ReviewSessionItem.outcome.is_(None),
        )
    )
    if remaining == 0:
        active.completed_at = datetime.now(timezone.utc)
        session.commit()
        return CurrentItemResult(kind="complete")

    session.commit()
    return get_current_item(session, today=today)


def get_review_complete_summary(
    session: Session, session_id: uuid.UUID
) -> ReviewCompleteSummary:
    rows = session.execute(
        select(ReviewSessionItem.outcome, func.count(ReviewSessionItem.id))
        .where(ReviewSessionItem.session_id == session_id)
        .group_by(ReviewSessionItem.outcome)
    )
    counts = {outcome: count for outcome, count in rows}
    forgot = counts.get(ReviewOutcome.forgot.value, 0)
    remembered = counts.get(ReviewOutcome.remembered.value, 0)
    return ReviewCompleteSummary(
        session_id=session_id,
        total_reviewed=forgot + remembered,
        forgot=forgot,
        remembered=remembered,
    )


def export_learner_data(session: Session) -> dict:
    return {
        "category": "vocabulary",
        "words": serialize_all(session, VocabularyWord),
        "review_sessions": serialize_all(session, ReviewSession),
        "review_items": serialize_all(session, ReviewSessionItem),
    }
