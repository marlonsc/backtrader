#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from .metabase import MetaParams
from .utils.py3 import with_metaclass


class ListenerBase(with_metaclass(MetaParams, object)):
    """Base class for event listeners in Backtrader. Subclass to implement
    custom event handling logic. All docstrings and comments must be line-wrapped
    at 90 characters or less.


    """

    def __init__(self):
        """ """
        pass  # Initialization logic for the listener, if needed.

    def next(self):
        """ """
        pass  # Called on each iteration. Override to implement per-step logic.

    def start(self, cerebro):
        """Called at the start of the run. Receives the Cerebro instance.

        :param cerebro: The Cerebro engine instance.

        """

    def stop(self):
        """ """
        pass  # Called at the end of the run. Override for cleanup logic.
