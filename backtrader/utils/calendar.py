# Copyright (c) 2025 backtrader contributors
"""
Utilitários para manipulação de calendário e timezone no backtrader.
Todas as funções e docstrings devem ser line-wrap ≤ 90 caracteres.
"""

from ..tradingcal import PandasMarketCalendar, TradingCalendarBase
from ..utils.py3 import string_types


def addcalendar(cal):
    """
    Instancia e retorna um calendário de negociação global a partir de diferentes
    tipos de entrada (string, instância, classe, etc).

    :param cal: String, instância ou classe de calendário
    :return: Instância de calendário
    """
    if isinstance(cal, string_types):
        calobj = PandasMarketCalendar()
        calobj.p.calendar = cal
        return calobj
    elif hasattr(cal, "valid_days"):
        calobj = PandasMarketCalendar()
        calobj.p.calendar = cal
        return calobj
    else:
        try:
            if issubclass(cal, TradingCalendarBase):
                return cal()
        except TypeError:  # já é instância
            pass
    return cal


def addtz(params, tz):
    """
    Define o timezone global nos parâmetros do sistema.

    :param params: Objeto de parâmetros
    :param tz: Timezone (None, string, int, pytz)
    """
    params.tz = tz
