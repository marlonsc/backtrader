#!/usr/bin/env python
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
        swap the columns again arose.


    """

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
        """ """
        super(YahooFinanceCSVData, self).start()

        if not self.params.reverse:
            return

        # Yahoo sends data in reverse order and the file is still unreversed
        dq = collections.deque()
        for line in self.f:
            dq.appendleft(line)

        f = io.StringIO(newline=None)
        f.writelines(dq)
        f.seek(0)
        self.f.close()
        self.f = f

    def _loadline(self, linetokens):
        """

        :param linetokens:

        """
        while True:
            nullseen = False
            for tok in linetokens[1:]:
                if tok == "null":
                    nullseen = True
                    linetokens = self._getnextline()  # refetch tokens
                    if not linetokens:
                        return False  # cannot fetch, go away

                    # out of for to carry on wiwth while True logic
                    break

            if not nullseen:
                break  # can proceed

        i = itertools.count(0)

        dttxt = linetokens[next(i)]
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))
        dtnum = date2num(datetime.combine(dt, self.p.sessionend))

        self.lines.datetime[0] = dtnum
        o = float(linetokens[next(i)])
        h = float(linetokens[next(i)])
        l = float(linetokens[next(i)])
        c = float(linetokens[next(i)])
        self.lines.openinterest[0] = 0.0

        # 2018-11-16 ... Adjusted Close seems to always be delivered after
        # the close and before the volume columns
        # SRL or 1.0 if empty
        adjustedclose = float(linetokens[next(i)]) or 1.0
        try:
            v = float(linetokens[next(i)])
        except BaseException:  # cover the case in which volume is "null"
            v = 0.0

        if self.p.swapcloses:  # swap closing prices if requested
            c, adjustedclose = adjustedclose, c

        adjfactor = c / adjustedclose

        # in v7 "adjusted prices" seem to be given, scale back for non adj
        if self.params.adjclose:
            o /= adjfactor
            h /= adjfactor
            l /= adjfactor
            c = adjustedclose
            # If the price goes down, volume must go up and viceversa
            if self.p.adjvolume:
                v *= adjfactor

        if self.p.round:
            decimals = self.p.decimals
            o = round(o, decimals)
            h = round(h, decimals)
            l = round(l, decimals)
            c = round(c, decimals)

        v = round(v, self.p.roundvolume)

        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.adjclose[0] = adjustedclose

        return True


class YahooLegacyCSV(YahooFinanceCSVData):
    """This is intended to load files which were downloaded before Yahoo
    discontinued the original service in May-2017


    """

    params = (("version", ""),)


class YahooFinanceCSV(feed.CSVFeedBase):
    """ """

    DataCls = YahooFinanceCSVData


class YahooFinanceData(YahooFinanceCSVData):
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

        Number of times (each) to try to download the data


    """

    params = (
        ("proxies", {}),
        ("period", "d"),
        ("reverse", False),
        ("urldown", "https://query1.finance.yahoo.com/v7/finance/download"),
        ("retries", 3),
    )

    def start_v7(self):
        """ """
        try:
            import requests
        except ImportError:
            msg = (
                "The new Yahoo data feed requires to have the requests "
                "module installed. Please use pip install requests or "
                "the method of your choice"
            )
            raise Exception(msg)

        self.error = None

        sesskwargs = dict()
        if self.p.proxies:
            sesskwargs["proxies"] = self.p.proxies

        # urldown/ticker?period1=posix1&period2=posix2&interval=1d&events=history

        # Try to download
        urld = "{}/{}".format(self.p.urldown, self.p.dataname)

        urlargs = []
        posix = date(1970, 1, 1)

        if self.p.fromdate is not None:
            period1 = (self.p.fromdate.date() - posix).total_seconds()
        else:
            period1 = 0
        urlargs.append("period1={}".format(int(period1)))
        if self.p.todate is not None:
            period2 = (self.p.todate.date() - posix).total_seconds()
        else:
            # use current time as todate if not provided
            period2 = (datetime.utcnow().date() - posix).total_seconds()
        urlargs.append("period2={}".format(int(period2)))

        intervals = {
            bt.TimeFrame.Days: "1d",
            bt.TimeFrame.Weeks: "1wk",
            bt.TimeFrame.Months: "1mo",
        }

        urlargs.append("interval={}".format(intervals[self.p.timeframe]))
        urlargs.append("events=history")

        urld = "{}?{}".format(urld, "&".join(urlargs))
        f = None
        sess = requests.Session()
        sess.headers["User-Agent"] = "backtrader"
        for i in range(self.p.retries + 1):  # at least once
            resp = sess.get(urld, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue

            ctype = resp.headers["Content-Type"]
            # Cover as many text types as possible for Yahoo changes
            if not ctype.startswith("text/"):
                self.error = "Wrong content type: %s" % ctype
                continue  # HTML returned? wrong url?

            # buffer everything from the socket into a local buffer
            try:
                # r.encoding = 'UTF-8'
                f = io.StringIO(resp.text, newline=None)
            except Exception:
                continue  # try again if possible

            break

        self.f = f

    def start(self):
        """ """
        self.start_v7()

        # Prepared a "path" file -  CSV Parser can take over
        super(YahooFinanceData, self).start()


class YahooFinance(feed.CSVFeedBase):
    """ """

    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()
