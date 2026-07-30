from sqlalchemy import Column, Integer, String

from app.core.db import Base


class ThrowawayRoundTripModel(Base):
    __tablename__ = "throwaway_round_trip_model"
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)


def test_write_through_one_session_reads_back_identical_through_a_fresh_session(
    db_session_factory,
):
    write_session = db_session_factory()
    write_session.add(ThrowawayRoundTripModel(id=1, value="hello"))
    write_session.commit()
    write_session.close()

    read_session = db_session_factory()
    row = read_session.get(ThrowawayRoundTripModel, 1)
    read_session.close()

    assert row is not None
    assert row.value == "hello"
