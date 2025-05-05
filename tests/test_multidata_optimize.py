import datetime

import backtrader as bt

from testcommon import getdatadir


class BtTestStrategy(bt.Strategy):
    params = (
        ('period', 15),
        ('printdata', True),
        ('printops', True),
    )


def test_multidata_optimize():
    cerebro = bt.Cerebro(maxcpus=1, optreturn=False)

    cerebro.optstrategy(BtTestStrategy, period=[5, 6, 7])

    data = bt.feeds.YahooFinanceCSVData(
        dataname=getdatadir("nvda-1999-2014.txt"),
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2002, 12, 31),
        reverse=False,
        swapcloses=True,
    )
    cerebro.adddata(data)

    data = bt.feeds.YahooFinanceCSVData(
        dataname=getdatadir("orcl-1995-2014.txt"),
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2002, 12, 31),
        reverse=False,
        swapcloses=True,
    )
    cerebro.adddata(data)

    cerebro.run()


if __name__ == '__main__':
    test_multidata_optimize()
