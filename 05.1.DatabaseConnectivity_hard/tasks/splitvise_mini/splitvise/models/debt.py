from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from .base import Base


class Debt(Base):  # type: ignore
    __tablename__ = 'debts'

    debt_id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    debtor_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    value = Column(Numeric, nullable=False)

    event = relationship('Event', back_populates='debts')
    debtor = relationship('User')
