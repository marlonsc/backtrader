"""
ATR Arbitrage Strategy for Backtrader

Implements a pair trading strategy using ATR and SMA bands on the price difference
between two instruments.
"""
import pandas as pd
import datetime
import backtrader as bt
from backtrader.feeds import PandasData
from backtrader.indicators.atr import AverageTrueRange as ATR
from backtrader.indicators.sma import MovingAverageSimple as SMA
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.returns import Returns


class ATRArbitrageStrategy(bt.Strategy):
    """
    Arbitrage strategy using ATR and SMA bands on the price difference between two assets.
    """

    params = (
        ("atr_period", 14),  # ATR周期
        ("atr_multiplier", 2.0),  # ATR乘数
        ("printlog", False),
    )

    def __init__(self):
        super().__init__()
        # 计算价差
        self.price_diff = self.data0.close - 1.4 * self.data1.close

        # 计算价差ATR
        self.price_diff_atr = ATR(data=self.data0, period=self.p.atr_period)  # pylint: disable=unexpected-keyword-arg

        # 计算价差移动平均
        self.price_diff_ma = SMA(data=self.price_diff, period=self.p.atr_period)  # pylint: disable=unexpected-keyword-arg

        # 计算上下轨
        self.upper_band = (
            self.price_diff_ma + self.p.atr_multiplier * self.price_diff_atr
        )
        self.lower_band = (
            self.price_diff_ma - self.p.atr_multiplier * self.price_diff_atr
        )

        # 交易相关变量
        self.order = None
        self.position_type = None

    def next(self):
        """ """
        if self.order:
            return

        # 交易逻辑
        if self.position:
            # 平仓条件
            if (
                self.position_type == "long_j_short_jm"
                and self.price_diff[0] >= self.price_diff_ma[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"平仓: 价差={self.price_diff[0]:.2f},"
                        f" ATR={self.price_diff_atr[0]:.2f}"
                    )

            elif (
                self.position_type == "short_j_long_jm"
                and self.price_diff[0] <= self.price_diff_ma[0]
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"平仓: 价差={self.price_diff[0]:.2f},"
                        f" ATR={self.price_diff_atr[0]:.2f}"
                    )

        else:
            # 开仓条件
            if self.price_diff[0] >= self.upper_band[0]:
                # 做空J，做多JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.position_type = "short_j_long_jm"
                if self.p.printlog:
                    print(
                        f"开仓: 做空J，做多JM, 价差={self.price_diff[0]:.2f},"
                        f" ATR={self.price_diff_atr[0]:.2f}"
                    )

            elif self.price_diff[0] <= self.lower_band[0]:
                # 做多J，做空JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.position_type = "long_j_short_jm"
                if self.p.printlog:
                    print(
                        f"开仓: 做多J，做空JM, 价差={self.price_diff[0]:.2f},"
                        f" ATR={self.price_diff_atr[0]:.2f}"
                    )

    def notify_order(self, order):
        """

        :param order:

        """
        if order.status in [order.Completed]:
            if self.p.printlog:
                if order.isbuy():
                    print(
                        f"买入执行: 价格={order.executed.price:.2f},"
                        f" 成本={order.executed.value:.2f},"
                        f" 手续费={order.executed.comm:.2f}"
                    )
                else:
                    print(
                        f"卖出执行: 价格={order.executed.price:.2f},"
                        f" 成本={order.executed.value:.2f},"
                        f" 手续费={order.executed.comm:.2f}"
                    )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("订单被取消/拒绝")

        self.order = None


def load_data(symbol1, symbol2, fromdate, todate):
    """
    Load two symbols from HDF5 and return as Backtrader PandasData feeds.
    """
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
    df1 = pd.read_hdf(output_file, key=symbol2).reset_index()

    date_col = [col for col in df0.columns if "date" in col.lower()]
    if not date_col:
        raise ValueError("数据集中未找到日期列")

    df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
    df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
    df0 = df0.sort_index().loc[fromdate:todate]
    df1 = df1.sort_index().loc[fromdate:todate]

    data0 = PandasData(dataname=df0)
    data1 = PandasData(dataname=df1)
    return data0, data1


def run_strategy():
    """ """
    # 创建回测引擎
    cerebro = bt.Cerebro()

    # 设置初始资金
    cerebro.broker.setcash(150000)

    # 设置滑点
    cerebro.broker.set_slippage_perc(perc=0.0005)  # 设置0.05%的滑点

    # 设置手续费
    cerebro.broker.setcommission(commission=0.0003)

    cerebro.broker.set_shortcash(False)

    # 加载数据
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)
    data0, data1 = load_data("/J", "/JM", fromdate, todate)

    if data0 is None or data1 is None:
        print("无法加载数据，请检查文件路径和数据格式")
        return

    # 添加数据
    cerebro.adddata(data0, name="J")
    cerebro.adddata(data1, name="JM")

    # 添加策略
    cerebro.addstrategy(ATRArbitrageStrategy, printlog=True)

    # 添加分析器
    cerebro.addanalyzer(SharpeRatio, _name="sharpe_ratio")
    cerebro.addanalyzer(DrawDown, _name="drawdown")
    cerebro.addanalyzer(Returns, _name="returns")

    # 运行回测
    print("初始资金: %.2f" % cerebro.broker.getvalue())
    results = cerebro.run()
    print("最终资金: %.2f" % cerebro.broker.getvalue())

    # 打印分析结果
    strat = results[0]
    sharpe = strat.analyzers.sharpe_ratio.get_analysis().get("sharperatio", 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)
    returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0)
    print("夏普比率:", sharpe)
    print("最大回撤:", drawdown)
    print("年化收益率:", returns)

    # 使用backtrader原生绘图
    cerebro.plot()


if __name__ == "__main__":
    run_strategy()
