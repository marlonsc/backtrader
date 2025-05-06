"""pair-trading.py module.

Description of the module functionality."""

# ##################################################################
# Pair Trading adapted to backtrader
# with PD.OLS and info for StatsModel.API
# author: Remi Roche
##################################################################

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import datetime

# The above could be sent to an independent module
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class PairTradingStrategy(bt.Strategy):
""""""
"""Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print("%s, %s" % (dt.isoformat(), txt))

    def notify_order(self, order):
"""Args::
    order:"""
""""""
""""""
        """
        elif (self.zscore[0] < self.up_medium and self.zscore[0] > self.low_medium):
            self.log('CLOSE LONG %s, price = %.2f' % ("PEP", self.data0.close[0]))
            self.close(self.data0)
            self.log('CLOSE LONG %s, price = %.2f' % ("KO", self.data1.close[0]))
            self.close(self.data1)
        """

    def stop(self):
""""""
""""""
""""""
    parser = argparse.ArgumentParser(description="MultiData Strategy")

    parser.add_argument(
        "--data0",
        "-d0",
        default="../../datas/daily-PEP.csv",
        help="1st data into the system",
    )

    parser.add_argument(
        "--data1",
        "-d1",
        default="../../datas/daily-KO.csv",
        help="2nd data into the system",
    )

    parser.add_argument(
        "--fromdate",
        "-f",
        default="1997-01-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--todate",
        "-t",
        default="1998-06-01",
        help="Starting date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--period",
        default=10,
        type=int,
        help="Period to apply to the Simple Moving Average",
    )

    parser.add_argument("--cash", default=100000, type=int, help="Starting Cash")

    parser.add_argument(
        "--runnext",
        action="store_true",
        help="Use next by next instead of runonce",
    )

    parser.add_argument(
        "--nopreload", action="store_true", help="Do not preload the data"
    )

    parser.add_argument(
        "--oldsync",
        action="store_true",
        help="Use old data synchronization method",
    )

    parser.add_argument(
        "--commperc",
        default=0.005,
        type=float,
        help="Percentage commission (0.005 is 0.5%%",
    )

    parser.add_argument(
        "--stake", default=10, type=int, help="Stake to apply in each operation"
    )

    parser.add_argument(
        "--plot",
        "-p",
        default=True,
        action="store_true",
        help="Plot the read data",
    )

    parser.add_argument("--numfigs", "-n", default=1, help="Plot using numfigs figures")

    return parser.parse_args()


if __name__ == "__main__":
    runstrategy()
