# Copyright (c) 2025 backtrader contributors
"""
OptReturn utility class for encapsulating optimization results.
Docstrings and comments should be line-wrapped ≤ 90 characters.
"""


class OptReturn(object):
    """
    Container for strategy optimization results.

    :param params: Strategy parameters
    :param **kwargs: Additional attributes to be stored
    """

    def __init__(self, params, **kwargs):
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)
