# Copyright (c) 2025 backtrader contributors
"""
Iteration utility functions for general use in the backtrader framework.
All functions and docstrings should be line-wrapped ≤ 90 characters.
"""

import collections

from .py3 import string_types

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections


def iterize(iterable):
    """Transforms elements into iterables, except strings, to facilitate generic loops.
Strings are encapsulated in tuples. Other non-iterable elements are also
encapsulated in tuples.

Args:
    iterable: Iterable object or single element

Returns:
    List of iterables"""
    niterable = list()
    for elem in iterable:
        if isinstance(elem, string_types):
            elem = (elem,)
        elif not isinstance(elem, collectionsAbc.Iterable):
            elem = (elem,)
        niterable.append(elem)
    return niterable
