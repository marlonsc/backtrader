#!/usr/bin/env python
"""This module contains classes for creating dictionaries with automatic
attributes and values.
"""
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
# Copyright (c) 2025 backtrader contributors

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from .py3 import values as py3lvalues

from collections import OrderedDict, defaultdict


def Tree():
    """Create a tree of nested dictionaries.

    Returns:
        defaultdict: A defaultdict of Tree objects.
    """
    return defaultdict(Tree)


class AutoDictList(dict):
    """Create a list of dictionaries.

    Returns:
        dict: A dictionary of lists.
    """

    def __missing__(self, key):
        """Args:
    key:"""
        value = self[key] = list()
        return value


class DotDict(dict):
    """Dictionary with attribute-style access (dot notation).

    Attributes can be accessed as keys and vice versa. Raises AttributeError for
    special attributes (dunder names).

    Returns:
        dict: A dictionary with attribute-style access.
    """

    def __getattr__(self, key):
        """Return value for key as attribute, unless dunder name."""
        if key.startswith("__"):
            raise AttributeError(f"DotDict has no attribute '{key}'")
        return self[key]


class AutoDict(dict):
    """Dictionary with automatic closing and opening.

    Returns:
        dict: A dictionary with automatic closing and opening.
    """

    _closed = False

    def _close(self):
        """Close the dictionary.

        Returns:
            dict: The closed dictionary.
        """
        self._closed = True
        for key, val in self.items():
            if isinstance(val, (AutoDict, AutoOrderedDict)):
                val._close()

    def _open(self):
        """Open the dictionary.

        Returns:
            dict: The opened dictionary.
        """
        self._closed = False

    def __missing__(self, key):
        """Check if the key is missing.
        Args:
            key: The key to check.

        Returns:
            dict: The dictionary with the key.
        """
        if self._closed:
            raise KeyError

        value = self[key] = AutoDict()
        return value

    def __getattr__(self, key):
        """Get the value of the key.

        Args:
            key: The key to get the value of.

        Returns:
            dict: The value of the key.
        """
        if False and key.startswith("_"):
            raise AttributeError

        return self[key]

    def __setattr__(self, key, value):
        """Set the value of the key.

        Args:
            key: The key to set the value of.
            value: The value to set.
        """
        if False and key.startswith("_"):
            self.__dict__[key] = value
            return

        self[key] = value


class AutoOrderedDict(OrderedDict):
    """Ordered dictionary with automatic closing and opening.

    Returns:
        OrderedDict: An ordered dictionary with automatic closing and opening.
    """

    _closed = False

    def _close(self):
        """Close the ordered dictionary.

        Returns:
            OrderedDict: The closed ordered dictionary.
        """
        self._closed = True
        for key, val in self.items():
            if isinstance(val, (AutoDict, AutoOrderedDict)):
                val._close()

    def _open(self):
        """Open the ordered dictionary.

        Returns:
            OrderedDict: The opened ordered dictionary.
        """
        self._closed = False

    def __missing__(self, key):
        """Check if the key is missing.

        Args:
            key: The key to check.

        Returns:
            OrderedDict: The ordered dictionary with the key.
        """
        if self._closed:
            raise KeyError

        # value = self[key] = type(self)()
        value = self[key] = AutoOrderedDict()
        return value

    def __getattr__(self, key):
        """Get the value of the key.

        Args:
            key: The key to get the value of.

        Returns:
            OrderedDict: The value of the key.
        """
        if key.startswith("_"):
            raise AttributeError

        return self[key]

    def __setattr__(self, key, value):
        """Set the value of the key.

        Args:
            key: The key to set the value of.
            value: The value to set.
        """
        if key.startswith("_"):
            self.__dict__[key] = value
            return

        self[key] = value

    # Define math operations
    def __iadd__(self, other):
        """Add two dictionaries.

        Args:
            other: The other dictionary to add.

        Returns:
            OrderedDict: The sum of the two dictionaries.
        """
        if not isinstance(self, type(other)):
            return type(other)() + other

        return self + other

    def __isub__(self, other):
        """Subtract two dictionaries.

        Args:
            other: The other dictionary to subtract.

        Returns:
            OrderedDict: The difference of the two dictionaries.
        """
        if not isinstance(self, type(other)):
            return type(other)() - other

        return self - other

    def __imul__(self, other):
        """Multiply two dictionaries.

        Args:
            other: The other dictionary to multiply.

        Returns:
            OrderedDict: The product of the two dictionaries.
        """
        if not isinstance(self, type(other)):
            return type(other)() * other

        return self + other

    def __idiv__(self, other):
        """Divide two dictionaries.

        Args:
            other: The other dictionary to divide.

        Returns:
            OrderedDict: The quotient of the two dictionaries.
        """
        if not isinstance(self, type(other)):
            return type(other)() // other

        return self + other

    def __itruediv__(self, other):
        """Divide two dictionaries.

        Args:
            other: The other dictionary to divide.

        Returns:
            OrderedDict: The quotient of the two dictionaries.
        """
        if not isinstance(self, type(other)):
            return type(other)() / other

        return self + other

    def lvalues(self):
        """Get the values of the dictionary.

        Returns:
            list: The values of the dictionary.
        """
        return py3lvalues(self)
