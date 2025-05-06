# Copyright (c) 2025 backtrader contributors
"""
Classe utilitária OptReturn para encapsular resultados de otimização.
Docstrings e comentários devem ser line-wrap ≤ 90 caracteres.
"""


class OptReturn(object):
    """Container para resultados de otimização de estratégias."""

    def __init__(self, params, **kwargs):
        """

        :param params: 
        :param **kwargs: 

        """
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)
