# strategies.py
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
    """ """

    def on_disconnected(self):
        """ """
        print("[连接状态] 与交易服务器连接断开")

    def on_stock_order(self, order):
        """

        :param order:

        """
        print("\n[委托单回调] 订单状态更新")
        print(f"证券代码: {order.stock_code}")
        print(f"订单状态: {order.order_status}")  # 需根据券商文档映射状态码含义
        print(f"系统订单号: {order.order_sysid}")

    def on_stock_asset(self, asset):
        """

        :param asset:

        """
        print("\n[账户资产] 资金变动通知")
        print(f"账户ID: {asset.account_id}")
        print(f"可用资金: {asset.cash}")
        print(f"总资产估值: {asset.total_asset}")

    def on_stock_trade(self, trade):
        """

        :param trade:

        """
        print("\n[成交记录] 交易已达成")
        print(f"账户ID: {trade.account_id}")
        print(f"证券代码: {trade.stock_code}")
        print(f"关联订单号: {trade.order_id}")

    def on_stock_position(self, position):
        """

        :param position:

        """
        print("\n[持仓变动] 头寸更新")
        print(f"证券代码: {position.stock_code}")
        print(f"当前持仓量: {position.volume}")

    def on_order_error(self, order_error):
        """

        :param order_error:

        """
        print("\n[委托失败] 订单提交错误")
        print(f"错误订单号: {order_error.order_id}")
        print(f"错误代码: {order_error.error_id}")
        print(f"错误详情: {order_error.error_msg}")  # 建议根据error_id映射具体原因

    def on_cancel_error(self, cancel_error):
        """

        :param cancel_error:

        """
        print("\n[撤单失败] 取消订单错误")
        print(f"目标订单号: {cancel_error.order_id}")
        print(f"错误代码: {cancel_error.error_id}")
        print(f"错误信息: {cancel_error.error_msg}")

    def on_order_stock_async_response(self, response):
        """

        :param response:

        """
        print("\n[异步响应] 委托请求已受理")
        print(f"账户ID: {response.account_id}")
        print(f"订单号: {response.order_id}")
        print(f"请求序列号: {response.seq}")

    def on_account_status(self, status):
        """

        :param status:

        """
        print("\n[账户状态] 登录/连接状态变化")
        print(f"账户ID: {status.account_id}")
        print(f"账户类型: {status.account_type}")  # 如普通户/信用户
        print(f"当前状态: {status.status}")
        # 需映射状态码（如已连接/断开）


class my_broker:
    """ """

    def __init__(self, use_real_trading=False):
        """

        :param use_real_trading:  (Default value = False)

        """
        self.path = r"E:\software\QMT\userdata_mini"
        self.session_id = 123456
        self.xt_trader = XtQuantTrader(self.path, self.session_id)
        callback = MyXtQuantTraderCallback()
        self.acc = StockAccount("39131771")
        self.xt_trader.register_callback(callback)
        self.use_real_trading = use_real_trading  # Added flag to determine if it's real trading

        if use_real_trading:  # Only connect if it's real trading
            self.xt_trader.start()
            connect_result = self.xt_trader.connect()
            if connect_result != 0:
                import sys

                sys.exit("链接失败，程序即将退出 %d" % connect_result)
            subscribe_result = self.xt_trader.subscribe(self.acc)
            if subscribe_result != 0:
                print("账号订阅失败 %d" % subscribe_result)

    def buy(self, stock_code, price, quantity):
        """

        :param stock_code:
        :param price:
        :param quantity:

        """
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
        """

        :param stock_code:
        :param price:
        :param quantity:

        """
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
        """

        :param order_id:

        """
        if self.use_real_trading:
            self.xt_trader.cancel_order_stock(self.acc, order_id)

    def query(self):
        """ """
        if self.use_real_trading:
            order = self.xt_trader.query_stock_orders(self.acc, False)
            return order


class TestStrategy(bt.Strategy):
    """ """

    params = (
        ("use_real_trading", False),  #
        ("any", 50),
    )

    def log(self, txt, dt=None):
        """

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close
        self.order = None
        self.mbroker = my_broker(
            use_real_trading=self.p.use_real_trading
        )  # 默认不使用实盘

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("BUY EXECUTED, %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, %.2f" % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def next(self):
        """ """

        data = self.datas[0]
        stock_code = data._name
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        if not self.position:
            if self.dataclose[0] < self.dataclose[-1]:
                if self.dataclose[-1] < self.dataclose[-2]:
                    # 模拟下单
                    self.mbroker.buy(stock_code=stock_code, price=1, quantity=200)
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])
                    self.order = self.buy()

        else:
            if len(self) >= (self.bar_executed + 5):
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class AnotherStrategy(bt.Strategy):
    """ """

    params = (
        ("period1", 10),
        ("period2", 30),
        ("period3", 30),
        ("use_real_trading", False),
    )

    def log(self, txt, dt=None):
        """

        :param txt:
        :param dt:  (Default value = None)

        """
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """ """
        self.dataclose = self.datas[0].close
        self.order = None
        self.mbroker = my_broker(
            use_real_trading=self.p.use_real_trading
        )  # 默认不使用实盘

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("BUY EXECUTED, %.2f" % order.executed.price)
            elif order.issell():
                self.log("SELL EXECUTED, %.2f" % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def next(self):
        """ """
        data = self.datas[0]
        stock_code = data._name
        self.log("Close, %.2f" % self.dataclose[0])

        if self.order:
            return

        if not self.position:
            if self.dataclose[0] > self.dataclose[-1]:
                if self.dataclose[-1] > self.dataclose[-2]:
                    # 模拟下单
                    self.mbroker.buy(stock_code=stock_code, price=1000, quantity=200)
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])
                    self.order = self.buy()

        else:
            if len(self) >= (self.bar_executed + 5):
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


class SmaCross(bt.SignalStrategy):
    """ """

    params = (
        ("period1", 10),
        ("period2", 30),
        ("use_real_trading", False),
    )

    def __init__(self):
        """ """
        sma1, sma2 = (
            bt.ind.SMA(period=self.p.period1),
            bt.ind.SMA(period=self.p.period2),
        )
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)
