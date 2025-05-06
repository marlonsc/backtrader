# Copyright (c) 2025 backtrader contributors
"""
Funções utilitárias de iteração para uso geral no framework backtrader.
Todas as funções e docstrings devem ser line-wrap ≤ 90 caracteres.
"""

import collections

from .py3 import string_types

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections


def iterize(iterable):
    """Transforma elementos em iteráveis, exceto strings, para facilitar loops
    genéricos. Strings são encapsuladas em tuplas. Outros elementos não
    iteráveis também são encapsulados em tuplas.

    :param iterable: Objeto iterável ou elemento único
    :returns: Lista de iteráveis

    """
    niterable = list()
    for elem in iterable:
        if isinstance(elem, string_types):
            elem = (elem,)
        elif not isinstance(elem, collectionsAbc.Iterable):
            elem = (elem,)
        niterable.append(elem)
    return niterable
