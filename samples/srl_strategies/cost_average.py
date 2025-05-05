# -*- coding: UTF-8 -*-

import backtrader as bt


class CostAverageStrategy(bt.Strategy):
    """ """

    params = (("amount", 1000), ("interval", 5))

    def __init__(self):
        """ """
        self.counter = 0

    def next(self):
        """ """
        if self.counter % self.p.interval == 0:
            self.buy(size=self.p.amount / self.data.close[0])
        self.counter += 1


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CostAverageStrategy)

    data = bt.feeds.BacktraderCSVData(dataname="../../datas/2006-day-001.txt")
    cerebro.adddata(data)

    cerebro.run()
    cerebro.plot()
