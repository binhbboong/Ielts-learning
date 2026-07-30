import base64
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import inspect


def json_value(value):
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def serialize_row(value) -> dict:
    return {
        column.key: json_value(getattr(value, column.key))
        for column in inspect(value).mapper.column_attrs
    }


def serialize_all(db, model) -> list[dict]:
    return [serialize_row(row) for row in db.query(model).all()]
