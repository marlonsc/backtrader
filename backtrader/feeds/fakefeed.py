"""fakefeed.py module.

Description of the module functionality."""

import logging
import math
from enum import Enum

import backtrader as bt

_logger = logging.getLogger(__name__)


class FakeFeed(bt.DataBase):
""""""
""""""
""""""
""""""
""""""
"""Args::
    dt: 
    value:"""
    value:"""
        _logger.debug(f"{self._name} - Updating line - Bar Time: {dt} - Value: {value}")

        self.lines.datetime[0] = bt.date2num(dt)
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

        # Put the prices into the bar
        if math.isnan(self.lines.open[0]):
            self.lines.open[0] = value
        if math.isnan(self.lines.high[0]) or value > self.lines.high[0]:
            self.lines.high[0] = value
        if math.isnan(self.lines.low[0]) or value < self.lines.low[0]:
            self.lines.low[0] = value
        self.lines.close[0] = value
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

    def _update_bar(self, dt, vopen, vlow, vhigh, vclose):
"""Args::
    dt: 
    vopen: 
    vlow: 
    vhigh: 
    vclose:"""
    vclose:"""
        _logger.debug(f"{self._name} - Updating bar - Bar Time: {dt} - Value: {vclose}")

        self.lines.datetime[0] = bt.date2num(dt)
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

        # Put the prices into the bar
        self.lines.open[0] = vopen
        self.lines.high[0] = vhigh
        self.lines.low[0] = vlow
        self.lines.close[0] = vclose
        self.lines.volume[0] = 0.0
        self.lines.openinterest[0] = 0.0

    def _load(self):
""""""
"""Args::
    now: 
    backfill: (Default value = False)"""
    backfill: (Default value = False)"""
        tf, comp = (
            (self.p.timeframe, self.p.compression)
            if not backfill
            else (self._timeframe, self._compression)
        )
        if tf == bt.TimeFrame.Ticks:
            delta = self.p.tick_interval * comp
        elif tf == bt.TimeFrame.Seconds:
            delta = datetime.timedelta(seconds=comp)
        elif tf == bt.TimeFrame.Minutes:
            delta = datetime.timedelta(minutes=comp)
        elif tf == bt.TimeFrame.Days:
            delta = datetime.timedelta(days=comp)
        else:
            raise RuntimeError(
                f"{self._name} - Unsupported timeframe: {self.p.timeframe}"
            )

        if self._last_delivered is None:
            if backfill:
                self._last_delivered = self._time_floored(
                    now - delta * self.p.num_gen_bars, tf, comp
                )  # go back one bar too far since we add one instantly
            else:
                self._last_delivered = self._time_floored(now, tf)

        self._last_delivered += delta

        _logger.info(f"{self._name} - Loading bar: {self._last_delivered}")

        if backfill:
            self._update_bar(
                self._last_delivered,
                self._cur_value,
                self._cur_value,
                self._cur_value + comp,
                self._cur_value + comp,
            )
            self._cur_value += comp
        else:
            self._update_line(self._last_delivered, self._cur_value)
            self._cur_value += 1

        self._num_bars_delivered += 1
        return True

    @staticmethod
    def _time_floored(now, timeframe, comp=1):
"""Args::
    now: 
    timeframe: 
    comp: (Default value = 1)"""
    comp: (Default value = 1)"""
        t = now
        if timeframe in [bt.TimeFrame.Seconds, bt.TimeFrame.Ticks]:
            t -= datetime.timedelta(seconds=t.second % comp, microseconds=t.microsecond)
        elif timeframe == bt.TimeFrame.Minutes:
            t -= datetime.timedelta(
                minutes=t.minute % comp,
                seconds=t.second,
                microseconds=t.microsecond,
            )
        elif timeframe == bt.TimeFrame.Days:
            if comp != 1:
                raise Exception(
                    "For timeframe days only compression of 1 is supported."
                )
            t -= datetime.timedelta(
                hours=t.hour,
                minutes=t.minute,
                seconds=t.second,
                microseconds=t.microsecond,
            )
        else:
            raise Exception(f"TimeFrame {timeframe} not supported")
        return t

    def _load_live(self, now):
"""Args::
    now:"""
    now:"""
        tf = self.p.timeframe

        comp = self.p.compression

        if self._last_delivered is None:
            # first run, fill last_delivered
            self._last_delivered = self._time_floored(now, tf)

        if tf == bt.TimeFrame.Ticks:
            if now - self._last_delivered < self.p.tick_interval:
                return None
            _logger.info(
                f"{self._name} - Delivering - now: {now} - lastDel:"
                f" {self._last_delivered}"
            )
            self._last_delivered += self.p.tick_interval
        else:
            if tf == bt.TimeFrame.Minutes:
                if now.minute == self._last_delivered.minute:
                    return None
                self._last_delivered += datetime.timedelta(minutes=1)
            elif tf == bt.TimeFrame.Days:
                if now.day == self._last_delivered.day:
                    return None
                self._last_delivered += datetime.timedelta(days=1)

        self._current_comp += 1

        if (
            self._current_comp == comp
        ):  # do not use self._compression as it is modified by resampler already
            self._current_comp = 0

            self._update_line(self._last_delivered, self._cur_value)
            self._cur_value += 1
            _logger.info(f"{self._name} - Tick delivered: {self._last_delivered}")
            return True
        else:
            return None
