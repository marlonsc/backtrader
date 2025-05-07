"""live_backtrader.py module.

Description of the module functionality."""


import backtrader as bt
from qmtbt import QMTStore
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
""""""
"""Args::
    stock_code: 
    price: 
    quantity:"""
    quantity:"""
        # 使用指定价下单，接口返回订单编号，后续可以用于撤单操作以及查询委托状态
        print("order using the fix price:")
        fix_result_order_id = self.xt_trader.order_stock(
            self.acc,
            stock_code,
            xtconstant.STOCK_BUY,
            quantity,
            xtconstant.FIX_PRICE,
            price,
        )
        print(fix_result_order_id)

    def sell(self, stock_code, price, quantity):
"""Args::
    stock_code: 
    price: 
    quantity:"""
    quantity:"""
        # 买之前得检查仓位
        print("order using the fix price:")
        fix_result_order_id = self.xt_trader.order_stock(
            self.acc,
            stock_code,
            xtconstant.STOCK_SELL,
            quantity,
            xtconstant.FIX_PRICE,
            price,
        )
        print(fix_result_order_id)

    def cancel_order(self, order_id):
"""Args::
    order_id:"""
""""""
""""""
"""Logging function fot this strategy

Args::
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
        data = self.datas[0]
        data._name
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close

                    # self.mbroker.buy(stock_code= stock_code , price=1000,quantity=200)
                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log("SELL CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                # self.mbroker.sell(stock_code=stock_code, price=100)


if __name__ == "__main__":
    store = QMTStore()
    code_list = ["603429.SH"]

    # 添加数据
    datas = store.getdatas(
        code_list=code_list,
        timeframe=bt.TimeFrame.Minutes,
        fromdate=datetime(2020, 1, 1),
        todate=datetime(2021, 1, 1),
        live=False,
    )

    for d in datas:
        # print(len(d))
        cerebro = bt.Cerebro(maxcpus=16)

        cerebro.adddata(d)
        # cerebro.broker = broker

        # 添加策略
        # buy_date = datetime(2022, 8, 1).date()  # 设置固定买入日期
        cerebro.addstrategy(TestStrategy)

        # cerebro.optstrategy

        # # 设置初始资金
        cerebro.broker.setcash(1000000.0)

        # 设置佣金
        cerebro.broker.setcommission(commission=0.001)

        cerebro.run()
        if cerebro.broker.getvalue() != 1000000.0:
            print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
