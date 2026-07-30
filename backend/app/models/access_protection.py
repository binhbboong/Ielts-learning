from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False)
