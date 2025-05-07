# Copyright (c) 2025 backtrader contributors
"""
Utilities for timer manipulation in backtrader.
All functions and docstrings should be line-wrapped ≤ 90 characters.
"""

import datetime
from ..timer import Timer


def create_timer(
    pretimers,
    owner,
    when,
    offset=datetime.timedelta(),
    repeat=datetime.timedelta(),
    weekdays=None,
    weekcarry=False,
    monthdays=None,
    monthcarry=True,
    allow=None,
    tzdata=None,
    strats=False,
    cheat=False,
    *args,
    **kwargs,
):
    """
    Creates and adds a timer to the list of pending timers.

    :param pretimers: List of pending timers
    :param owner: Timer owner object
    :param when: Trigger condition
    :param offset: Timer offset
    :param repeat: Repetition
    :param weekdays: Days of the week
    :param weekcarry: Week carry
    :param monthdays: Days of the month
    :param monthcarry: Month carry
    :param allow: Permission
    :param tzdata: Timezone
    :param strats: Strategies
    :param cheat: Cheat flag
    :param *args: Additional args
    :param **kwargs: Additional kwargs
    :return: Timer instance
    """
    if weekdays is None:
        weekdays = []
    if monthdays is None:
        monthdays = []
    timer = Timer(
        tid=len(pretimers),
        owner=owner,
        strats=strats,
        when=when,
        offset=offset,
        repeat=repeat,
        weekdays=weekdays,
        weekcarry=weekcarry,
        monthdays=monthdays,
        monthcarry=monthcarry,
        allow=allow,
        tzdata=tzdata,
        cheat=cheat,
        *args,
        **kwargs,
    )
    pretimers.append(timer)
    return timer


def schedule_timer(
    cerebro,
    when,
    offset=datetime.timedelta(),
    repeat=datetime.timedelta(),
    weekdays=None,
    weekcarry=False,
    monthdays=None,
    monthcarry=True,
    allow=None,
    tzdata=None,
    strats=False,
    cheat=False,
    *args,
    **kwargs,
):
    """
    Schedules a timer for the cerebro object.
    :param cerebro: Cerebro instance
    :param when: Trigger condition
    :param offset: Timer offset
    :param repeat: Repetition
    :param weekdays: Days of the week
    :param weekcarry: Week carry
    :param monthdays: Days of the month
    :param monthcarry: Month carry
    :param allow: Permission
    :param tzdata: Timezone
    :param strats: Strategies
    :param cheat: Cheat flag
    :param *args: Additional args
    :param **kwargs: Additional kwargs
    :return: Timer instance
    """
    return create_timer(
        cerebro._pretimers,
        owner=cerebro,
        when=when,
        offset=offset,
        repeat=repeat,
        weekdays=weekdays,
        weekcarry=weekcarry,
        monthdays=monthdays,
        monthcarry=monthcarry,
        allow=allow,
        tzdata=tzdata,
        strats=strats,
        cheat=cheat,
        *args,
        **kwargs,
    )


def notify_timer(timer, when, *args, **kwargs):
    """
    Timer notification (stub for future interface).
    :param timer: Timer instance
    :param when: Timer moment
    :param *args: Additional args
    :param **kwargs: Additional kwargs
    """
    pass
