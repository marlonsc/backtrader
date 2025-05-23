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


class Position(object):
    """Keeps and updates the size and price of a position. The object has no
    relationship to any asset. It only keeps size and price.

    Member Attributes:
      - size (int): current size of the position
      - price (float): current price of the position

    The Position instances can be tested using len(position) to see if size
    is not null


    """

    def __str__(self):
        """ """
        items = list()
        items.append("--- Position Begin")
        items.append("- Size: {}".format(self.size))
        items.append("- Price: {}".format(self.price))
        items.append("- Price orig: {}".format(self.price_orig))
        items.append("- Closed: {}".format(self.upclosed))
        items.append("- Opened: {}".format(self.upopened))
        items.append("- Adjbase: {}".format(self.adjbase))
        items.append("--- Position End")
        return "\n".join(items)

    def __init__(self, size=0, price=0.0):
        """

        :param size:  (Default value = 0)
        :param price:  (Default value = 0.0)

        """
        self._size = size
        if size:
            self.price = self.price_orig = price
        else:
            self.price = 0.0

        self.adjbase = None

        self.upopened = size
        self.upclosed = 0
        self.set(size, price)

        self.updt = None

    @property
    def size(self):
        """ """
        return self._size

    @size.setter
    def size(self, value):
        """

        :param value:

        """
        self._size = value

    @property
    def position(self):
        """ """
        return self._size

    @position.setter
    def position(self, value):
        """

        :param value:

        """
        self._size = value

    def fix(self, size, price):
        """

        :param size:
        :param price:

        """
        oldsize = self.size
        self.size = size
        self.price = price
        return self.size == oldsize

    def set(self, size, price):
        """

        :param size:
        :param price:

        """
        if self.size > 0:
            if size > self.size:
                self.upopened = size - self.size  # new 10 - old 5 -> 5
                self.upclosed = 0
            else:
                # same side min(0, 3) -> 0 / reversal min(0, -3) -> -3
                self.upopened = min(0, size)
                # same side min(10, 10 - 5) -> 5
                # reversal min(10, 10 - -5) -> min(10, 15) -> 10
                self.upclosed = min(self.size, self.size - size)

        elif self.size < 0:
            if size < self.size:
                self.upopened = size - self.size  # ex: -5 - -3 -> -2
                self.upclosed = 0
            else:
                # same side max(0, -5) -> 0 / reversal max(0, 5) -> 5
                self.upopened = max(0, size)
                # same side max(-10, -10 - -5) -> max(-10, -5) -> -5
                # reversal max(-10, -10 - 5) -> max(-10, -15) -> -10
                self.upclosed = max(self.size, self.size - size)

        else:  # self.size == 0
            self.upopened = self.size
            self.upclosed = 0

        self.size = size
        self.price_orig = self.price
        if size:
            self.price = price
        else:
            self.price = 0.0

        return self.size, self.price, self.upopened, self.upclosed

    def __len__(self):
        """ """
        return abs(self.size)

    def __bool__(self):
        """ """
        return bool(self.size != 0)

    __nonzero__ = __bool__

    def clone(self):
        """ """
        return Position(size=self.size, price=self.price)

    def pseudoupdate(self, size, price):
        """

        :param size:
        :param price:

        """
        return Position(self.size, self.price).update(size, price)

    def update(self, size, price, dt=None):
        """Updates the current position and returns the updated size, price and
        units used to open/close a position

        :param size: new position size
        :param price: new position price
        :param dt:  (Default value = None)
        :returns: If a position is reduced the price of the remaining size
                   does not change
                   If a position is closed the price is nullified
                   If a position is reversed the price is the price given as
                   argument
               opened - amount of contracts from argument "size" that were used
                   to open/increase a position.
                   A position can be opened from 0 or can be a reversal.
                   If a reversal is performed then opened is less than "size",
                   because part of "size" will have been used to close the
                   existing position
               closed - amount of units from arguments "size" that were used to
                   close/reduce a position

            Both opened and closed carry the same sign as the "size" argument
            because they refer to a part of the "size" argument

        """
        self.datetime = dt  # record datetime update (datetime.datetime)

        self.price_orig = self.price
        oldsize = self.size
        self.size += size

        if not self.size:
            # Update closed existing position
            opened, closed = 0, size
            self.price = 0.0
        elif not oldsize:
            # Update opened a position from 0
            opened, closed = size, 0
            self.price = price
        elif oldsize > 0:  # existing "long" position updated
            if size > 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size > 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size < 0 # reversed position form plus to minus
                opened, closed = self.size, -oldsize
                self.price = price

        else:  # oldsize < 0 - existing short position updated
            if size < 0:  # increased position
                opened, closed = size, 0
                self.price = (self.price * oldsize + size * price) / self.size

            elif self.size < 0:  # reduced position
                opened, closed = 0, size
                # self.price = self.price

            else:  # self.size > 0 - reversed position from minus to plus
                opened, closed = self.size, -oldsize
                self.price = price

        self.upopened = opened
        self.upclosed = closed

        return self.size, self.price, opened, closed
