# Copyright (c) 2025 backtrader contributors
"""
OptReturn utility class for encapsulating optimization results.
Docstrings and comments should be line-wrapped ≤ 90 characters.
"""


class OptReturn(object):

    def __init__(self, params, **kwargs):
        """

        :param params:
        :param **kwargs:

        """
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)
