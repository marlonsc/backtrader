"""strategy-selection.py module.

Description of the module functionality."""

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

import argparse

import backtrader as bt


class St0(bt.SignalStrategy):
""""""
""""""
""""""
""""""
""""""
        """"""
        idx = kwargs.pop("idx")

        obj = cls._STRATS[idx](*args, **kwargs)
        return obj


def runstrat(pargs=None):
"""Args::
    pargs: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for strategy selection",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/2005-2006-day-001.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--maxcpus",
        required=False,
        action="store",
        default=None,
        type=int,
        help="Limit the numer of CPUs to use",
    )

    parser.add_argument(
        "--optreturn",
        required=False,
        action="store_true",
        help="Return reduced/mocked strategy object",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
