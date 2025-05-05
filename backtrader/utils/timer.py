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
    """
    Cria e adiciona um timer à lista de timers pendentes.

    :param pretimers: Lista de timers pendentes
    :param owner: Objeto dono do timer
    :param when: Condição de disparo
    :param offset: Offset do timer
    :param repeat: Repetição
    :param weekdays: Dias da semana
    :param weekcarry: Carregar semana
    :param monthdays: Dias do mês
    :param monthcarry: Carregar mês
    :param allow: Permissão
    :param tzdata: Timezone
    :param strats: Estratégias
    :param cheat: Cheat flag
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais
    :return: Instância de Timer
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
    """
    Agenda um timer para o objeto cerebro.
    :param cerebro: Instância de Cerebro
    :param when: Condição de disparo
    :param offset: Offset do timer
    :param repeat: Repetição
    :param weekdays: Dias da semana
    :param weekcarry: Carregar semana
    :param monthdays: Dias do mês
    :param monthcarry: Carregar mês
    :param allow: Permissão
    :param tzdata: Timezone
    :param strats: Estratégias
    :param cheat: Cheat flag
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais
    :return: Instância de Timer
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
    """
    Notificação de timer (stub para interface futura).
    :param timer: Instância de Timer
    :param when: Momento do timer
    :param *args: Args adicionais
    :param **kwargs: Kwargs adicionais
    """
    pass
