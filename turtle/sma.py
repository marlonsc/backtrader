"""sma.py module.

Description of the module functionality."""


debug = False
win_prob = 0


class SmaCross(bt.SignalStrategy):
""""""
""""""
"""Logging function for this strategy

Args::
    txt: 
    dt: (Default value = None)"""
    dt: (Default value = None)"""
        if debug:
            dt = dt or self.datas[0].datetime.date(0)
            print("%s, %s" % (dt.isoformat(), txt))

    def next(self):
        """在每根K线执行交易检查"""
        if self.crossover[0] > 0:  # 触发买入信号
            self.bar_executed.append(len(self))
            self.log(
                f"📈 SMA{self.params.sma1} 上穿 SMA{self.params.sma2}，触发买入信号."
            )

        if self.crossover[0] < 0:  # 触发买入信号
            self.log(
                f"📉 SMA{self.params.sma1} 下穿 SMA{self.params.sma2}，触发卖出信号."
            )
            self.bar_executed = self.bar_executed[1:]

        if (
            len(self.bar_executed) > 0
            and len(self) >= self.bar_executed[0] + self.params.hold_days
        ):
            self.log(f"⏳ 第{len(self) - self.bar_executed[0]}个周期, 卖出.")
            self.bar_executed = self.bar_executed[1:]
            self.sell()

    def notify_order(self, order):
"""监听订单状态变化

Args::
    order:"""
    order:"""
        # self.log(f"🤖 订单状态变更：{bt.Order.Status[order.status]}")
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            self.log(
                f"{'买入' if order.isbuy() else '卖出'} {order.executed.size} @"
                f" {order.executed.price} | {self.position.size}"
            )

    def notify_trade(self, trade):
"""监听交易完成，输出盈亏

Args::
    trade:"""
    trade:"""
        if trade.isclosed:
            self.log(
                f"🎉 盈利: {trade.pnlcomm:.2f}"
                if trade.pnlcomm > 0
                else f"💔 亏损: {trade.pnlcomm:.2f}"
            )
            if trade.pnlcomm > 0:
                self.win += 1
            else:
                self.loss += 1

    def stop(self):
        """回测结束，输出最终净值"""
        final_value = self.broker.getvalue()
        start_value = self.broker.startingcash
        net_profit = final_value - start_value

        self.log("=" * 30)
        self.log(f"📊 回测结束 - 期末资金: {final_value:.2f}")
        self.log(f"💰 期初资金: {start_value:.2f}")
        self.log(f"🚀 策略净利润: {net_profit:.2f}")
        self.log("=" * 30)
        self.log(f"👍 胜率: {self.win / (self.win + self.loss)}")
        global win_prob
        win_prob = self.win / (self.win + self.loss)


def parse_args(pargs=None):
"""Args::
    pargs: (Default value = None)"""
"""Args::
    data: 
    plot: (Default value = False)
    args: (Default value = {})"""
    args: (Default value = {})"""
    cerebro = bt.Cerebro()
    data0 = bt.feeds.PandasData(
        dataname=data,
        datetime="date",
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
    )
    cerebro.adddata(data0)
    cerebro.addstrategy(SmaCross, **(eval("dict(" + args.strat + ")")))
    cerebro.broker.setcommission(commission=0.005)  # 设置佣金
    cerebro.broker.setcash(50000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=200)
    # cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    cerebro.run()

    profit = cerebro.broker.getvalue() - cerebro.broker.startingcash
    if plot:
        cerebro.plot()
    return profit, win_prob


if __name__ == "__main__":
    pass

    import pandas as pd

    args = parse_args()
    feed = args.feed
    df = pd.read_csv(feed, parse_dates=["date"])
    debug = True
    runstrat(df, True, args)
