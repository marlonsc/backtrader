import backtrader as bt

import pytest

import testcommon


class BtTestStrategy(bt.Strategy):
    params = (
        ('period', 15),
        ('printdata', True),
        ('printops', True),
    )

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        pass

    def next(self):
        pass


def test_optsample(main=False):
    """filters can have a state so when running optstrategy then filters will run several times. so they need to be reset before a new run is started.
    Otherwise their behavior might change between different runs"""
    data = testcommon.getdata(0)

    cerebro = bt.Cerebro(maxcpus=1, optreturn=False)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=2)

    cerebro.optstrategy(BtTestStrategy, period=[5, 4])

    result = cerebro.run()

    # check that we see the expected timestamp in the first bar. if the resampler state didnt reset properly then the second optrun will screw this value up
    assert pytest.approx(732314.99999999) == result[0][0].data0.lines.datetime.array[0]
