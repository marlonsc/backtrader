# Copyright (c) 2025 backtrader contributors
"""
Utilities for calendar and timezone manipulation in backtrader.
All functions and docstrings should be line-wrapped ≤ 90 characters.
"""

from .tradingcal import PandasMarketCalendar, TradingCalendarBase
from .utils.py3 import string_types


def addcalendar(cal):
    """Instantiates and returns a global trading calendar from different
    input types (string, instance, class, etc).

    Args:
        cal: String, instance or calendar class

    Returns:
        Calendar instance"""
    if isinstance(cal, string_types):
        calobj = PandasMarketCalendar()
        if not hasattr(calobj, 'p'):
            raise AttributeError(
                "PandasMarketCalendar instance has no 'p' attribute. "
                "Check your calendar implementation."
            )
        calobj.p.calendar = cal
        return calobj
    elif hasattr(cal, "valid_days"):
        calobj = PandasMarketCalendar()
        if not hasattr(calobj, 'p'):
            raise AttributeError(
                "PandasMarketCalendar instance has no 'p' attribute. "
                "Check your calendar implementation."
            )
        calobj.p.calendar = cal
        return calobj
    else:
        try:
            if issubclass(cal, TradingCalendarBase):
                return cal()
        except TypeError:  # already an instance
            pass
    return cal


def addtz(params, tz):
    """Sets the global timezone in system parameters.

    Args:
        params: Parameters object
        tz: Timezone (None, string, int, pytz)"""
    params.tz = tz
