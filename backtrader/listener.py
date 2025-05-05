#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from backtrader.utils.py3 import ( with_metaclass)


class ListenerBase(with_metaclass(bt.MetaParams, object)):
    def next(self):
        pass

    def start(self, cerebro):
        pass

    def stop(self):
        pass
