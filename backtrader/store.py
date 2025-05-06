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

from .metabase import MetaParams
from .utils.py3 import with_metaclass


class MetaSingleton(MetaParams):
    """Metaclass to make a metaclassed class a singleton."""

    def __init__(self, name, bases, dct):
        """Args:
    name: 
    bases: 
    dct:"""
        super().__init__(name, bases, dct)
        self._singleton = None

    def __call__(self, *args, **kwargs):
        """"""
        if self._singleton is None:
            self._singleton = super().__call__(*args, **kwargs)
        return self._singleton


class Store(with_metaclass(MetaSingleton, object)):
    """Base class for all Stores"""

    _started = False

    params = ()

    def getdata(self, *args, **kwargs):
        """Returns ``DataCls`` with args, kwargs"""
        if not hasattr(self, "DataCls") or self.DataCls is None:
            raise RuntimeError("DataCls is not set for this Store.")
        if not callable(self.DataCls):
            raise TypeError("DataCls is not callable. Manual review required.")
        data = self.DataCls(*args, **kwargs)
        data._store = self
        return data

    @classmethod
    def getbroker(cls, *args, **kwargs):
        """Returns broker with *args, **kwargs from registered ``BrokerCls``"""
        if not hasattr(cls, "BrokerCls") or cls.BrokerCls is None:
            raise RuntimeError("BrokerCls is not set for this Store.")
        if not callable(cls.BrokerCls):
            raise TypeError("BrokerCls is not callable. Manual review required.")
        broker = cls.BrokerCls(*args, **kwargs)
        broker._store = cls
        return broker

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    def start(self, data=None, broker=None):
        """Args:
    data: (Default value = None)
    broker: (Default value = None)"""
        if not self._started:
            self._started = True
            self.notifs = collections.deque()
            self.datas = list()
            self.broker = None

        if data is not None:
            self._cerebro = self._env = data._env
            self.datas.append(data)

            if self.broker is not None:
                if hasattr(self.broker, "data_started"):
                    self.broker.data_started(data)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        """ """

    def put_notification(self, msg, *args, **kwargs):
        """Args:
    msg:"""
        self.notifs.append((msg, args, kwargs))

    def get_notifications(self):
        """ """
        self.notifs.append(None)  # put a mark / threads could still append
        return [x for x in iter(self.notifs.popleft, None)]
