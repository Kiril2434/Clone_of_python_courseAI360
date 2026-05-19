from sqlalchemy import Integer, Column, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship

from .base import Base


class Event(Base):  # type: ignore
    __tablename__ = 'events'

    event_id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.trip_id'), nullable=False)
    title = Column(String, nullable=False)
    settled_up = Column(Boolean, nullable=False, default=False)

    trip = relationship('Trip', back_populates='events')
    expenses = relationship('Expense', back_populates='event')
    debts = relationship('Debt', back_populates='event')
