import typing as tp
from decimal import Decimal

from sqlalchemy import select

from .models.base import Session
from .models import User, Expense, Trip, Debt, Event, Summary
from .exceptions import SplitViseException

MoneyType = Decimal


def create_user(
        username: str,
        *,
        session: Session
) -> User:
    """
    Create new User; validate user exists
    :param username: username to create
    :param session: active session to perform operations with
    :return: orm User object
    :exception: username already taken
    """
    existing = session.execute(select(User).where(User.username == username)).scalar()
    if existing is not None:
        raise SplitViseException(f"Username {username} already taken")
    user = User(username=username)
    session.add(user)
    session.commit()
    return user


def create_event(
        trip_id: int,
        people_debt: tp.Mapping[int, MoneyType],
        people_payment: tp.Mapping[int, MoneyType],
        title: str,
        *,
        session: Session
) -> Event:
    """
    Create Event in database, automatically creates Debts and Expenses; validates sum
    :param trip_id: Trip.trip_id from the database
    :param people_debt: mapping of User.user_id to theirs debt in that event
    :param people_payment: mapping of User.user_id to theirs payments in that event
    :param title: title of the event
    :param session: active session to perform operations with
    :return: orm Event object
    :exception: Trip not found by id, Can not create debt for user not in trip,
                Can not create payment for user not in trip, Sum of debts and sum of payments are not equal
    """
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise SplitViseException(f"Trip not found by id {trip_id}")

    trip_user_ids = {u.user_id for u in trip.users}

    if not people_debt or not people_payment:
        raise SplitViseException("Empty debts or payments")

    for user_id in people_debt:
        if user_id not in trip_user_ids:
            raise SplitViseException(f"Can not create debt for user {user_id} not in trip")

    for user_id in people_payment:
        if user_id not in trip_user_ids:
            raise SplitViseException(f"Can not create payment for user {user_id} not in trip")

    debt_sum = sum(people_debt.values())
    payment_sum = sum(people_payment.values())
    if debt_sum != payment_sum:
        raise SplitViseException("Sum of debts and sum of payments are not equal")

    event = Event(trip_id=trip_id, title=title, settled_up=False)
    session.add(event)
    session.flush()

    for user_id, value in people_payment.items():
        session.add(Expense(event_id=event.event_id, payer_id=user_id, value=value))

    for user_id, value in people_debt.items():
        session.add(Debt(event_id=event.event_id, debtor_id=user_id, value=value))

    session.commit()
    return event


def create_trip(
        creator_id: int,
        title: str,
        description: str,
        *,
        session: Session
) -> Trip:
    """
    Create Trip. Automatically add creator to the trip. Validate input: the title should not be empty and the creator
    should exist in the users table
    :param creator_id: User.user_id from the database to create trip by
    :param title: Title of the trip
    :param description: Long (or not so long) description of the trip
    :param session: active session to perform operations with
    :return: orm Trip object
    :exception: Title of a trip should not be empty, User not found by id
    """
    if not title:
        raise SplitViseException("Title of a trip should not be empty")

    creator = session.get(User, creator_id)
    if creator is None:
        raise SplitViseException(f"User not found by id {creator_id}")

    trip = Trip(title=title, description=description)
    trip.users.append(creator)
    session.add(trip)
    session.commit()
    return trip


def add_user_to_trip(
        guest_id: int,
        trip_id: int,
        *,
        session: Session
) -> None:
    """
    Mark that the user with guest_id takes part in the trip. Check that the user and the trip do exist and the user has
    not been added to the trip yet.
    :param guest_id: User.user_id from the database to add to the trip
    :param trip_id: Trip.trip_id from the database
    :param session: active session to perform operations with
    :return: None
    :exception: Trip not found by id, User already in trip
    """
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise SplitViseException(f"Trip not found by id {trip_id}")

    guest = session.get(User, guest_id)
    if guest is None:
        raise SplitViseException(f"User not found by id {guest_id}")

    if guest in trip.users:
        raise SplitViseException(f"User {guest_id} already in trip")

    trip.users.append(guest)
    session.commit()


def get_trip_users(
        trip_id: int,
        *,
        session: Session
) -> list[User]:
    """
    Get Users from Trip; validate Trip exists
    :param trip_id: Trip.trip_id from the database
    :param session: active session to perform operations with
    :return: list of orm User objects
    :exception: Trip not found by id
    """
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise SplitViseException(f"Trip not found by id {trip_id}")
    return list(trip.users)


def make_summary(
        trip_id: int,
        *,
        session: Session
) -> None:
    """
    Make trip summary. Mark all the events of the trip as settled up. Validate at least the existence of the trip
    being calculated
    :param trip_id: Trip.trip_id from the database
    :param session: active session to perform operations with
    :return: None
    :exception: Trip not found by id
    """
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise SplitViseException(f"Trip not found by id {trip_id}")

    balances: dict[int, Decimal] = {}

    for event in trip.events:
        for expense in event.expenses:
            user_id = int(expense.payer_id)
            balances[user_id] = balances.get(user_id, Decimal(0)) + Decimal(str(expense.value))
        for debt in event.debts:
            user_id = int(debt.debtor_id)
            balances[user_id] = balances.get(user_id, Decimal(0)) - Decimal(str(debt.value))
        event.settled_up = True

    creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0]
    debtors = [(uid, -bal) for uid, bal in balances.items() if bal < 0]

    creditors.sort(key=lambda x: x[0])
    debtors.sort(key=lambda x: x[0])

    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        cred_id, cred_bal = creditors[i]
        debt_id, debt_bal = debtors[j]

        amount = min(cred_bal, debt_bal)
        session.add(Summary(
            trip_id=trip_id,
            user_from_id=cred_id,
            user_to_id=debt_id,
            value=amount
        ))

        creditors[i] = (cred_id, cred_bal - amount)
        debtors[j] = (debt_id, debt_bal - amount)

        if creditors[i][1] == 0:
            i += 1
        if debtors[j][1] == 0:
            j += 1

    session.commit()
