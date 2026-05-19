from sqlalchemy import Integer, Column, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Summary(Base):  # type: ignore
    __tablename__ = 'summaries'

    summary_id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.trip_id'), nullable=False)
    user_from_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    user_to_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    value = Column(Numeric, nullable=False)

    trip = relationship('Trip')
    user_from = relationship('User', foreign_keys=[user_from_id])
    user_to = relationship('User', foreign_keys=[user_to_id])
