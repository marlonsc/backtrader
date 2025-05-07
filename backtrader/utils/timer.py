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
    """Creates and adds a timer to the list of pending timers.

Args:
    pretimers: List of pending timers
    owner: Timer owner object
    when: Trigger condition
    offset: Timer offset
    repeat: Repetition
    weekdays: Days of the week
    weekcarry: Week carry
    monthdays: Days of the month
    monthcarry: Month carry
    allow: Permission
    tzdata: Timezone
    strats: Strategies
    cheat: Cheat flag

Returns:
    Timer instance"""
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
    """Schedules a timer for the cerebro object.

Args:
    cerebro: Cerebro instance
    when: Trigger condition
    offset: Timer offset
    repeat: Repetition
    weekdays: Days of the week
    weekcarry: Week carry
    monthdays: Days of the month
    monthcarry: Month carry
    allow: Permission
    tzdata: Timezone
    strats: Strategies
    cheat: Cheat flag

Returns:
    Timer instance"""
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
    """Timer notification (stub for future interface).

Args:
    timer: Timer instance
    when: Timer moment"""
