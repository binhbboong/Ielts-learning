import random
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
    VocabularyQuiz,
    VocabularyQuizItem,
    VocabularyWord,
)
from app.models.study_profile import StudyProfile
from app.schemas.vocabulary import (
    DueQueueSummary,
    QuizCompleteSummary,
    QuizCurrentItem,
    ReviewCompleteSummary,
    ReviewCurrentItem,
    ReviewOutcome,
    VocabularyWordCreate,
)
from app.services.export_utils import serialize_all, serialize_row
from app.models.user import LEGACY_USER_ID

QUIZ_PASS_THRESHOLD = 0.8
QUIZ_OPTION_COUNT = 4

INTERVAL_DAYS = (1, 3, 7, 14, 30)
DAILY_REVIEW_TARGET = 20
_PHASES = (
    ("foundation", 4.5),
    ("core_skills", 5.0),
    ("development", 5.5),
    ("consolidation", 6.0),
    ("exam_readiness", 6.5),
    ("peak_performance", 6.5),
)
_LEVEL_VOCABULARY = {
    4.5: (
        ("essential", "completely necessary", "Reliable internet is essential for remote study.", "Education"),
        ("increase", "to become greater in amount", "The chart shows an increase in energy use.", "Data description"),
        ("benefit", "a helpful or positive effect", "Public transport provides a benefit to city residents.", "Society"),
        ("factor", "one cause that influences a result", "Cost is an important factor in choosing a university.", "Education"),
        ("reduce", "to make something smaller or less", "Cycling can reduce traffic congestion.", "Environment"),
        ("require", "to need or demand something", "The course requires two hours of study each day.", "Education"),
        ("provide", "to give or supply something needed", "Local libraries provide free access to computers.", "Society"),
        ("improve", "to make or become better", "Regular practice can improve listening skills quickly.", "Education"),
        ("common", "happening or found often", "Traffic jams are common during rush hour.", "Cities"),
        ("major", "very large or important", "Pollution is a major concern for coastal cities.", "Environment"),
        ("limited", "restricted in amount or extent", "Funding for the project is limited this year.", "Government"),
        ("positive", "good, favourable, or optimistic", "The survey showed a positive attitude toward recycling.", "Environment"),
        ("negative", "bad, harmful, or unfavourable", "Noise pollution has a negative effect on sleep.", "Health"),
        ("develop", "to grow or become more advanced", "Many countries are working to develop renewable energy.", "Environment"),
        ("include", "to contain something as part of a whole", "The report includes data from five countries.", "Data description"),
        ("average", "a typical or usual amount", "The average commute takes forty minutes.", "Cities"),
        ("modern", "relating to the present time", "Modern classrooms often use digital whiteboards.", "Education"),
        ("traditional", "following long-established customs", "Traditional farming methods are still common in rural areas.", "Society"),
        ("various", "of different types", "The museum displays various artefacts from ancient cultures.", "Society"),
        ("similar", "resembling but not identical", "The two graphs show a similar upward trend.", "Data description"),
    ),
    5.0: (
        ("significant", "large or important enough to be noticed", "There was a significant rise in online learning.", "Data description"),
        ("contribute", "to help cause or produce something", "Exercise can contribute to better mental health.", "Health"),
        ("available", "able to be obtained or used", "Clean water is not equally available in every region.", "Society"),
        ("impact", "a strong effect on someone or something", "Technology has a major impact on communication.", "Technology"),
        ("maintain", "to keep something at the same level or condition", "Governments should maintain public parks.", "Environment"),
        ("considerable", "notably large in amount", "The city invested a considerable sum in public transport.", "Cities"),
        ("demonstrate", "to show clearly by giving proof", "The experiment demonstrates how heat affects growth.", "Data description"),
        ("indicate", "to point out or show", "The results indicate a steady decline in readership.", "Data description"),
        ("primary", "main or most important", "The primary cause of the delay was bad weather.", "Argumentation"),
        ("subsequent", "coming after something in time", "Subsequent studies confirmed the initial findings.", "Data description"),
        ("approach", "a way of dealing with something", "Teachers are adopting a more practical approach to science.", "Education"),
        ("context", "the situation within which something exists", "The policy makes more sense in a historical context.", "Argumentation"),
        ("establish", "to set up or bring into existence", "The university plans to establish a new research centre.", "Education"),
        ("estimate", "an approximate calculation", "Experts estimate that costs will double within a decade.", "Data description"),
        ("potential", "capable of becoming something in the future", "Solar power has huge potential in sunny regions.", "Environment"),
        ("relevant", "closely connected to the matter at hand", "Only relevant sources were included in the report.", "Argumentation"),
        ("resource", "a stock or supply that can be drawn on", "Water is a limited resource in many countries.", "Environment"),
        ("respond", "to react or answer", "Cities must respond quickly to extreme weather events.", "Cities"),
        ("statistic", "a fact expressed as a number", "The statistic shows unemployment falling for the third year.", "Data description"),
        ("trend", "a general direction in which something is developing", "The trend toward remote work continued after the pandemic.", "Work"),
    ),
    5.5: (
        ("substantial", "large in size, value, or importance", "The policy led to a substantial reduction in waste.", "Environment"),
        ("inevitable", "certain to happen and impossible to avoid", "Some degree of urban expansion is inevitable.", "Cities"),
        ("allocate", "to give something for a particular purpose", "More funding should be allocated to primary education.", "Government"),
        ("perspective", "a particular way of considering an issue", "From an economic perspective, the proposal is practical.", "Argumentation"),
        ("implement", "to put a plan or decision into effect", "Schools should implement digital literacy programmes.", "Education"),
        ("controversial", "causing public disagreement", "The new tax is a controversial topic among voters.", "Government"),
        ("derive", "to obtain something from a source", "Much of the country's income is derived from tourism.", "Society"),
        ("distinct", "recognisably different", "The two proposals have distinct advantages and drawbacks.", "Argumentation"),
        ("dominant", "most important, powerful, or influential", "English remains the dominant language of international business.", "Society"),
        ("emphasize", "to give special importance to something", "The report emphasizes the need for cleaner air.", "Environment"),
        ("equivalent", "equal in value or meaning", "One year of experience is roughly equivalent to two courses.", "Work"),
        ("fluctuate", "to rise and fall irregularly", "Oil prices tend to fluctuate throughout the year.", "Data description"),
        ("justify", "to show adequate grounds for a decision", "It is hard to justify the cost of the new stadium.", "Government"),
        ("notion", "a belief or idea about something", "The notion that money guarantees happiness is widely debated.", "Argumentation"),
        ("phenomenon", "a fact or situation observed to exist", "Urban migration is a global phenomenon.", "Cities"),
        ("proportion", "a part, share, or number in relation to a whole", "A large proportion of graduates move abroad for work.", "Data description"),
        ("reinforce", "to strengthen or support", "New evidence reinforces the theory of climate change.", "Environment"),
        ("scenario", "a possible sequence of future events", "In the worst-case scenario, sea levels could rise sharply.", "Environment"),
        ("underlying", "the fundamental cause or basis of something", "Poverty is the underlying cause of many health problems.", "Health"),
        ("widespread", "found or distributed over a large area", "Widespread flooding disrupted transport across the region.", "Environment"),
    ),
    6.0: (
        ("prevalent", "common or widespread in a particular place", "Remote work is increasingly prevalent in large companies.", "Work"),
        ("detrimental", "causing harm or damage", "Excessive screen time can be detrimental to sleep quality.", "Health"),
        ("facilitate", "to make an action or process easier", "Public libraries facilitate access to reliable information.", "Education"),
        ("disparity", "an unfair or noticeable difference", "The data reveals a disparity between urban and rural incomes.", "Society"),
        ("sustainable", "able to continue without exhausting resources", "Cities need sustainable transport systems.", "Environment"),
        ("accumulate", "to gather together over time", "Plastic waste continues to accumulate in the ocean.", "Environment"),
        ("ambiguous", "open to more than one interpretation", "The instructions were ambiguous and confused many students.", "Education"),
        ("coherent", "logical and consistent", "A coherent argument requires well-organised evidence.", "Argumentation"),
        ("comprehensive", "complete and including everything necessary", "The report offers a comprehensive review of the industry.", "Data description"),
        ("constrain", "to restrict or limit", "Limited budgets constrain what schools can offer students.", "Education"),
        ("correlate", "to have a mutual relationship", "Income level appears to correlate with life expectancy.", "Health"),
        ("deteriorate", "to become progressively worse", "Air quality continues to deteriorate in industrial cities.", "Environment"),
        ("empirical", "based on observation or experience", "The claim lacks empirical support from controlled studies.", "Data description"),
        ("hypothesis", "a proposed explanation based on limited evidence", "Researchers tested the hypothesis with a large sample.", "Data description"),
        ("inherent", "existing as a natural part of something", "There is an inherent risk in relying on a single supplier.", "Argumentation"),
        ("paradox", "a situation with contradictory but true elements", "It is a paradox that wealthier nations often waste more food.", "Argumentation"),
        ("plausible", "seeming reasonable or probable", "A more plausible explanation involves changes in diet.", "Health"),
        ("rigorous", "thorough, careful, and exact", "The study followed a rigorous testing procedure.", "Data description"),
        ("subsequently", "after a particular event", "The factory closed and subsequently many jobs were lost.", "Work"),
        ("viable", "capable of working successfully", "Wind power is a viable alternative in coastal regions.", "Environment"),
    ),
    6.5: (
        ("exacerbate", "to make a problem or bad situation worse", "Poor planning may exacerbate housing shortages.", "Cities"),
        ("mitigate", "to make something harmful less severe", "Green spaces can mitigate the effects of air pollution.", "Environment"),
        ("undermine", "to gradually make something weaker", "Misinformation can undermine public trust.", "Media"),
        ("compelling", "convincing and able to attract strong interest", "There is compelling evidence for early intervention.", "Argumentation"),
        ("proliferation", "a rapid increase in the number of something", "The proliferation of smartphones has changed social interaction.", "Technology"),
        ("ambivalent", "having mixed feelings about something", "Many residents feel ambivalent about the new development.", "Cities"),
        ("anomaly", "something that deviates from the standard", "The unusually cold summer was treated as a statistical anomaly.", "Data description"),
        ("discrepancy", "a lack of compatibility between facts", "There is a discrepancy between the two survey results.", "Data description"),
        ("entrenched", "firmly established and difficult to change", "Gender roles remain entrenched in some industries.", "Society"),
        ("equitable", "fair and impartial", "The reform aims to create a more equitable tax system.", "Government"),
        ("impede", "to delay or prevent progress", "Bureaucracy can impede the rollout of new technology.", "Government"),
        ("inadvertently", "without intention; accidentally", "The policy inadvertently increased costs for small businesses.", "Government"),
        ("juxtapose", "to place side by side for comparison", "The exhibition juxtaposes historical and modern artwork.", "Media"),
        ("meticulous", "showing great attention to detail", "The audit required a meticulous review of every transaction.", "Work"),
        ("nuanced", "characterized by subtle distinctions", "The documentary offers a nuanced view of the conflict.", "Media"),
        ("pervasive", "spreading widely throughout an area", "Smartphone use has become pervasive among teenagers.", "Technology"),
        ("precarious", "not securely held or in position", "Many gig workers face a precarious financial situation.", "Work"),
        ("substantiate", "to provide evidence to support a claim", "The lawyer failed to substantiate the allegations.", "Argumentation"),
        ("tangible", "able to be perceived, especially by touch", "The investment produced tangible improvements in literacy.", "Education"),
        ("unprecedented", "never done or known before", "The heatwave brought unprecedented demand for electricity.", "Environment"),
    ),
}


@dataclass(frozen=True)
class CurrentItemResult:
    kind: str
    item: ReviewCurrentItem | None = None


def add_word(
    session: Session,
    payload: VocabularyWordCreate,
    *,
    today: date | None = None,
    user_id=LEGACY_USER_ID,
    target_band: float | None = None,
    cefr_level: str | None = None,
    source: str = "manual",
) -> VocabularyWord:
    current_date = today or learner_today()
    word = VocabularyWord(
        user_id=user_id,
        **payload.model_dump(),
        target_band=target_band,
        cefr_level=cefr_level,
        source=source,
        interval_index=0,
        next_due_date=current_date + timedelta(days=INTERVAL_DAYS[0]),
    )
    session.add(word)
    session.commit()
    session.refresh(word)
    return word


def _cefr_for_band(band: float) -> str:
    if band < 4.0:
        return "A2"
    if band < 5.5:
        return "B1"
    if band < 6.5:
        return "B2"
    return "C1"


def learner_level_context(
    session: Session, user_id, *, today: date | None = None
) -> tuple[int, str, float, str]:
    current_date = today or learner_today()
    profile = session.get(StudyProfile, user_id)
    if profile is None:
        profile = StudyProfile(
            user_id=user_id,
            exam_type="ielts_academic",
            baseline_band=3.5,
            target_band=6.5,
            minimum_skill_band=6.0,
            start_date=current_date,
            target_date=current_date + timedelta(weeks=24),
            daily_minutes=60,
            study_days_per_week=5,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
    week = max(1, min(24, ((current_date - profile.start_date).days // 7) + 1))
    phase_index = min(5, (week - 1) // 4)
    phase, phase_band = _PHASES[phase_index]
    band = min(profile.target_band, phase_band)
    return week, phase, band, _cefr_for_band(band)


def _band_recommendation_candidates(
    session: Session, user_id, band: float, cefr: str
) -> list[dict]:
    existing = {
        value.casefold()
        for value in session.scalars(
            select(VocabularyWord.word).where(VocabularyWord.user_id == user_id)
        )
    }
    words = _LEVEL_VOCABULARY[band]
    return [
        {
            "key": f"{band}:{word}",
            "word": word,
            "meaning": meaning,
            "example": example,
            "topic": topic,
            "target_band": band,
            "cefr_level": cefr,
        }
        for word, meaning, example, topic in words
        if word.casefold() not in existing
    ]


def get_level_recommendations(
    session: Session, user_id=LEGACY_USER_ID, *, today: date | None = None
) -> dict:
    week, phase, band, cefr = learner_level_context(session, user_id, today=today)
    recommendations = _band_recommendation_candidates(session, user_id, band, cefr)
    return {
        "current_band": band,
        "cefr_level": cefr,
        "phase": phase,
        "week": week,
        "recommendations": recommendations,
    }


def _backfill_daily_words(
    session: Session,
    user_id,
    needed: int,
    *,
    today: date,
) -> list[VocabularyWord]:
    if needed <= 0:
        return []
    _week, _phase, band, cefr = learner_level_context(session, user_id, today=today)
    candidates = _band_recommendation_candidates(session, user_id, band, cefr)
    created = []
    for recommendation in candidates[:needed]:
        word = VocabularyWord(
            user_id=user_id,
            word=recommendation["word"],
            meaning=recommendation["meaning"],
            example=recommendation["example"],
            topic=recommendation["topic"],
            target_band=recommendation["target_band"],
            cefr_level=recommendation["cefr_level"],
            source="daily_backfill",
            interval_index=0,
            next_due_date=today,
        )
        session.add(word)
        created.append(word)
    if created:
        session.flush()
    return created


def _daily_backfill_preview(
    session: Session, user_id, today: date, total_due: int
) -> tuple[int, bool]:
    # Mirrors start_or_resume_review's own gate: backfill happens at most once per
    # calendar day, so once today's session exists (active or completed) there's
    # nothing left to preview.
    if _active_session(session, user_id, today) is None and _session_for_day(
        session, user_id, today
    ) is not None:
        return 0, False
    needed = max(0, DAILY_REVIEW_TARGET - total_due)
    if needed <= 0:
        return 0, False
    _week, _phase, band, cefr = learner_level_context(session, user_id, today=today)
    candidates = _band_recommendation_candidates(session, user_id, band, cefr)
    backfill_count = min(needed, len(candidates))
    return backfill_count, backfill_count < needed


def add_level_recommendation(
    session: Session,
    key: str,
    user_id=LEGACY_USER_ID,
    *,
    today: date | None = None,
) -> VocabularyWord:
    feed = get_level_recommendations(session, user_id, today=today)
    recommendation = next(
        (item for item in feed["recommendations"] if item["key"] == key), None
    )
    if recommendation is None:
        raise ValueError("Recommendation not found or already added")
    payload = VocabularyWordCreate(
        word=recommendation["word"],
        meaning=recommendation["meaning"],
        example=recommendation["example"],
        topic=recommendation["topic"],
    )
    return add_word(
        session,
        payload,
        today=today,
        user_id=user_id,
        target_band=recommendation["target_band"],
        cefr_level=recommendation["cefr_level"],
        source="level_recommendation",
    )


def get_due_summary(
    session: Session, *, today: date | None = None, user_id=LEGACY_USER_ID
) -> DueQueueSummary:
    current_date = today or learner_today()
    due_filter = (
        (VocabularyWord.user_id == user_id)
        & (VocabularyWord.next_due_date <= current_date)
    )
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
    total_due = total or 0
    backfill_count, shortfall = _daily_backfill_preview(
        session, user_id, current_date, total_due
    )
    return DueQueueSummary(
        total_due=total_due,
        by_interval={
            f"{INTERVAL_DAYS[index]}_{'day' if INTERVAL_DAYS[index] == 1 else 'days'}": count
            for index, count in interval_rows
        },
        by_topic={topic: count for topic, count in topic_rows},
        daily_target=DAILY_REVIEW_TARGET,
        backfill_count=backfill_count,
        shortfall=shortfall,
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


def _active_session(
    session: Session, user_id=LEGACY_USER_ID, day: date | None = None
) -> ReviewSession | None:
    target_day = day or learner_today()
    return session.scalar(
        select(ReviewSession).where(
            ReviewSession.user_id == user_id,
            ReviewSession.day == target_day,
            ReviewSession.completed_at.is_(None),
        )
    )


def _session_for_day(
    session: Session, user_id, day: date
) -> ReviewSession | None:
    return session.scalar(
        select(ReviewSession).where(
            ReviewSession.user_id == user_id,
            ReviewSession.day == day,
        )
    )


def start_or_resume_review(
    session: Session, *, today: date | None = None, user_id=LEGACY_USER_ID
) -> ReviewSession | None:
    current_date = today or learner_today()
    active = _active_session(session, user_id, current_date)
    if active is not None:
        return active

    if _session_for_day(session, user_id, current_date) is not None:
        # Today's session (whether due-only or backfilled) already ran and
        # completed — backfill happens at most once per calendar day.
        return None

    due_words = list(
        session.scalars(
            select(VocabularyWord)
            .where(
                VocabularyWord.user_id == user_id,
                VocabularyWord.next_due_date <= current_date,
            )
            .order_by(VocabularyWord.next_due_date, VocabularyWord.id)
        )
    )
    backfilled = _backfill_daily_words(
        session, user_id, DAILY_REVIEW_TARGET - len(due_words), today=current_date
    )
    queue_words = due_words + backfilled
    if not queue_words:
        return None

    review_session = ReviewSession(user_id=user_id, day=current_date)
    session.add(review_session)
    session.flush()
    session.add_all(
        [
            ReviewSessionItem(
                session_id=review_session.id,
                word_id=word.id,
                position=position,
            )
            for position, word in enumerate(queue_words)
        ]
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        active = _active_session(session, user_id, current_date)
        if active is None:
            raise
        return active
    session.refresh(review_session)
    return review_session


def get_current_item(
    session: Session, *, today: date | None = None, user_id=LEGACY_USER_ID
) -> CurrentItemResult:
    current_date = today or learner_today()
    active = _active_session(session, user_id, current_date)
    if active is None:
        summary = get_due_summary(session, today=today, user_id=user_id)
        nothing_to_review = summary.total_due == 0 and summary.backfill_count == 0
        return CurrentItemResult(
            kind="nothing_due" if nothing_to_review else "not_started"
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
            is_new=item.word.source == "daily_backfill",
        ),
    )


def assess_current_item(
    session: Session,
    outcome: ReviewOutcome,
    *,
    today: date | None = None,
    user_id=LEGACY_USER_ID,
) -> CurrentItemResult:
    current_date = today or learner_today()
    active = _active_session(session, user_id, current_date)
    current = get_current_item(session, today=current_date, user_id=user_id)
    if active is None or current.kind != "item" or current.item is None:
        raise ValueError("There is no current review item")

    item = session.get(ReviewSessionItem, current.item.item_id)
    word = session.get(VocabularyWord, current.item.word_id)
    item.outcome = outcome.value
    item.assessed_at = datetime.now(timezone.utc)
    word.interval_index, word.next_due_date = reschedule(
        word.interval_index, outcome, today=current_date
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
    return get_current_item(session, today=current_date, user_id=user_id)


def get_review_complete_summary(
    session: Session, session_id: uuid.UUID, user_id=LEGACY_USER_ID
) -> ReviewCompleteSummary:
    owned = session.query(ReviewSession).filter_by(id=session_id, user_id=user_id).one_or_none()
    if owned is None:
        raise ValueError("Review session not found")
    rows = session.execute(
        select(ReviewSessionItem.outcome, func.count(ReviewSessionItem.id))
        .where(ReviewSessionItem.session_id == session_id)
        .group_by(ReviewSessionItem.outcome)
    )
    counts = {outcome: count for outcome, count in rows}
    forgot = counts.get(ReviewOutcome.forgot.value, 0)
    remembered = counts.get(ReviewOutcome.remembered.value, 0)
    new_words_included = session.scalar(
        select(func.count(ReviewSessionItem.id))
        .join(VocabularyWord, ReviewSessionItem.word_id == VocabularyWord.id)
        .where(
            ReviewSessionItem.session_id == session_id,
            VocabularyWord.source == "daily_backfill",
        )
    )
    return ReviewCompleteSummary(
        session_id=session_id,
        total_reviewed=forgot + remembered,
        forgot=forgot,
        remembered=remembered,
        new_words_included=new_words_included or 0,
    )


@dataclass(frozen=True)
class HistoryDayWord:
    word: str
    meaning: str


@dataclass(frozen=True)
class HistoryDayReview:
    word: str
    outcome: str
    assessed_at: datetime


@dataclass(frozen=True)
class HistoryDay:
    day: date
    words_added: list
    words_reviewed: list


def get_history(session: Session, user_id=LEGACY_USER_ID) -> list[HistoryDay]:
    words = (
        session.query(VocabularyWord)
        .filter(VocabularyWord.user_id == user_id)
        .order_by(VocabularyWord.created_at)
        .all()
    )
    items = (
        session.query(ReviewSessionItem)
        .join(ReviewSession, ReviewSessionItem.session_id == ReviewSession.id)
        .filter(
            ReviewSession.user_id == user_id,
            ReviewSessionItem.assessed_at.isnot(None),
        )
        .order_by(ReviewSessionItem.assessed_at)
        .all()
    )

    buckets: dict[date, dict] = {}

    def bucket(day_value: date) -> dict:
        return buckets.setdefault(
            day_value, {"words_added": [], "words_reviewed": []}
        )

    for word in words:
        bucket(learner_today(now=word.created_at))["words_added"].append(
            HistoryDayWord(word=word.word, meaning=word.meaning)
        )

    for item in items:
        bucket(learner_today(now=item.assessed_at))["words_reviewed"].append(
            HistoryDayReview(
                word=item.word.word, outcome=item.outcome, assessed_at=item.assessed_at
            )
        )

    return [
        HistoryDay(day=day_value, **content)
        for day_value, content in sorted(buckets.items(), reverse=True)
    ]


def export_learner_data(session: Session, user_id=LEGACY_USER_ID) -> dict:
    return {
        "category": "vocabulary",
        "words": serialize_all(session, VocabularyWord, user_id),
        "review_sessions": serialize_all(session, ReviewSession, user_id),
        "review_items": [
            serialize_row(item)
            for item in session.query(ReviewSessionItem)
            .join(ReviewSession)
            .filter(ReviewSession.user_id == user_id)
            .all()
        ],
    }


@dataclass(frozen=True)
class QuizItemResult:
    kind: str
    item: QuizCurrentItem | None = None
    summary: QuizCompleteSummary | None = None


def _quiz_summary(quiz: VocabularyQuiz) -> QuizCompleteSummary:
    total = quiz.total or 0
    correct = quiz.correct or 0
    passed = total > 0 and (correct / total) >= QUIZ_PASS_THRESHOLD
    return QuizCompleteSummary(
        quiz_id=quiz.id, correct=correct, total=total, passed=passed
    )


def _build_quiz_options(
    session: Session, user_id, word: VocabularyWord, other_words: list[VocabularyWord]
) -> tuple[list[str], int]:
    same_level = list(
        session.scalars(
            select(VocabularyWord).where(
                VocabularyWord.user_id == user_id,
                VocabularyWord.id != word.id,
                VocabularyWord.cefr_level == word.cefr_level,
            )
        )
    )
    random.shuffle(same_level)
    distractor_pool = list(same_level)
    fallback = [w for w in other_words if w.id != word.id]
    random.shuffle(fallback)
    for candidate in fallback:
        if candidate not in distractor_pool:
            distractor_pool.append(candidate)

    distractors = distractor_pool[: QUIZ_OPTION_COUNT - 1]
    entries = [(word.meaning, True)] + [(w.meaning, False) for w in distractors]
    random.shuffle(entries)
    options = [meaning for meaning, _ in entries]
    correct_option_index = next(
        index for index, (_, is_correct) in enumerate(entries) if is_correct
    )
    return options, correct_option_index


def _build_quiz(session: Session, user_id, day: date) -> VocabularyQuiz | None:
    day_session = _session_for_day(session, user_id, day)
    if day_session is None or day_session.completed_at is None:
        return None

    session_items = (
        session.query(ReviewSessionItem)
        .filter_by(session_id=day_session.id)
        .order_by(ReviewSessionItem.position)
        .all()
    )
    words = [item.word for item in session_items]
    if not words:
        return None

    quiz = VocabularyQuiz(user_id=user_id, day=day)
    session.add(quiz)
    session.flush()

    shuffled_words = list(words)
    random.shuffle(shuffled_words)
    quiz_items = []
    for position, word in enumerate(shuffled_words):
        options, correct_option_index = _build_quiz_options(
            session, user_id, word, words
        )
        quiz_items.append(
            VocabularyQuizItem(
                quiz_id=quiz.id,
                word_id=word.id,
                position=position,
                options=options,
                correct_option_index=correct_option_index,
            )
        )
    session.add_all(quiz_items)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = (
            session.query(VocabularyQuiz).filter_by(user_id=user_id, day=day).one_or_none()
        )
        if existing is None:
            raise
        return existing
    session.refresh(quiz)
    return quiz


def get_or_start_quiz_item(
    session: Session, *, day: date, user_id=LEGACY_USER_ID
) -> QuizItemResult:
    quiz = session.query(VocabularyQuiz).filter_by(user_id=user_id, day=day).one_or_none()
    if quiz is None:
        quiz = _build_quiz(session, user_id, day)
        if quiz is None:
            return QuizItemResult(kind="not_ready")

    if quiz.submitted_at is not None:
        return QuizItemResult(kind="complete", summary=_quiz_summary(quiz))

    item = (
        session.query(VocabularyQuizItem)
        .filter(
            VocabularyQuizItem.quiz_id == quiz.id,
            VocabularyQuizItem.selected_option_index.is_(None),
        )
        .order_by(VocabularyQuizItem.position)
        .first()
    )
    if item is None:
        return _finalize_quiz(session, quiz)

    total = session.scalar(
        select(func.count(VocabularyQuizItem.id)).where(
            VocabularyQuizItem.quiz_id == quiz.id
        )
    )
    return QuizItemResult(
        kind="item",
        item=QuizCurrentItem(
            quiz_id=quiz.id,
            item_id=item.id,
            word=item.word.word,
            options=item.options,
            position=item.position,
            total=total or 0,
        ),
    )


def _finalize_quiz(session: Session, quiz: VocabularyQuiz) -> QuizItemResult:
    items = session.query(VocabularyQuizItem).filter_by(quiz_id=quiz.id).all()
    total = len(items)
    correct = sum(
        1 for item in items if item.selected_option_index == item.correct_option_index
    )
    quiz.total = total
    quiz.correct = correct
    quiz.submitted_at = datetime.now(timezone.utc)
    session.commit()
    return QuizItemResult(kind="complete", summary=_quiz_summary(quiz))


def answer_current_quiz_item(
    session: Session,
    selected_option_index: int,
    *,
    day: date,
    user_id=LEGACY_USER_ID,
) -> QuizItemResult:
    current = get_or_start_quiz_item(session, day=day, user_id=user_id)
    if current.kind != "item" or current.item is None:
        raise ValueError("There is no current quiz item")

    item = session.get(VocabularyQuizItem, current.item.item_id)
    item.selected_option_index = selected_option_index
    session.flush()

    quiz = session.get(VocabularyQuiz, current.item.quiz_id)
    remaining = session.scalar(
        select(func.count(VocabularyQuizItem.id)).where(
            VocabularyQuizItem.quiz_id == quiz.id,
            VocabularyQuizItem.selected_option_index.is_(None),
        )
    )
    if remaining == 0:
        return _finalize_quiz(session, quiz)

    session.commit()
    return get_or_start_quiz_item(session, day=day, user_id=user_id)


def get_quiz_result(
    session: Session, day: date, user_id=LEGACY_USER_ID
) -> QuizCompleteSummary | None:
    quiz = (
        session.query(VocabularyQuiz)
        .filter_by(user_id=user_id, day=day)
        .one_or_none()
    )
    if quiz is None or quiz.submitted_at is None:
        return None
    return _quiz_summary(quiz)
