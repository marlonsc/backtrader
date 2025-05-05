# -*- coding: UTF-8 -*-
# Source: https://www.backtrader.com/docu/quickstart/quickstart/#basic-setup
# In this example:
#   - backtrader will be imported
#   - The Cerebro engine will be instantiated
#   - The resulting cerebro instance will be told to run (loop over data)
#   - And the resulting outcome will be printed out

# import
import backtrader as bt

# globals

# functions


if __name__ == "__main__":

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(66_000)

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}€")

    cerebro.run()

    print(f"Final Portfolio Value: {cerebro.broker.getvalue():,.2f}€")
