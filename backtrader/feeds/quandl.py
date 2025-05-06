"""quandl.py module.

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

from .. import feed
from ..utils import date2num
from ..utils.py3 import (
    ProxyHandler,
    build_opener,
    install_opener,
    urlopen,
    urlquote,
)

__all__ = ["QuandlCSV", "Quandl"]


class QuandlCSV(feed.CSVDataBase):
    """Parses pre-downloaded Quandl CSV Data Feeds (or locally generated if they
comply to the Quandl format)
Specific parameters:
- ``dataname``: The filename to parse or a file-like object
- ``reverse`` (default: ``False``)
It is assumed that locally stored files have already been reversed
during the download process
- ``adjclose`` (default: ``True``)
Whether to use the dividend/split adjusted close and adjust all
values according to it.
- ``round`` (default: ``False``)
Whether to round the values to a specific number of decimals after
having adjusted the close
- ``decimals`` (default: ``2``)
Number of decimals to round to"""

    _online = False  # flag to avoid double reversal

    params = (
        ("reverse", False),
        ("adjclose", True),
        ("round", False),
        ("decimals", 2),
    )

    def start(self):
""""""
"""Args::
    linetokens:"""
    """Executes a direct download of data from Quandl servers for the given time
range.
Specific parameters (or specific meaning):
- ``dataname``
The ticker to download ('YHOO' for example)
- ``baseurl``
The server url. Someone might decide to open a Quandl compatible
service in the future.
- ``proxies``
A dict indicating which proxy to go through for the download as in
{'http': 'http://myproxy.com'} or {'http': 'http://127.0.0.1:8080'}
- ``buffered``
If True the entire socket connection wil be buffered locally before
parsing starts.
- ``reverse``
Quandl returns the value in descending order (newest first). If this is
``True`` (the default), the request will tell Quandl to return in
ascending (oldest to newest) format
- ``adjclose``
Whether to use the dividend/split adjusted close and adjust all values
according to it.
- ``apikey``
apikey identification in case it may be needed
- ``dataset``
string identifying the dataset to query. Defaults to ``WIKI``"""

    _online = True  # flag to avoid double reversal

    params = (
        ("baseurl", "https://www.quandl.com/api/v3/datasets"),
        ("proxies", {}),
        ("buffered", True),
        ("reverse", True),
        ("apikey", None),
        ("dataset", "WIKI"),
    )

    def start(self):
""""""
        self.error = None

        url = "{}/{}/{}.csv".format(
            self.p.baseurl, self.p.dataset, urlquote(self.p.dataname)
        )

        urlargs = []
        if self.p.reverse:
            urlargs.append("order=asc")

        if self.p.apikey is not None:
            urlargs.append("api_key={}".format(self.p.apikey))

        if self.p.fromdate:
            dtxt = self.p.fromdate.strftime("%Y-%m-%d")
            urlargs.append("start_date={}".format(dtxt))

        if self.p.todate:
            dtxt = self.p.todate.strftime("%Y-%m-%d")
            urlargs.append("end_date={}".format(dtxt))

        if urlargs:
            url += "?" + "&".join(urlargs)

        if self.p.proxies:
            proxy = ProxyHandler(self.p.proxies)
            opener = build_opener(proxy)
            install_opener(opener)

        try:
            datafile = urlopen(url)
        except IOError as e:
            self.error = str(e)
            # leave us empty
            return

        if datafile.headers["Content-Type"] != "text/csv":
            self.error = "Wrong content type: %s" % datafile.headers
            return  # HTML returned? wrong url?

        if self.params.buffered:
            # buffer everything from the socket into a local buffer
            f = io.StringIO(datafile.read().decode("utf-8"), newline=None)
            datafile.close()
        else:
            f = datafile

        self.f = f

        # Prepared a "path" file -  CSV Parser can take over
        super(Quandl, self).start()
