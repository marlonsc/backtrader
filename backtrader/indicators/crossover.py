#!/usr/bin/env python
###############################################################################
#
# Copyright (C) 2015-2025 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import numpy as np
from backtrader.indicators.basicops import And
from backtrader.indicator import Indicator
from backtrader.lineseries import LineSeries, LineSeriesMaker
from backtrader.linebuffer import LineBuffer
from backtrader.lineseries import LineSeriesStub
from backtrader.lineroot import LineMultiple


class NonZeroDifference(Indicator):
    """
    Tracks the difference between two data inputs, memorizing the last non-zero value if
    the current difference is zero.

    Formula:
        diff = data - data1
        nzd = diff if diff else diff(-1)
    """

    _mindatas = 2  # requires two (2) data sources
    alias = ("NZD",)
    lines = ("nzd",)

    def nextstart(self):
        """
        Set the initial value for the non-zero difference line.
        """
        self.l.nzd[0] = self.data0[0] - self.data1[0]  # seed value

    def next(self):
        """
        Update the non-zero difference line for the next time step.
        """
        d = self.data0[0] - self.data1[0]
        self.l.nzd[0] = d if d else self.l.nzd[-1]

    def oncestart(self, start, end):
        """
        Set the initial value for the non-zero difference line in batch mode.
        """
        self.line.array[start] = self.data0.array[start] - self.data1.array[start]

    def once(self, start, end):
        """
        Update the non-zero difference line in batch mode.
        """
        d0array = self.data0.array
        d1array = self.data1.array
        larray = self.line.array

        prev = larray[start - 1]
        for i in range(start, end):
            d = d0array[i] - d1array[i]
            larray[i] = prev = d if d else prev


class _CrossBase(Indicator):
    """
    Base class for cross indicators (CrossUp, CrossDown).
    """
    _mindatas = 2

    lines = ("cross",)

    plotinfo = dict(plotymargin=0.05, plotyhlines=[0.0, 1.0])

    def __init__(self, *args, **kwargs):
        """
        Initialize the cross indicator base.
        """
        super().__init__(*args, **kwargs)
        nzd = NonZeroDifference(self.data0, self.data1)

        if self._crossup:
            before = nzd(-1) < 0.0  # data0 was below or at 0
            after = self.data0 > self.data1
        else:
            before = nzd(-1) > 0.0  # data0 was above or at 0
            after = self.data0 < self.data1

        self.lines.cross = And(before, after)


class CrossUp(_CrossBase):
    """
    Indicator that signals when the first data crosses above the second data.

    Formula:
        diff = data - data1
        upcross = last_non_zero_diff < 0 and data0(0) > data1(0)
    """

    _crossup = True


class CrossDown(_CrossBase):
    """
    Indicator that signals when the first data crosses below the second data.

    Formula:
        diff = data - data1
        downcross = last_non_zero_diff > 0 and data0(0) < data1(0)
    """

    _crossup = False


class CrossOver(Indicator):
    """
    Detects crossovers between two data series (data, data1).

    - Returns 1.0 if data crosses above data1
    - Returns -1.0 if data crosses below data1
    - Returns 0.0 otherwise

    Args:
        data: Main series (DataSeries, Indicator, or Line)
        data1: Secondary series (DataSeries, Indicator, or Line)
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments

    Raises:
        TypeError: If two valid inputs are not provided
        ValueError: If any input is None
    """
    _mindatas = 2
    lines = ("crossover",)
    plotinfo = dict(plotymargin=0.05, plotyhlines=[-1.0, 1.0])

    def __init__(self, *args, **kwargs):
        """
        Initialize the CrossOver indicator.

        Handles all calling patterns: (data, data1), data=..., data1=... .
        If only one input is provided, data1 defaults to a zero line of the same length.

        Args:
            *args: Positional arguments for data and data1.
            **kwargs: Keyword arguments for data and data1.
        Raises:
            TypeError: If no valid input is provided.
            ValueError: If any input is None or datas are not correctly initialized.
        """
        data0 = kwargs.pop('data', None)
        data1 = kwargs.pop('data1', None)

        # If not provided via kwargs, try positional args
        if data0 is None and data1 is None:
            if len(args) == 2:
                data0, data1 = args
            elif len(args) == 1:
                data0 = args[0]
                data1 = None
            elif len(args) == 0:
                def make_zero_line():
                    z = LineBuffer()
                    z.forward(0.0, 1)
                    return z
                data0 = make_zero_line()
                data1 = make_zero_line()
            else:
                raise TypeError("CrossOver requires at least one input: data")
        elif data0 is None and len(args) >= 1:
            data0 = args[0]
            if len(args) > 1:
                data1 = args[1]
        elif data1 is None and len(args) >= 2:
            data1 = args[1]

        # Refined PATCH: Only unwrap LineSeriesStub with LineMultiple owner
        def unwrap_stub(x):
            if isinstance(x, LineSeriesStub) and hasattr(x, '_owner') and isinstance(x._owner, LineMultiple):
                return x._owner
            return x
        data0 = unwrap_stub(data0)
        data1 = unwrap_stub(data1)
        # Prevent passing a Strategy instance
        import backtrader
        if isinstance(data0, backtrader.Strategy) or isinstance(data1, backtrader.Strategy):
            raise TypeError("CrossOver: data0/data1 cannot be a Strategy instance")
        data0 = LineSeriesMaker(data0)
        # If data1 is an Indicator, use its first line
        if hasattr(data1, 'lines') and hasattr(data1, '__class__') and \
           issubclass(data1.__class__, Indicator):
            data1 = data1.lines[0]
        if data1 is None:
            # Create a zero line of the same length as data0
            class ZeroLine(LineSeries):
                def __init__(self, src):
                    super().__init__()
                    self.lines[0].array = np.zeros(len(src))
            data1 = ZeroLine(data0)
        else:
            data1 = LineSeriesMaker(data1)
        if data0 is None or data1 is None:
            raise ValueError("CrossOver requires two non-null inputs: data and data1")
        super().__init__(data0, data1, **kwargs)
        if len(self.datas) < 2:
            raise ValueError(
                f"CrossOver failed to initialize: datas={self.datas} "
                f"(data0 type: {type(data0)}, data1 type: {type(data1)})"
            )
        self.data0 = self.datas[0]
        self.data1 = self.datas[1]
        upcross = CrossUp(self.data0, self.data1)
        downcross = CrossDown(self.data0, self.data1)
        self.lines.crossover = upcross - downcross
