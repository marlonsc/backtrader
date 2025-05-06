#!/usr/bin389/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2024 Daniel Rodriguez
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
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from .signal import (
    SIGNAL_LONG,
    SIGNAL_LONG_ANY,
    SIGNAL_LONG_INV,
    SIGNAL_LONGEXIT,
    SIGNAL_LONGEXIT_ANY,
    SIGNAL_LONGEXIT_INV,
    SIGNAL_LONGSHORT,
    SIGNAL_SHORT,
    SIGNAL_SHORT_ANY,
    SIGNAL_SHORT_INV,
    SIGNAL_SHORTEXIT,
    SIGNAL_SHORTEXIT_ANY,
    SIGNAL_SHORTEXIT_INV,
)
from .utils.py3 import (
    with_metaclass,
)

try:
    from .metasigstrategy import MetaSigStrategy
except ImportError:

    class MetaSigStrategy(type):
        """ """
        pass


try:
    from .strategy import Strategy
except ImportError:

    class Strategy:
        """ """
        pass


class SignalStrategy(with_metaclass(MetaSigStrategy, Strategy)):
    """This subclass of ``Strategy`` is meant to to auto-operate using
    **signals**.
    
    *Signals* are usually indicators and the expected output values:
    
      - ``> 0`` is a ``long`` indication
    
      - ``< 0`` is a ``short`` indication
    
    There are 5 types of *Signals*, broken in 2 groups.
    
    **Main Group**:
    
      - ``LONGSHORT``: both ``long`` and ``short`` indications from this signal
        are taken
    
      - ``LONG``:
        - ``long`` indications are taken to go long
        - ``short`` indications are taken to *close* the long position. But:
    
          - If a ``LONGEXIT`` (see below) signal is in the system it will be
            used to exit the long
    
          - If a ``SHORT`` signal is available and no ``LONGEXIT`` is available
            , it will be used to close a ``long`` before opening a ``short``
    
      - ``SHORT``:
        - ``short`` indications are taken to go short
        - ``long`` indications are taken to *close* the short position. But:
    
          - If a ``SHORTEXIT`` (see below) signal is in the system it will be
            used to exit the short
    
          - If a ``LONG`` signal is available and no ``SHORTEXIT`` is available
            , it will be used to close a ``short`` before opening a ``long``
    
    **Exit Group**:
    
      This 2 signals are meant to override others and provide criteria for
      exitins a ``long``/``short`` position
    
      - ``LONGEXIT``: ``short`` indications are taken to exit ``long``
        positions
    
      - ``SHORTEXIT``: ``long`` indications are taken to exit ``short``
        positions
    
    **Order Issuing**
    
      Orders execution type is ``Market`` and validity is ``None`` (*Good until
      Canceled*)


    """

    params = (
        ("signals", []),
        ("_accumulate", False),
        ("_concurrent", False),
        ("_data", None),
    )

    def _start(self):
        """ """
        self._sentinel = None  # sentinel for order concurrency
        super(SignalStrategy, self)._start()

    def signal_add(self, sigtype, signal):
        """

        :param sigtype: 
        :param signal: 

        """
        self._signals[sigtype].append(signal)

    def _notify(self, qorders=[], qtrades=[]):
        """

        :param qorders:  (Default value = [])
        :param qtrades:  (Default value = [])

        """
        # Nullify the sentinel if done
        procorders = qorders or self._orderspending
        if self._sentinel is not None:
            for order in procorders:
                if order == self._sentinel and not order.alive():
                    self._sentinel = None
                    break

        super(SignalStrategy, self)._notify(qorders=qorders, qtrades=qtrades)

    def _next_catch(self):
        """ """
        self._next_signal()
        if hasattr(self, "_next_custom"):
            self._next_custom()

    def _next_signal(self):
        """ """
        if self._sentinel is not None and not self.p._concurrent:
            return  # order active and more than 1 not allowed

        sigs = self._signals
        nosig = [[0.0]]

        # Calculate current status of the signals
        ls_long = all(x[0] > 0.0 for x in sigs[SIGNAL_LONGSHORT] or nosig)
        ls_short = all(x[0] < 0.0 for x in sigs[SIGNAL_LONGSHORT] or nosig)

        l_enter0 = all(x[0] > 0.0 for x in sigs[SIGNAL_LONG] or nosig)
        l_enter1 = all(x[0] < 0.0 for x in sigs[SIGNAL_LONG_INV] or nosig)
        l_enter2 = all(x[0] for x in sigs[SIGNAL_LONG_ANY] or nosig)
        l_enter = l_enter0 or l_enter1 or l_enter2

        s_enter0 = all(x[0] < 0.0 for x in sigs[SIGNAL_SHORT] or nosig)
        s_enter1 = all(x[0] > 0.0 for x in sigs[SIGNAL_SHORT_INV] or nosig)
        s_enter2 = all(x[0] for x in sigs[SIGNAL_SHORT_ANY] or nosig)
        s_enter = s_enter0 or s_enter1 or s_enter2

        l_ex0 = all(x[0] < 0.0 for x in sigs[SIGNAL_LONGEXIT] or nosig)
        l_ex1 = all(x[0] > 0.0 for x in sigs[SIGNAL_LONGEXIT_INV] or nosig)
        l_ex2 = all(x[0] for x in sigs[SIGNAL_LONGEXIT_ANY] or nosig)
        l_exit = l_ex0 or l_ex1 or l_ex2

        s_ex0 = all(x[0] > 0.0 for x in sigs[SIGNAL_SHORTEXIT] or nosig)
        s_ex1 = all(x[0] < 0.0 for x in sigs[SIGNAL_SHORTEXIT_INV] or nosig)
        s_ex2 = all(x[0] for x in sigs[SIGNAL_SHORTEXIT_ANY] or nosig)
        s_exit = s_ex0 or s_ex1 or s_ex2

        # Use oppossite signales to start reversal (by closing)
        # but only if no "xxxExit" exists
        l_rev = not self._longexit and s_enter
        s_rev = not self._shortexit and l_enter

        # Opposite of individual long and short
        l_leav0 = all(x[0] < 0.0 for x in sigs[SIGNAL_LONG] or nosig)
        l_leav1 = all(x[0] > 0.0 for x in sigs[SIGNAL_LONG_INV] or nosig)
        l_leav2 = all(x[0] for x in sigs[SIGNAL_LONG_ANY] or nosig)
        l_leave = l_leav0 or l_leav1 or l_leav2

        s_leav0 = all(x[0] > 0.0 for x in sigs[SIGNAL_SHORT] or nosig)
        s_leav1 = all(x[0] < 0.0 for x in sigs[SIGNAL_SHORT_INV] or nosig)
        s_leav2 = all(x[0] for x in sigs[SIGNAL_SHORT_ANY] or nosig)
        s_leave = s_leav0 or s_leav1 or s_leav2

        # Invalidate long leave if longexit signals are available
        l_leave = not self._longexit and l_leave
        # Invalidate short leave if shortexit signals are available
        s_leave = not self._shortexit and s_leave

        # Take size and start logic
        size = self.getposition(self._dtarget).size
        if not size:
            if ls_long or l_enter:
                self._sentinel = self.buy(self._dtarget)

            elif ls_short or s_enter:
                self._sentinel = self.sell(self._dtarget)

        elif size > 0:  # current long position
            if ls_short or l_exit or l_rev or l_leave:
                # closing position - not relevant for concurrency
                self.close(self._dtarget)

            if ls_short or l_rev:
                self._sentinel = self.sell(self._dtarget)

            if ls_long or l_enter:
                if self.p._accumulate:
                    self._sentinel = self.buy(self._dtarget)

        elif size < 0:  # current short position
            if ls_long or s_exit or s_rev or s_leave:
                # closing position - not relevant for concurrency
                self.close(self._dtarget)

            if ls_long or s_rev:
                self._sentinel = self.buy(self._dtarget)

            if ls_short or s_enter:
                if self.p._accumulate:
                    self._sentinel = self.sell(self._dtarget)
