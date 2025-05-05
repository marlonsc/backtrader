# Copyright (c) 2025 backtrader contributors
"""
Utilitários para estratégias de arbitragem. Inclui funções para inicialização de
variáveis comuns e notificação de ordens/trades. Todos os comentários e docstrings
são quebrados em até 90 caracteres.
"""

def init_common_vars(strategy, extra_vars=None):
    """
    Inicializa variáveis comuns para estratégias de arbitragem. Adicionalmente,
    permite inicializar variáveis extras passadas em um dicionário.

    :param strategy: Instância da estratégia (self)
    :param extra_vars: Dicionário de variáveis extras a inicializar
    """
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
    """
    Notificação padrão de ordens para estratégias de arbitragem.

    :param strategy: Instância da estratégia (self)
    :param order: Ordem recebida
    """
    if order.status in [order.Completed]:
        if getattr(strategy.p, 'printlog', False):
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
    """
    Notificação padrão de trades para estratégias de arbitragem.

    :param strategy: Instância da estratégia (self)
    :param trade: Trade recebido
    """
    if getattr(strategy.p, 'printlog', False) and trade.isclosed:
        print(f"Trade PnL: {trade.pnlcomm:.2f}")
