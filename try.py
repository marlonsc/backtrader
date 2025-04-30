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
def finetune(Strategy, method='Sko', stock='000001.SH', timeframe=bt.TimeFrame.Days, fromdate=datetime(2020, 1, 1),
             todate=datetime(2021, 1, 1)):
    print('test beginning')
    store = QMTStore()
    data = store.getdata(dataname=stock, timeframe=timeframe, fromdate=fromdate,
                         todate=todate, live=False)
    strategy_params = Strategy.params
    param_names = []
    for param_name in strategy_params._getitems():
        if not param_name[0].startswith('_') and param_name[0]!='signals':  # 过滤掉以_开头的默认参数
            param_names.append(param_name[0])
    print(param_names)
    if len(param_names) == 0:
        print('no param')
        return 0
    # if len(param_names) == 0:
    #     print('no param')
    #     return 0
    if method == 'Sko':
        # 获取策略的参数

        # 确保参数数量和范围正确
        n_dim = len(param_names)
        lb = [1] * n_dim  # 假设所有参数的最小值为1
        ub = [50] * n_dim  # 假设所有参数的最大值为50

        def backtest(p) -> float:
            # 将参数列表转换为字典
            param_dict = {name: int(value) for name, value in zip(param_names, p)}
            cerebro = bt.Cerebro()
            cerebro.adddata(data)
            # 动态解包参数字典到策略类
            cerebro.addstrategy(Strategy,  ** param_dict)
            start_cash = 1000000
            cerebro.broker.setcash(start_cash)
            cerebro.broker.setcommission(commission=0.00025)
            cerebro.run()
            end_value = cerebro.broker.getvalue()
            print(-(start_cash - end_value))
            return -(start_cash - end_value)

        from sko.GA import GA
        ga = GA(func=backtest, n_dim=n_dim, size_pop=10, max_iter=10, prob_mut=0.001, lb=lb, ub=ub, precision=1e-7)
        best_x, best_y = ga.run()
        print('best_x:', best_x, '\n', 'best_y:', best_y)

    if method == 'Optuna':
        param_range = (1, 50)
        def backtest(trial) -> float:
            strategy_params = param_names
            param_dict = {name: trial.suggest_int(name, *param_range) for name in strategy_params}
            strategy = SmaCross
            cerebro = bt.Cerebro()
            cerebro.adddata(data)
            cerebro.addstrategy(strategy,**param_dict)
            start_cash = 1000000
            cerebro.broker.setcash(start_cash)
            cerebro.broker.setcommission(commission=0.00025)
            cerebro.run()
            return start_cash - cerebro.broker.getvalue()

        study = optuna.create_study(direction='maximize')
        study.optimize(backtest, n_trials=100, n_jobs=1)
        trial = study.best_trial

        print("\tBest Score: {}".format(trial.value))
        print("\tBest Params: {}".format(trial.params))



if __name__ == '__main__':
    # use_real_trading =True  # 设置是否为实盘操作
    # selected_strategy = TestStrategy  # 用户选择的策略
    #
    # store = QMTStore()
    # code_list = ['603429.SH']
    #
    # datas = store.getdatas(code_list=code_list, timeframe=bt.TimeFrame.Minutes, fromdate=datetime(2020, 1, 1),
    #                        todate=datetime(2021, 1, 1), live=False)
    #
    # for d in datas:
    #     cerebro = bt.Cerebro(maxcpus=16)
    #
    #     cerebro.adddata(d)
    #     if use_real_trading:
    #         cerebro.mbroker = my_broker(use_real_trading=True)
    #     cerebro.addstrategy(selected_strategy)  # 根据用户选择添加策略
    #
    #     cerebro.broker.setcash(1000000.0)
    #     cerebro.broker.setcommission(commission=0.001)
    #
    #     # 实盘操作
    #
    #     cerebro.run()
    #
    #     print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    finetune(SmaCross,method='Optuna',stock='600519.SH')  # 简单测试
    # finetune(AnotherStrategy)  # 真实回测
    # finetune(TestStrategy) # no param