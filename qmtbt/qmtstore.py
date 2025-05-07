"""qmtstore.py module.

Description of the module functionality."""


import pandas as pd
from backtrader.metabase import MetaParams
from xtquant import xtdata, xttrader, xttype


class MetaSingleton(MetaParams):
    """Metaclass to make a metaclassed class a singleton"""

    def __init__(cls, name, bases, dct):
"""Args::
    name: 
    bases: 
    dct:"""
    dct:"""
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        """"""
        if cls._singleton is None:
            cls._singleton = super(MetaSingleton, cls).__call__(*args, **kwargs)

        return cls._singleton


class QMTStore(object, metaclass=MetaSingleton):
""""""
        """Returns ``DataCls`` with args, kwargs"""
        kwargs["store"] = self
        qmtFeed = self.__class__.DataCls(*args, **kwargs)
        return qmtFeed

    def getdatas(self, *args, **kwargs):
        """Returns ``DataCls`` with *args, **kwargs (multiple entries)"""
        return [
            self.getdata(*args, **{**kwargs, "dataname": stock})
            for stock in kwargs.pop("code_list", 1)
        ]

    def setdatas(self, cerebro, datas):
"""Set the datas

Args::
    cerebro: 
    datas:"""
    datas:"""
        for data in datas:
            cerebro.adddata(data)

    def getbroker(self, *args, **kwargs):
        """Returns broker with *args, **kwargs from registered ``BrokerCls``"""
        return self.__class__.BrokerCls(*args, **kwargs)

    def __init__(self):
""""""
""""""
"""Args::
    mini_qmt_path: 
    account:"""
    account:"""

        try:
            xtdata.connect()
        except BaseException:
            return -1

        session_id = int(random.randint(100000, 999999))
        xt_trader = xttrader.XtQuantTrader(mini_qmt_path, session_id)

        xt_trader.start()

        connect_result = xt_trader.connect()

        if connect_result == 0:
            print("连接成功")

            self.stock_account = xttype.StockAccount(account)

            xt_trader.subscribe(self.stock_account)

            self.xt_trader = xt_trader

        return connect_result

    def _auto_expand_array_columns(self, df: pd.DataFrame) -> pd.DataFrame:
"""Write by ChatGPT4
Automatically identify and expand DataFrame columns containing array values.

Args::
    df: 

Returns::
    - A new DataFrame with the expanded columns."""
    - A new DataFrame with the expanded columns."""
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (list, tuple))).all():
                # Expand the array column into a new DataFrame
                expanded_df = df[col].apply(pd.Series)
                # Generate new column names
                expanded_df.columns = [
                    f"{col}{i + 1}" for i in range(expanded_df.shape[1])
                ]
                # Drop the original column and join the expanded columns
                df = df.drop(col, axis=1).join(expanded_df)
        return df

    def _fetch_history(
        self,
        symbol,
        period,
        start_time="",
        end_time="",
        count=-1,
        dividend_type="front",
        download=True,
    ):
"""获取历史数据
参数：
symbol: 标的代码
period: 周期
start_time: 起始日期
end_time: 终止日期

Args::
    symbol: 
    period: 
    start_time: (Default value = "")
    end_time: (Default value = "")
    count: (Default value = -1)
    dividend_type: (Default value = "front")
    download: (Default value = True)"""
    download: (Default value = True)"""
        print("下载数据" + symbol)
        if download:
            xtdata.download_history_data(
                stock_code=symbol,
                period=period,
                start_time=start_time,
                end_time=end_time,
            )
        res = xtdata.get_market_data_ex(
            stock_list=[symbol],
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=count,
            dividend_type=dividend_type,
            fill_data=True,
        )
        res = res[symbol]
        if period == "tick":
            res = self._auto_expand_array_columns(res)
        return res

    def _subscribe_live(self, symbol, period, callback, start_time="", end_time=""):
"""Args::
    symbol: 
    period: 
    callback: 
    start_time: (Default value = "")
    end_time: (Default value = "")"""
    end_time: (Default value = "")"""

        seq = xtdata.subscribe_quote(
            stock_code=symbol,
            period=period,
            start_time=start_time,
            end_time=end_time,
            callback=callback,
        )

        return seq

    def _unsubscribe_live(self, seq):
"""Args::
    seq:"""
    seq:"""
        xtdata.unsubscribe_quote(seq)
