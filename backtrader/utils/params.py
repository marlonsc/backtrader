# Copyright (c) 2025 backtrader contributors
"""
Utility functions for initialization and manipulation of Params objects.
Docstrings and comments should be line-wrapped ≤ 90 characters.
"""


def make_params(params_tuple):
    """
    Dynamically creates a Params class from a tuple of (name, value) pairs.

    :param params_tuple: Tuple of parameter (name, value) pairs
    :return: Params instance with corresponding attributes
    """
    param_dict = dict((k, v) for k, v in params_tuple)
    return type("Params", (), param_dict)()
