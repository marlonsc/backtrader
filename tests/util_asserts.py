import backtrader as bt


def assert_data(data, idx: int, time, open=None, high=None, low=None, close=None):
    """

    :param data:
    :param idx:
    :type idx: int
    :param time:
    :param open: (Default value = None)
    :param high: (Default value = None)
    :param low: (Default value = None)
    :param close: (Default value = None)

    """
    lables = ["open", "high", "low", "close"]
    for l in lables:
        val = locals()[l]
        if val is None:
            continue
        assert getattr(data, l)[idx] == val

    assert bt.num2date(data.datetime[idx]) == time
