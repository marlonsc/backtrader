import collections

# 导入队列工具和元类工具
import random

from backtrader import BrokerBase, CommInfoBase, Order, OrderBase

# 从backtrader框架导入经纪商基类和订单基类
from backtrader.position import Position

# 导入仓位管理类
from xtquant import xttype

# 随机数生成模块
from xtquant.xttrader import XtQuantTrader

# 导入QMT交易接口
from xtquant.xttype import StockAccount

# 导入股票账户类型
from .qmtstore import QMTStore

# 导入自定义的QMT存储类


# 自定义的QMT订单类，继承自backtrader的订单基类
class QMTOrder(OrderBase):
    """ """

    def __init__(self, owner, data, ccxt_order):
        """Args:
    owner: 
    data: 
    ccxt_order:"""

        self.owner = owner
        self.data = data
        self.ccxt_order = ccxt_order
        self.executed_fills = []
        self.ordtype = self.Buy if ccxt_order["side"] == "buy" else self.Sell
        self.size = float(ccxt_order["amount"])
        self._orders = {}  # 跟踪活跃订单 {order_id: QMTOrder}

        super(QMTOrder, self).__init__()


class MetaQMTBroker(BrokerBase.__class__):
    """ """

    def __init__(cls, name, bases, dct):
        """Class has already been created ... register

Args:
    name: 
    bases: 
    dct:"""
        # Initialize the class
        super(MetaQMTBroker, cls).__init__(name, bases, dct)
        QMTStore.BrokerCls = cls


class StockCommission(CommInfoBase):
    """ """

    params = (
        ("commission", 0.0003),  # 万三佣金
        ("stocklike", True),  # 股票模式（按数量计算）
    )


class QMTBroker(BrokerBase, metaclass=MetaQMTBroker):
    """ """

    def __init__(self, **kwargs):
        """"""

        super(QMTBroker, self).__init__()  # 关键：调用父类初始化
        StockCommission()
        self.setcommission()
        self.store = QMTStore(**kwargs)
        self.mini_qmt_path = kwargs.get("mini_qmt_path")
        self.account_id = kwargs.get("account_id")
        self.num = 1
        self._orders = {}
        self.notifs = collections.deque()
        if not self.mini_qmt_path:
            raise ValueError("mini_qmt_path 参数未提供")
        if not self.account_id:
            raise ValueError("account_id 参数未提供")

        session_id = int(random.randint(100000, 999999))

        xt_trader = XtQuantTrader(self.mini_qmt_path, session_id)
        # 启动交易对象
        xt_trader.start()
        # 连接客户端
        connect_result = xt_trader.connect()

        if connect_result == 0:
            print("连接成功1")

        account = StockAccount(self.account_id)
        # 订阅账号
        xt_trader.subscribe(account)

        self.xt_trader = xt_trader
        self.account = account

    def setcash(self, cash):
        """Args:
    cash:"""
        self.cash = cash
        self.value = cash

    def query_stock_asset(self, account):
        """Args:
    account:"""
        return self.cash

    def getcash(self):
        """ """
        self.query_stock_asset(self.account)

        # self.cash = res.cash

        return self.cash

    def getvalue(self, datas=None):
        """Args:
    datas: (Default value = None)"""

        # res = self.query_stock_asset(self.account)

        # self.value = res.market_value

        return self.value

    def getposition(self, data, clone=True):
        """Args:
    data: 
    clone: (Default value = True)"""

        xt_position = self.xt_trader.query_stock_position(self.account, data._dataname)
        pos = Position(size=xt_position.volume, price=xt_position.avg_price)
        return pos

    def get_notification(self):
        """ """
        try:
            return self.notifs.popleft()
        except IndexError:
            pass

        return None

    def notify(self, order):
        """Args:
    order:"""
        self.notifs.append(order.clone())

    def next(self):
        """ """
        # comminfo = self.broker.getcommissioninfo(self.data)
        for order_id in list(self._orders.keys()):
            qmt_order = self.xt_trader.query_order(self.account, order_id)
            bt_order = self._orders[order_id]

            if qmt_order.status == xttype.ORDER_STATUS_FILLED:
                bt_order.completed()  # 标记为已完成
                self.notify(bt_order)
                del self._orders[order_id]
            elif qmt_order.status == xttype.ORDER_STATUS_CANCELED:
                bt_order.cancel()
                self.notify(bt_order)
                del self._orders[order_id]

    def buy(
        self,
        owner,
        data,
        size,
        price=None,
        plimit=None,
        exectype=None,
        valid=None,
        tradeid=0,
        oco=None,
        trailamount=None,
        trailpercent=None,
        **kwargs,
    ):
        """Args:
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)
    oco: (Default value = None)
    trailamount: (Default value = None)
    trailpercent: (Default value = None)"""
        order = {
            "stock_code": data._dataname,  # 股票代码（如 '600000.SH'）
            "order_type": (
                xttype.LIMIT_ORDER if exectype == Order.Limit else xttype.MARKET_ORDER
            ),
            "order_volume": int(size),  # 数量（QMT需要整数）
            "price": price or 0,  # 市价单传0
            "side": xttype.SIDE_BUY,  # 买入方向
        }

        # 调用QMT接口下单
        order_id = self.xt_trader.order(self.account, order)

        # 创建Backtrader订单对象
        bt_order = QMTOrder(owner, data, order_id)
        bt_order.submit()  # 标记为已提交
        self.notify(bt_order)  # 发送通知

        return bt_order

    def sell(
        self,
        owner,
        data,
        size,
        price=None,
        plimit=None,
        exectype=None,
        valid=None,
        tradeid=0,
        oco=None,
        trailamount=None,
        trailperc7ent=None,
        **kwargs,
    ):
        """Args:
    owner: 
    data: 
    size: 
    price: (Default value = None)
    plimit: (Default value = None)
    exectype: (Default value = None)
    valid: (Default value = None)
    tradeid: (Default value = 0)
    oco: (Default value = None)
    trailamount: (Default value = None)
    trailperc7ent: (Default value = None)"""
        order = {
            "stock_code": data._dataname,
            "order_type": (
                xttype.LIMIT_ORDER if exectype == Order.Limit else xttype.MARKET_ORDER
            ),
            "order_volume": int(size),
            "price": price or 0,
            "side": xttype.SIDE_SELL,
        }
        order_id = self.xt_trader.order(self.account, order)
        bt_order = QMTOrder(owner, data, order_id)
        bt_order.submit()
        self.notify(bt_order)
        return bt_order

    def cancel(self, order):
        """Args:
    order:"""
        self.xt_trader.cancel_order(self.account, order.ccxt_order)
        order.cancel()  # 标记为已取消
        self.notify(order)
