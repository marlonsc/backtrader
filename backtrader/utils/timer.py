# Copyright (c) 2025 backtrader contributors
"""
Utilitários para manipulação de timers no backtrader.
Todas as funções e docstrings devem ser line-wrap ≤ 90 caracteres.
"""

import datetime

from ..timer import Timer


def create_timer(
    pretimers,
    owner,
    when,
    offset=datetime.timedelta(),
    repeat=datetime.timedelta(),
    weekdays=None,
    weekcarry=False,
    monthdays=None,
    monthcarry=True,
    allow=None,
    tzdata=None,
    strats=False,
    cheat=False,
    *args,
    **kwargs,
):
    """Cria e adiciona um timer à lista de timers pendentes.

    :param pretimers: Lista de timers pendentes
    :param owner: Objeto dono do timer
    :param when: Condição de disparo
    :param offset: Offset do timer (Default value = datetime.timedelta())
    :param repeat: Repetição (Default value = datetime.timedelta())
    :param weekdays: Dias da semana (Default value = None)
    :param weekcarry: Carregar semana (Default value = False)
    :param monthdays: Dias do mês (Default value = None)
    :param monthcarry: Carregar mês (Default value = True)
    :param allow: Permissão (Default value = None)
    :param tzdata: Timezone (Default value = None)
    :param strats: Estratégias (Default value = False)
    :param cheat: Cheat flag (Default value = False)
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais
    :returns: Instância de Timer

    """
    if weekdays is None:
        weekdays = []
    if monthdays is None:
        monthdays = []
    timer = Timer(
        tid=len(pretimers),
        owner=owner,
        strats=strats,
        when=when,
        offset=offset,
        repeat=repeat,
        weekdays=weekdays,
        weekcarry=weekcarry,
        monthdays=monthdays,
        monthcarry=monthcarry,
        allow=allow,
        tzdata=tzdata,
        cheat=cheat,
        *args,
        **kwargs,
    )
    pretimers.append(timer)
    return timer


def schedule_timer(
    cerebro,
    when,
    offset=datetime.timedelta(),
    repeat=datetime.timedelta(),
    weekdays=None,
    weekcarry=False,
    monthdays=None,
    monthcarry=True,
    allow=None,
    tzdata=None,
    strats=False,
    cheat=False,
    *args,
    **kwargs,
):
    """Agenda um timer para o objeto cerebro.

    :param cerebro: Instância de Cerebro
    :param when: Condição de disparo
    :param offset: Offset do timer (Default value = datetime.timedelta())
    :param repeat: Repetição (Default value = datetime.timedelta())
    :param weekdays: Dias da semana (Default value = None)
    :param weekcarry: Carregar semana (Default value = False)
    :param monthdays: Dias do mês (Default value = None)
    :param monthcarry: Carregar mês (Default value = True)
    :param allow: Permissão (Default value = None)
    :param tzdata: Timezone (Default value = None)
    :param strats: Estratégias (Default value = False)
    :param cheat: Cheat flag (Default value = False)
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais
    :returns: Instância de Timer

    """
    return create_timer(
        cerebro._pretimers,
        owner=cerebro,
        when=when,
        offset=offset,
        repeat=repeat,
        weekdays=weekdays,
        weekcarry=weekcarry,
        monthdays=monthdays,
        monthcarry=monthcarry,
        allow=allow,
        tzdata=tzdata,
        strats=strats,
        cheat=cheat,
        *args,
        **kwargs,
    )


def notify_timer(timer, when, *args, **kwargs):
    """Notificação de timer (stub para interface futura).

    :param timer: Instância de Timer
    :param when: Momento do timer
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais

    """
