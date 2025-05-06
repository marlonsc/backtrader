"""data-resample.py module.

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
import backtrader.feeds as btfeeds


def runstrat():
""""""
""""""
    parser = argparse.ArgumentParser(description="Resample down to minutes")

    parser.add_argument(
        "--dataname", default="", required=False, help="File Data to Load"
    )

    parser.add_argument(
        "--oldrs",
        required=False,
        action="store_true",
        help="Use deprecated DataResampler",
    )

    parser.add_argument(
        "--timeframe",
        default="weekly",
        required=False,
        choices=["daily", "weekly", "monthly"],
        help="Timeframe to resample to",
    )

    parser.add_argument(
        "--compression",
        default=1,
        required=False,
        type=int,
        help="Compress n bars into 1",
    )

    return parser.parse_args()


if __name__ == "__main__":
    runstrat()
