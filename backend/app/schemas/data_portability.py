import uuid
from datetime import datetime

from pydantic import BaseModel


class ExportDocument(BaseModel):
    export_format_version: int
    export_id: uuid.UUID
    produced_at: datetime
    complete: bool
    category_count: int
    categories: list[str]
    data: dict[str, dict]


class ExportFailure(BaseModel):
    status: str = "error"
    message: str
    retryable: bool = True
