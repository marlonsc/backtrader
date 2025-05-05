# -*- coding: UTF-8 -*-

# import
import backtrader as bt

# globals


class BuyAndHold(bt.Strategy):
    """ """

    def __init__(self):
        """ """
        self.order = None

    def next(self):
        """ """
        if self.order is None:
            self.order = self.buy()


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BuyAndHold)

    data = bt.feeds.BacktraderCSVData(dataname="../../datas/2006-day-001.txt")
    cerebro.adddata(data)

    cerebro.run()
    cerebro.plot()
