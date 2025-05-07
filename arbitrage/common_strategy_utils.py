# Copyright (c) 2025 backtrader contributors
"""
Utilities for arbitrage strategies. Includes functions for initialization of
common variables and notification of orders/trades. All comments and docstrings
are broken into up to 90 characters.
"""


def init_common_vars(strategy, extra_vars=None):
    """Initializes common variables for arbitrage strategies. Additionally,
allows initializing extra variables passed in a dictionary.

Args:
    strategy: Strategy instance (self)
    extra_vars: Dictionary of extra variables to initialize"""
    strategy.returns_j = []
    strategy.returns_jm = []
    strategy.order = None
    strategy.position_type = None
    strategy.entry_day = 0
    strategy.dates = []
    if extra_vars:
        for k, v in extra_vars.items():
            setattr(strategy, k, v)


def notify_order_default(strategy, order):
    """Default order notification for arbitrage strategies.

Args:
    strategy: Strategy instance (self)
    order: Received order"""
    if order.status in [order.Completed]:
        if getattr(strategy.p, "printlog", False):
            if order.isbuy():
                print(
                    f"Buy executed: price={order.executed.price:.2f}, "
                    f"cost={order.executed.value:.2f}, "
                    f"comm={order.executed.comm:.2f}"
                )
            else:
                print(
                    f"Sell executed: price={order.executed.price:.2f}, "
                    f"cost={order.executed.value:.2f}, "
                    f"comm={order.executed.comm:.2f}"
                )
    elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        print("Order Canceled/Margin/Rejected")
    strategy.order = None


def notify_trade_default(strategy, trade):
    """Default trade notification for arbitrage strategies.

Args:
    strategy: Strategy instance (self)
    trade: Received trade"""
    if getattr(strategy.p, "printlog", False) and trade.isclosed:
        print(f"Trade PnL: {trade.pnlcomm:.2f}")
