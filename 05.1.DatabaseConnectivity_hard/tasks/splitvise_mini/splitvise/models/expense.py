from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Expense(Base):  # type: ignore
    __tablename__ = 'expenses'

    expense_id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    payer_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    value = Column(Numeric, nullable=False)

    event = relationship('Event', back_populates='expenses')
    payer = relationship('User')
