# Copyright (c) 2025 backtrader contributors
"""
Funções utilitárias para inicialização e manipulação de objetos Params.
Docstrings e comentários devem ser line-wrap ≤ 90 caracteres.
"""


def make_params(params_tuple):
    """Cria dinamicamente uma classe Params a partir de um tuple de pares (nome, valor).

    :param params_tuple: Tupla de pares (nome, valor) de parâmetros
    :returns: Instância de Params com atributos correspondentes

    """
    param_dict = dict((k, v) for k, v in params_tuple)
    return type("Params", (), param_dict)()
