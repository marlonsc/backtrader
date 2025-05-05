import backtrader as bt


def assert_data(data, idx: int, time, open=None, high=None, low=None, close=None):
    lables = ['open', 'high', 'low', 'close']
    for l in lables:
        val = locals()[l]
        if val is None:
            continue
        assert getattr(data, l)[idx] == val

    assert (bt.num2date(data.datetime[idx]) == time)
