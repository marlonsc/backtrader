"""qmtfeed.py module.

Description of the module functionality."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import datetime
import random
from collections import deque

import backtrader as bt
from backtrader.feed import DataBase

from .qmtstore import QMTStore


class MetaQMTFeed(DataBase.__class__):
""""""
"""Class has already been created ... register

Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        # Initialize the class
        super(MetaQMTFeed, cls).__init__(name, bases, dct)

        # Register with the store
        QMTStore.DataCls = cls


class QMTFeed(DataBase, metaclass=MetaQMTFeed):
    """QMT eXchange Trading Library Data Feed."""

    lines = (
        "lastClose",
        "amount",
        "pvolume",
        "stockStatus",
        "openInt",
        "lastSettlementPrice",
        "settlementPrice",
        "transactionNum",
        "askPrice1",
        "askPrice2",
        "askPrice3",
        "askPrice4",
        "askPrice5",
        "bidPrice1",
        "bidPrice2",
        "bidPrice3",
        "bidPrice4",
        "bidPrice5",
        "askVol1",
        "askVol2",
        "askVol3",
        "askVol4",
        "askVol5",
        "bidVol1",
        "bidVol2",
        "bidVol3",
        "bidVol4",
        "bidVol5",
        "openInterest",
        "dr",
        "totaldr",
        "preClose",
        "suspendFlag",
        "settelementPrice",
        "pe",
    )

    params = (
        ("live", False),  # only historical download
        ("timeframe", bt.TimeFrame.Days),
    )

    def __init__(self, **kwargs):
        """"""
        self._timeframe = self.p.timeframe
        self._compression = 1
        self.store = kwargs["store"]
        # self.cerebro = kwargs['cerebro']
        self._data = deque()  # data queue for price data
        self._seq = None

    # def __len__(self):
    #     return len(self._data)

    def start(
        self,
    ):
""""""
""""""
"""Args::
    value:"""
"""Args::
    current:"""
"""Args::
    replace: (Default value = False)"""
""""""
""""""
"""Args::
    dt: 
    period: (Default value = "1d")"""
    period: (Default value = "1d")"""
        if dt is None:
            return ""
        else:
            if period == "1d":
                formatted_string = dt.strftime("%Y%m%d")
            else:
                formatted_string = dt.strftime("%Y%m%d%H%M%S")
            return formatted_string

    def _append_data(self, item):
"""Args::
    item:"""
"""Args::
    period:"""
"""Args::
    period:"""
"""Args::
    datas:"""
    datas:"""
            for stock_code in datas:
                print(stock_code, datas[stock_code])
                # 遍历该股票的所有数据条目
                for current in datas[stock_code]:  # 添加内部循环处理每个数据字典
                    if self._get_datetime(current["time"]) == self.lines.datetime[0]:
                        self._load_current(current)
                    else:
                        self._data.append(current)

            # print("Received data columns:", res.columns)  # 查看列名
            # print("Full data:", res)  # 查看完整数据结构
            # current = res
            # data=current['time'][0]
            #
            # current['time']=data
            # print(current['time'])
            # if self._get_datetime(data) == self.lines.datetime[0]:
            #     self._load_current(current)
            # else:
            #     self._data.append(current)

        self._seq = self.store._subscribe_live(
            symbol=self.p.dataname,
            period=period,
            start_time=start_time,
            callback=on_data,
        )
        #
        # res = self.store._fetch_history(symbol=self.p.dataname, period=period, start_time=start_time, download=False)
        # result = res.to_dict('records')
        # for item in result:
        #     self._data.append(item)
