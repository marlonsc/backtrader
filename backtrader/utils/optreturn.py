# Copyright (c) 2025 backtrader contributors
"""
Classe utilitária OptReturn para encapsular resultados de otimização.
Docstrings e comentários devem ser line-wrap ≤ 90 caracteres.
"""


class OptReturn(object):
    """
    Container para resultados de otimização de estratégias.

    :param params: Parâmetros da estratégia
    :param **kwargs: Atributos adicionais a serem armazenados
    """

    def __init__(self, params, **kwargs):
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)
