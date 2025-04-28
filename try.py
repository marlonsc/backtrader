from xtquant import xtconstant
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from xtquant import xtconstant


class MyXtQuantTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        print("connection lost")
    def on_stock_order(self, order):
        print("on order callback:")
        print(order.stock_code, order.order_status, order.order_sysid)
    def on_stock_asset(self, asset):
        print("on asset callback")
        print(asset.account_id, asset.cash, asset.total_asset)
    def on_stock_trade(self, trade):
        print("on trade callback")
        print(trade.account_id, trade.stock_code, trade.order_id)
    def on_stock_position(self, position):
        print("on position callback")
        print(position.stock_code, position.volume)
    def on_order_error(self, order_error):
        print("on order_error callback")
        print(order_error.order_id, order_error.error_id, order_error.error_msg)
    def on_cancel_error(self, cancel_error):
        print("on cancel_error callback")
        print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)
    def on_order_stock_async_response(self, response):
        print("on_order_stock_async_response")
        print(response.account_id, response.order_id, response.seq)
    def on_account_status(self, status):
        print("on_account_status")
        print(status.account_id, status.account_type, status.status)

class my_broker:
    def __init__(self):
        self.path = r'E:\software\QMT\userdata_mini'  # 使用原始字符串避免转义
        self.session_id = 123456
        self.xt_trader = XtQuantTrader(self.path, self.session_id)
        # 连接QMT交易服务
        callback = MyXtQuantTraderCallback()
        self.acc = StockAccount('39131771')
        self.xt_trader.register_callback(callback)
        # 启动交易线程
        self.xt_trader.start()
        # 建立交易连接，返回0表示连接成功
        connect_result = self.xt_trader.connect()
        if connect_result != 0:
            import sys
            sys.exit('链接失败，程序即将退出 %d' % connect_result)
        # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
        subscribe_result = self.xt_trader.subscribe(self.acc)
        if subscribe_result != 0:
            print('账号订阅失败 %d' % subscribe_result)

    def buy(self, stock_code, price, quantity=200):
        print(1)
        # 调整股票代码格式为SH600000
        #
        stock_code = '600000.SH'
        # 使用指定价下单，接口返回订单编号，后续可以用于撤单操作以及查询委托状态
        print("order using the fix price:")
        fix_result_order_id = self.xt_trader.order_stock(self.acc, stock_code, xtconstant.STOCK_BUY, 200, xtconstant.FIX_PRICE,
                                                    10.5, 'strategy_name', 'remark')
        print(fix_result_order_id)


# 使用示例
broker = my_broker()
# 获取实时价格后下单（建议先获取行情）
broker.buy('600000.SH', 10.5)