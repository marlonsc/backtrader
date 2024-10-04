# -*- coding: UTF-8 -*-
# Source: https://www.backtrader.com/docu/quickstart/quickstart/#basic-setup

# import
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt

# globals

# functions


if __name__ == '__main__':

    cerebro = bt.Cerebro()

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
