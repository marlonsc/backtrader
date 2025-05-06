"""daysteps.py module.

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


class St(bt.Strategy):
""""""
""""""
""""""
""""""
""""""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample for pivot point and cross plotting",
    )

    parser.add_argument(
        "--data",
        required=False,
        default="../../datas/2005-2006-day-001.txt",
        help="Data to be read in",
    )

    parser.add_argument(
        "--cerebro",
        required=False,
        action="store",
        default="",
        help="Arguments for cerebro",
    )

    parser.add_argument(
        "--plot",
        "-p",
        nargs="?",
        required=False,
        metavar="kwargs",
        const="{}",
        help="Plot (with additional args if passed",
    )

    return parser.parse_args(pargs)


if __name__ == "__main__":
    runstrat()
