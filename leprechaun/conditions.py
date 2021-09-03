import operator
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from decimal import Decimal, getcontext
from functools import reduce

import win32api

from .base import InvalidConfigError, calc


def condition(data):
    if "conditions" in data or "conditions-and" in data:
        return AndCondition(data)
    if "conditions-or" in data:
        return OrCondition(data)
    if "condition" not in data:
        raise InvalidConfigError("no condition found")  # Some message filter by this exception message

    # Specific conditions
    if data["condition"] == "when-idle":
        return WhenIdleCondition(data)
    if data["condition"] == "on-schedule":
        return ScheduleCondition(data)

class Condition(ABC):
    @abstractmethod
    def satisfied(self) -> bool:
        pass

class WhenIdleCondition(Condition):
    def __init__(self, data):
        if "idle-time" not in data:
            raise InvalidConfigError("when-idle condition missing 'idle-time' field")

        # Using decimal here for precision and to track that a suffix was applied
        getcontext().prec = 3
        idle_time = calc(data["idle-time"], unary_operators={
            ("s",  "postfix"): Decimal,
            ("ms", "postfix"): lambda val: Decimal(val) / 1000,
            ("m",  "postfix"): lambda val: Decimal(val) * 60,
            ("h",  "postfix"): lambda val: Decimal(val) * 60 * 60,
            ("d",  "postfix"): lambda val: Decimal(val) * 60 * 60 * 24,
        })
        if not isinstance(idle_time, Decimal):
            raise InvalidConfigError("invalid type for 'idle-time' field (use ms, s, m, h, d suffixes to designate time)")

        if idle_time <= 0:
            raise InvalidConfigError(f"'idle-time' field must be above 0 (got '{data['idle-time']})'")

        self.milliseconds = int(idle_time * 1000)

    def satisfied(self):
        idle = (win32api.GetTickCount() - win32api.GetLastInputInfo())
        return idle >= self.milliseconds

class ScheduleCondition(Condition):
    week = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def __init__(self, data):
        if "days" not in data:
            self.days = list(range(7))
        else:
            self.days = []

            for day in data["days"]:
                try:
                    self.days.append(self.week.index(day))
                except ValueError:
                    raise InvalidConfigError(f"unknown day '{day}'") from None

        self.days = [self.week.index(day) for day in data["days"]]

        try:
            self.from_time = time.fromisoformat(data.get("from-time", "00:00"))
        except (TypeError, ValueError):
            raise InvalidConfigError(f"invalid value for field 'from-time' (got '{data['from-time']}')") from None

        try:
            self.until_time = time.fromisoformat(data.get("until-time", "00:00"))
        except (TypeError, ValueError):
            raise InvalidConfigError(f"invalid value for field 'until-time' (got '{data['until-time']}')") from None

    def satisfied(self):
        now = datetime.now()

        if now.weekday() not in self.days:
            return False

        if self.from_time == self.until_time:
            return True

        today = date.today()

        from_datetime = datetime.combine(today, self.from_time)
        until_datetime = datetime.combine(today, self.until_time)

        if self.from_time < self.until_time:
            return from_datetime <= now < until_datetime

        todaybegin = datetime.combine(today, time.min)
        tomorrowbegin = datetime.combine(today + timedelta(days=1), time.min)

        return todaybegin <= now < until_datetime or from_datetime <= now < tomorrowbegin


class AndCondition(Condition):
    def __init__(self, data):
        self.components = []

        try:
            condition_data = data["conditions"]
        except KeyError:
            condition_data = data["conditions-and"]

        for entry in condition_data:
            cond = condition(entry)
            self.components.append(cond)

    def satisfied(self):
        return reduce(operator.and_, (component.satisfied() for component in self.components), True)


class OrCondition(Condition):
    def __init__(self, data):
        self.components = []

        condition_data = data["conditions-or"]

        for entry in condition_data:
            cond = condition(entry)
            self.components.append(cond)

    def satisfied(self):
        return reduce(operator.or_, (component.satisfied() for component in self.components), False)
