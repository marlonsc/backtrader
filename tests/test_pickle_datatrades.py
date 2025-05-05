from io import BytesIO
import datetime

import backtrader as bt

import pickle

from testcommon import getdatadir


class BtTestStrategy(bt.Strategy):
    params = (
        ('period', 15),
        ('printdata', True),
        ('printops', True),
    )


def test_pickle_datatrades():
    cerebro = bt.Cerebro(optreturn=False)

    cerebro.addobserver(bt.observers.DataTrades)

    cerebro.addstrategy(BtTestStrategy, period=5)

    data = bt.feeds.YahooFinanceCSVData(
        dataname=getdatadir("nvda-1999-2014.txt"),
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2002, 12, 31),
        reverse=False,
        swapcloses=True,
    )
    cerebro.adddata(data)

    result = cerebro.run()

    f = BytesIO()
    dt = result[0].observers.datatrades
    pickle.dump(dt, f)

    f.seek(0)
    dt_loaded = pickle.load(f)
    assert len(dt_loaded) == 751


if __name__ == '__main__':
    test_pickle_datatrades()
