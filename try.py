from sko.GA import GA

import backtrader as bt
from qmtbt import QMTStore
from datetime import datetime
from xtquant import xtdata, xtconstant
import math
import backtrader as bt
from strategies import TestStrategy, AnotherStrategy ,my_broker
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
import optuna
from strategies import *
def finetune(Strategy, method='Sko', stocks=['000001.SZ'],
             timeframe=bt.TimeFrame.Days, fromdate=datetime(2020, 1, 1),
             todate=datetime(2020, 4, 1), count=1):
    """为每个股票优化独立参数"""
    store = QMTStore()
    optimized_params = {}

    # 获取策略可优化参数列表
    default_params = {
        name: value for name, value in Strategy.params._getitems()
        if not name.startswith('_') and name not in ['signals', 'use_real_trading']
    }
    param_names = list(default_params.keys())

    # 单股票优化函数
    def optimize_single_stock(stock):
        # 加载单股票数据
        data = store.getdata(dataname=stock, timeframe=timeframe,
                             fromdate=fromdate, todate=todate, live=False)

        # 优化逻辑
        if method == 'Sko':
            n_dim = len(param_names)
            lb = [1] * n_dim
            ub = [50] * n_dim

            def backtest(p):
                param_dict = {name: int(round(value)) for name, value in zip(param_names, p)}
                cerebro = bt.Cerebro()
                cerebro.adddata(data)
                cerebro.addstrategy(Strategy,  ** param_dict)
                cerebro.broker.setcash(1000000)
                cerebro.broker.setcommission(0.00025)
                cerebro.run()
                return -cerebro.broker.getvalue()

            ga = GA(func=backtest, n_dim=n_dim, size_pop=10, max_iter=count, prob_mut=0.001, lb=lb, ub=ub, precision=1e-7)
            best_x, _ = ga.run()
            return {k: int(v) for k, v in zip(param_names, best_x)}

        elif method == 'Optuna':
            def objective(trial):
                params = {name: trial.suggest_int(name, 1, 50)
                          for name in param_names}
                cerebro = bt.Cerebro()
                cerebro.adddata(data)
                cerebro.addstrategy(Strategy,  ** params)
                cerebro.broker.setcash(1000000)
                cerebro.broker.setcommission(0.00025)
                cerebro.run()
                return cerebro.broker.getvalue()

            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=count)
            return study.best_params

    # 为每个股票独立优化
    for stock in stocks:
        print(f"\n开始优化股票 {stock}")
        optimized_params[stock] = optimize_single_stock(stock)
        print(f"优化完成，参数：{optimized_params[stock]}")

    return optimized_params


def back_test(selected_strategy,

              optimized_params,
              use_real_trading=False,
              live=False,
              stocks=['000001.SZ'],
              fromdate=datetime(2020, 1, 1),
              todate=datetime(2020, 4, 1),
              ):
    """多股票独立参数回测"""

    store = QMTStore()

    results={}

    for stock in stocks:
        cerebro = bt.Cerebro()
        # 加载数据
        data = store.getdata(
            dataname=stock,
            timeframe=bt.TimeFrame.Days,
            fromdate=fromdate,
            todate=todate,
            live=live
        )
        cerebro.adddata(data)

        # 添加带独立参数的策略
        cerebro.addstrategy(
            selected_strategy,
            **optimized_params[stock],
            use_real_trading=use_real_trading
        )

        # 资金管理
        cerebro.broker.setcash(1000000.0)
        cerebro.broker.setcommission(commission=0.001)

    # 运行回测
        cerebro.run()
        cerebro.plot(style='candlestick', iplot=False)
        print(f"\n总资产: {cerebro.broker.getvalue():.2f}")
        results[stock] = cerebro.broker.getvalue()
    for stock, total_value in results.items():
        print(f"{stock} 总资产: {total_value:.2f}")

    return cerebro


if __name__ == '__main__':
    stra=TestStrategy

    # Sko 多只股票同时测试，得到多组参数
    # optuna_params = finetune(
    #     SmaCross,
    #     method='Sko',
    #     stocks=['600519.SH', '000001.SZ', '300750.SZ'],
    #     count=1
    # )
    # print(optuna_params)


    # Optuna 多只股票同时测试，得到多组参数
    optuna_params = finetune(
        stra,
        method='Optuna',
        stocks=['600519.SH'],
        count=1
    )
    print(optuna_params)

    # back_test(
    #     selected_strategy=stra,
    #     stocks=['600519.SH', '000001.SZ', '300750.SZ'],
    #     optimized_params=optuna_params,
    #
    # )



    # 使用优化参数进行测试,可以传入count来控制迭代次数
    # back_test(
    #     selected_strategy=stra,
    #     optimized_params=optuna_params,
    #     use_real_trading=False,
    #     stocks=['600519.SH']  # 使用与优化时相同的标的
    # )

    # use_real_trading=True 则是真实发送订单
    # back_test(
    #     selected_strategy=stra,
    #     optimized_params=optuna_params,
    #     use_real_trading=True,
    #     stocks=['600519.SH']  # 使用与优化时相同的标的
    # )


# 实时交易，但不能多只股票同时
    # back_test(
    #     selected_strategy=stra,
    #     optimized_params=optuna_params,
    #     use_real_trading=True,
    #     stocks=['600519.SH'],  # 使用与优化时相同的标的
    #     live=True
    # )















