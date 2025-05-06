"""yahoo.py module.

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

import collections
import io
import itertools
from datetime import date, datetime

import backtrader as bt

from .. import feed
from ..utils import date2num


class YahooFinanceCSVData(feed.CSVDataBase):
    """Parses pre-downloaded Yahoo CSV Data Feeds (or locally generated if they
comply to the Yahoo format)
Specific parameters:
- ``dataname``: The filename to parse or a file-like object
- ``reverse`` (default: ``False``)
It is assumed that locally stored files have already been reversed
during the download process
- ``adjclose`` (default: ``True``)
Whether to use the dividend/split adjusted close and adjust all
values according to it.
- ``adjvolume`` (default: ``True``)
Do also adjust ``volume`` if ``adjclose`` is also ``True``
- ``round`` (default: ``True``)
Whether to round the values to a specific number of decimals after
having adjusted the close
- ``roundvolume`` (default: ``0``)
Round the resulting volume to the given number of decimals after having
adjusted it
- ``decimals`` (default: ``2``)
Number of decimals to round to
- ``swapcloses`` (default: ``False``)
[2018-11-16] It would seem that the order of *close* and *adjusted
close* is now fixed. The parameter is retained, in case the need to
swap the columns again arose."""

    lines = ("adjclose",)

    params = (
        ("reverse", False),
        ("adjclose", True),
        ("adjvolume", True),
        ("round", True),
        ("decimals", 2),
        ("roundvolume", False),
        ("swapcloses", False),
    )

    def start(self):
""""""
"""Args::
    linetokens:"""
"""This is intended to load files which were downloaded before Yahoo
    discontinued the original service in May-2017"""
    """

    params = (("version", ""),)


class YahooFinanceCSV(feed.CSVFeedBase):
""""""
    """Executes a direct download of data from Yahoo servers for the given time
range.
Specific parameters (or specific meaning):
- ``dataname``
The ticker to download ('YHOO' for Yahoo own stock quotes)
- ``proxies``
A dict indicating which proxy to go through for the download as in
{'http': 'http://myproxy.com'} or {'http': 'http://127.0.0.1:8080'}
- ``period``
The timeframe to download data in. Pass 'w' for weekly and 'm' for
monthly.
- ``reverse``
[2018-11-16] The latest incarnation of Yahoo online downloads returns
the data in the proper order. The default value of ``reverse`` for the
online download is therefore set to ``False``
- ``adjclose``
Whether to use the dividend/split adjusted close and adjust all values
according to it.
- ``urldown``
The url of the actual download server
- ``retries``
Number of times (each) to try to download the data"""

    params = (
        ("proxies", {}),
        ("period", "d"),
        ("reverse", False),
        ("urldown", "https://query1.finance.yahoo.com/v7/finance/download"),
        ("retries", 3),
    )

    def start_v7(self):
""""""
""""""
""""""

    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()
