import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.db import Base
from app.models.user import LEGACY_USER_ID, User

test_engine = create_engine(settings.TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _seed_legacy_user():
    with TestSessionLocal() as session:
        if session.get(User, LEGACY_USER_ID) is None:
            session.add(
                User(
                    id=LEGACY_USER_ID,
                    email="learner@legacy.local",
                    display_name="Legacy learner",
                    password_hash="unused",
                )
            )
            session.commit()


@pytest.fixture()
def db_session():
    """A single session against the real test database, tables created fresh per test."""
    Base.metadata.create_all(bind=test_engine)
    _seed_legacy_user()
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session_factory():
    """Yields TestSessionLocal itself, so a test can open multiple independent sessions
    against the real test database to prove data round-trips across sessions, not just
    within one session's identity map."""
    Base.metadata.create_all(bind=test_engine)
    _seed_legacy_user()
    try:
        yield TestSessionLocal
    finally:
        Base.metadata.drop_all(bind=test_engine)
