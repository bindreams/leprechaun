from abc import ABC, abstractmethod
from datetime import datetime, date, time
from functools import reduce
import operator
import win32api
from .base import InvalidConfigError

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
    def __bool__(self):
        pass

class WhenIdleCondition(Condition):
    def __init__(self, data):
        if "idle-minutes" not in data:
            raise InvalidConfigError("when-idle condition missing 'idle-minutes' field")
        if data["idle-minutes"] <= 0:
            raise InvalidConfigError(f"'idle-minutes' field must be above 0 (got '{data['idle-minutes']})'")

        self.seconds = data["idle-minutes"] * 60
    
    def __bool__(self):
        idle = (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0
        return idle >= self.seconds

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
    
    def __bool__(self):
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
        tomorrowbegin = datetime.combine(today + 1, time.min)

        return todaybegin <= now < until_datetime or from_datetime <= now < tomorrowbegin


class AndCondition(Condition):
    def __init__(self, data):
        self.components = []

        for entry in data:
            cond = condition(entry)
            self.components.append(cond)
    
    def __bool__(self):
        return reduce(operator.and_, self.components, True)


class OrCondition(Condition):
    def __init__(self, data):
        self.components = []

        for entry in data:
            cond = condition(entry)
            self.components.append(cond)
    
    def __bool__(self):
        return reduce(operator.or_, self.components, False)
