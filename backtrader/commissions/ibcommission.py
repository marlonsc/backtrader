#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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
from __future__ import absolute_import, division, print_function, unicode_literals

from backtrader.comminfo import CommInfoBase
import math


class IBCommInfo(CommInfoBase):
    """
    Commissions are calculated by ib, but the trades calculations in the
    ```Strategy`` rely on the order carrying a CommInfo object attached for the
    calculation of the operation cost and value.

    These are non-critical informations, but removing them from the trade could
    break existing usage and it is better to provide a CommInfo objet which
    enables those calculations even if with approvimate values.

    The margin calculation is not a known in advance information with IB
    (margin impact can be gotten from OrderState objects) and therefore it is
    left as future exercise to get it"""

    COMM_PERC, COMM_FIXED, COMM_STOCK, COMM_FUTURE, COMM_OPTION, COMM_FOREX = range(6)

    def __init__(self, data=None):
        super(IBCommInfo, self).__init__()
        if self._commtype == self.COMM_STOCK:
            self._stocklike = True
            self.p.commission = 0.005
        elif self._commtype == self.COMM_OPTION:
            self._stocklike = False
            self.p.commission = 0.65
        elif self._commtype == self.COMM_FUTURE:
            self._stocklike = False
            self.p.commission = 1.37
        elif self._commtype == self.COMM_FOREX:
            self._stocklike = False
            self.p.commission = 0.00002

    """
    def get_margin(self, price):
        if not self.p.automargin:
            return self.p.margin

        elif self.p.automargin < 0:
            return price * self.p.mult

        return price * self.p.automargin  # int/float expected
    """

    def getsize(self, price, cash):
        """Returns the needed size to meet a cash operation at a given price"""
        # Just inherit from base class, need to be update
        # getsize 需要考虑佣金，cash需要减去佣金
        size = 0
        unitprice = 0
        if not self._stocklike:
            unitprice = self.get_margin(price)
        else:
            unitprice = price

        size = int(cash // unitprice)
        deltasize1 = math.ceil(self.getcommission(size, price) // unitprice)
        size -= deltasize1
        deltavalue = cash - self.getcommission(size, price) - unitprice * size
        deltasize2 = int(deltavalue // unitprice)
        size += deltasize2

        while cash - self.getcommission(size, price) - unitprice * size < 0:
            size -= 1

        size = int(size * self.p.leverage)
        return size

    def getoperationcost(self, size, price):
        """Returns the needed amount of cash an operation would cost"""
        # Same reasoning as above
        return abs(float(size)) * float(price)

    def getvaluesize(self, size, price):
        # In real life the margin approaches the price
        if not self._stocklike:
            return abs(size) * self.get_margin(price)

        return size * price

    def _getcommission(self, size, price, pseudoexec):
        """Calculates the commission of an operation at a given price

        pseudoexec: if True the operation has not yet been executed
        """

        if self._commtype == self.COMM_PERC:
            return abs(size) * self.p.commission * price

        if self._commtype == self.COMM_STOCK:
            # value of positions
            value = abs(size) * price
            # IB Commission Fixed model, Minimum per order:1$ Maximum per order %1 of trade
            brokercommission = abs(size) * self.p.commission
            brokercommission = max(1, brokercommission)
            brokercommission = min(brokercommission, value * 0.01)

            # Transaction Fee (0.0000278 * Value of Sale):
            transaction_fee = 0.0000278 * value

            # FINRA Trading Activity Fee. Fixed 8.30$
            trade_activtity_fee = 8.3

            # FINRA Consolidated Audit Trail Fee (0.000052 * Quantity)
            FINRA_fee = 0.000052 * abs(size)

            # total commission
            total_commission = (
                brokercommission + transaction_fee + trade_activtity_fee + FINRA_fee
            )

            return total_commission
        # 根据不同的权利金(Premium)，合约佣金不同
        # Contract commissions vary based on different premiums.
        if self._commtype == self.COMM_OPTION:
            if price < 0.05:
                communit = 0.25
            elif price < 0.1:
                communit = 0.5
            else:
                communit = 0.65

            # value of positions, Premium maybe < 0
            value = max(abs(size) * price, 0)
            # IB Commission Fixed model, Minimum per order:1$ Maximum per order %1 of trade
            brokercommission = abs(size) * communit
            brokercommission = max(1, brokercommission)

            # Exchange Fees
            exchangefee = 0.1 * abs(size)

            # Clearing Fees
            clearingfee = 0.02 * abs(size)

            # Regulatory Fees
            regulatoryfee = (0.02815 + 0.0052) * abs(size)

            # Transaction Fees
            trade_activtity_fee = 0.0000278 * value + 0.00279 * abs(size)

            # total commission
            total_commission = (
                brokercommission + exchangefee + clearingfee + trade_activtity_fee
            )

            return total_commission

        if self._commtype == self.COMM_FUTURE:
            # IB Commission Fixed model, Minimum per order:1$ Maximum per order %1 of trade
            total_commission = abs(size) * self.p.commission

            return total_commission

        if self._commtype == self.COMM_FOREX:
            # IB Commission, Perc mode2, Minimum per order
            brokercommission = abs(size) * price * self.p.commission
            total_commission = max(2, brokercommission)

            return total_commission

        return abs(size) * self.p.commission
