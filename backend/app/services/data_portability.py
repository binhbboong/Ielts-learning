import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.schemas.data_portability import ExportDocument
from app.models.user import LEGACY_USER_ID
from app.services import (
    listening_practice,
    mistake,
    practice_result,
    reading_practice,
    speaking_coach,
    vocabulary,
    writing_coach,
)

ExportSource = Callable[[Session, uuid.UUID], dict]

EXPORT_SOURCES: list[ExportSource] = [
    vocabulary.export_learner_data,
    mistake.export_learner_data,
    practice_result.export_learner_data,
    writing_coach.export_learner_data,
    speaking_coach.export_learner_data,
    reading_practice.export_learner_data,
    listening_practice.export_learner_data,
]

REQUIRED_CATEGORIES = (
    "vocabulary",
    "mistakes",
    "practice_results",
    "writing_submissions",
    "speaking_submissions",
    "reading_practice",
    "listening_practice",
)


class ExportAssemblyError(RuntimeError):
    pass


def assemble_export(
    db: Session, user_id: uuid.UUID = LEGACY_USER_ID
) -> ExportDocument:
    data: dict[str, dict] = {}
    for source in EXPORT_SOURCES:
        result = source(db, user_id)
        if not isinstance(result, dict) or not isinstance(result.get("category"), str):
            raise ExportAssemblyError("Every export source must return a category-tagged dict")
        category = result["category"]
        if category in data:
            raise ExportAssemblyError(f"Duplicate export category: {category}")
        data[category] = {
            key: value for key, value in result.items() if key != "category"
        }
    missing = set(REQUIRED_CATEGORIES) - set(data)
    if missing:
        raise ExportAssemblyError(
            f"Export incomplete; missing categories: {', '.join(sorted(missing))}"
        )
    categories = list(REQUIRED_CATEGORIES)
    return ExportDocument(
        export_format_version=1,
        export_id=uuid.uuid4(),
        produced_at=datetime.now(timezone.utc),
        complete=True,
        category_count=len(categories),
        categories=categories,
        data=data,
    )
