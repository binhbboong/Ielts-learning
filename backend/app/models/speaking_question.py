import uuid

from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SpeakingQuestion(Base):
    __tablename__ = "speaking_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    part: Mapped[str] = mapped_column(String(6), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
