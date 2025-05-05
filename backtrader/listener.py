#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import backtrader as bt
from backtrader.utils.py3 import with_metaclass


class ListenerBase(with_metaclass(bt.MetaParams, object)):
    """ """

    def __init__(self):
        """ """

    def next(self):
        """ """

    def start(self, cerebro):
        """

        :param cerebro:

        """

    def stop(self):
        """ """
