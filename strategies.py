"""strategies.py module.

Description of the module functionality."""

# 此模块用于统一存放书写的策略类，数据来源为mini QMT
# 初始化策略的时候需要实例化broker来获取数据：self.mbroker = my_broker(use_real_trading=self.p.use_real_trading)
# 需要输入参数来判断时候需要发送委托：
# params = (
#         ('use_real_trading', False),  # 默认参数
#     )
# 如果需要发送委托需要自行插入broker的buy()方法


import backtrader as bt
from xtquant import xtconstant
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount


class MyXtQuantTraderCallback(XtQuantTraderCallback):
""""""
""""""
"""Args::
    order:"""
"""Args::
    asset:"""
"""Args::
    trade:"""
"""Args::
    position:"""
"""Args::
    order_error:"""
"""Args::
    cancel_error:"""
"""Args::
    response:"""
"""Args::
    status:"""
""""""
"""Args::
    use_real_trading: (Default value = False)"""
"""Args::
    stock_code: 
    price: 
    quantity:"""
    quantity:"""
        if self.use_real_trading:
            fix_result_order_id = self.xt_trader.order_stock(
                self.acc,
                stock_code,
                xtconstant.STOCK_BUY,
                quantity,
                xtconstant.FIX_PRICE,
                price,
            )
            print(fix_result_order_id)
        else:
            print(
                "模拟买入，股票代码: %s, 价格: %.2f, 数量: %d"
                % (stock_code, price, quantity)
            )

    def sell(self, stock_code, price, quantity):
"""Args::
    stock_code: 
    price: 
    quantity:"""
    quantity:"""
        if self.use_real_trading:
            fix_result_order_id = self.xt_trader.order_stock(
                self.acc,
                stock_code,
                xtconstant.STOCK_SELL,
                quantity,
                xtconstant.FIX_PRICE,
                price,
            )
            print(fix_result_order_id)
        else:
            print(
                "模拟卖出，股票代码: %s, 价格: %.2f, 数量: %d"
                % (stock_code, price, quantity)
            )

    def cancel_order(self, order_id):
"""Args::
    order_id:"""
""""""
""""""
"""Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
"""Args::
    order:"""
""""""
""""""
"""Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
""""""
"""Args::
    order:"""
""""""
""""""
""""""
        sma1, sma2 = (
            bt.ind.SMA(period=self.p.period1),
            bt.ind.SMA(period=self.p.period2),
        )
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)
