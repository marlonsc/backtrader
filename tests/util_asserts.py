"""util_asserts.py module.

Description of the module functionality."""



def assert_data(data, idx: int, time, open=None, high=None, low=None, close=None):
"""Args::
    data: 
    idx: 
    time: 
    open: (Default value = None)
    high: (Default value = None)
    low: (Default value = None)
    close: (Default value = None)"""
    close: (Default value = None)"""
    lables = ["open", "high", "low", "close"]
    for l in lables:
        val = locals()[l]
        if val is None:
            continue
        assert getattr(data, l)[idx] == val

    assert bt.num2date(data.datetime[idx]) == time
