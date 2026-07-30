from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Every model in the project inherits from this. Shared by every epic."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
