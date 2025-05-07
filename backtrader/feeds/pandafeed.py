"""pandafeed.py module.

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

import backtrader.feed as feed
from backtrader import date2num
from backtrader.utils.py3 import filter, integer_types, string_types


class PandasDirectData(feed.DataBase):
    """Uses a Pandas DataFrame as the feed source, iterating directly over the
tuples returned by "itertuples".
This means that all parameters related to lines must have numeric
values as indices into the tuples
Note:
- The ``dataname`` parameter is a Pandas DataFrame
- A negative value in any of the parameters for the Data lines
indicates it's not present in the DataFrame
it is"""

    params = (
        ("datetime", 0),
        ("open", 1),
        ("high", 2),
        ("low", 3),
        ("close", 4),
        ("volume", 5),
        ("openinterest", 6),
    )

    datafields = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "openinterest",
    ]

    def start(self):
""""""
""""""
    """Uses a Pandas DataFrame as the feed source, using indices into column
names (which can be "numeric")
This means that all parameters related to lines must have numeric
values as indices into the tuples"""

    params = (
        ("nocase", True),
        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ("datetime", None),
        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ("open", -1),
        ("high", -1),
        ("low", -1),
        ("close", -1),
        ("volume", -1),
        ("openinterest", -1),
    )

    datafields = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "openinterest",
    ]

    def __init__(self):
""""""
""""""
""""""
        self._idx += 1

        if self._idx >= len(self.p.dataname):
            # exhausted all rows
            return False

        # Set the standard datafields
        for datafield in self.getlinealiases():
            if datafield == "datetime":
                continue

            colindex = self._colmapping[datafield]
            if colindex is None:
                # datafield signaled as missing in the stream: skip it
                continue

            # get the line to be set
            line = getattr(self.lines, datafield)

            # indexing for pandas: 1st is colum, then row
            line[0] = self.p.dataname.iloc[self._idx, colindex]

        # datetime conversion
        coldtime = self._colmapping["datetime"]

        if coldtime is None:
            # standard index in the datetime
            tstamp = self.p.dataname.index[self._idx]
        else:
            # it's in a different column ... use standard column index
            tstamp = self.p.dataname.iloc[self._idx, coldtime]

        # convert to float via datetime and store it
        dt = tstamp.to_pydatetime()
        dtnum = date2num(dt)
        self.lines.datetime[0] = dtnum

        # Done ... return
        return True
