"""buy_and_hold_simple.py module.

Description of the module functionality."""


# import
import backtrader as bt

# globals


class BuyAndHold(bt.Strategy):
""""""
""""""
""""""
        if self.order is None:
            self.order = self.buy()


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BuyAndHold)

    data = bt.feeds.BacktraderCSVData(dataname="../../datas/2006-day-001.txt")
    cerebro.adddata(data)

    cerebro.run()
    cerebro.plot()
