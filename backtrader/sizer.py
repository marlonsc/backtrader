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

from .metabase import MetaParams
from .utils.py3 import with_metaclass


class Sizer(with_metaclass(MetaParams, object)):
    """This is the base class for *Sizers*. Any *sizer* should subclass this
and override the ``_getsizing`` method
Member Attribs:
- ``strategy``: will be set by the strategy in which the sizer is working
Gives access to the entire api of the strategy, for example if the
actual data position would be needed in ``_getsizing``::
position = self.strategy.getposition(data)
- ``broker``: will be set by the strategy in which the sizer is working
Gives access to information some complex sizers may need like portfolio
value, .."""

    strategy = None
    broker = None

    def __init__(self):
        super().__init__()

    def getsizing(self, data, isbuy):
        """Args:
    data: 
    isbuy:"""
        comminfo = self.broker.getcommissioninfo(data)
        return self._getsizing(comminfo, self.broker.getcash(), data, isbuy)

    def _getsizing(self, comminfo, cash, data, isbuy):
        """This method has to be overriden by subclasses of Sizer to provide
the sizing functionality

Args:
    comminfo: The CommissionInfo instance that contains
    cash: current available cash in the
    data: target of the operation
    isbuy: will be"""
        raise NotImplementedError

    def set(self, strategy, broker):
        """Args:
    strategy: 
    broker:"""
        self.strategy = strategy
        self.broker = broker


SizerBase = Sizer  # alias for old naming
