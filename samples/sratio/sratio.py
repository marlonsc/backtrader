"""sratio.py module.

Description of the module functionality."""

# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import argparse
import itertools
import math
import operator
import sys

if sys.version_info.major == 2:
    map = itertools.imap


def average(x):
"""Args::
    x:"""
"""Args::
    x:"""
"""Args::
    x:"""
"""Args::
    pargs: (Default value = None)"""
"""Args::
    pargs: (Default value = None)"""
    pargs: (Default value = None)"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Sample Sharpe Ratio",
    )

    parser.add_argument(
        "--ret1",
        required=False,
        action="store",
        type=float,
        default=0.023286,
        help="Annual Return 1",
    )

    parser.add_argument(
        "--ret2",
        required=False,
        action="store",
        type=float,
        default=0.0257816485323,
        help="Annual Return 2",
    )

    parser.add_argument(
        "--riskfreerate",
        required=False,
        action="store",
        type=float,
        default=0.01,
        help="Risk free rate (decimal) for the Sharpe Ratio",
    )

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == "__main__":
    run()
