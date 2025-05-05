import datetime
import os
import sys

import backtrader as bt  # Import Backtrader
from backtest.feeds.datafeeds import StockCsvData
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo


# Create strategy
class TestStrategy(bt.Strategy):
    """
    TestStrategy: Example Backtrader strategy for demonstration and testing purposes.
    All comments and docstrings are in English and follow Neptor/GEN-AI guidelines.
    """
    # Optional, set backtest parameters: e.g., moving average period
    params = (("maperiod", 15),)

    def log(self, txt, dt=None):
        """Optional, build a function to print strategy logs: can be used to print order or trade records, etc."""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def __init__(self):
        """Required, initialize attributes, calculate indicators, etc."""
        super().__init__()
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a Simple Moving Average indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

        # Example indicators for plotting (only supported arguments)
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25)
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0])

    def notify_order(self, order):
        """Optional, print order information"""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}"
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    f"SELL EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}"
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        """Optional, print trade information"""
        if not trade.isclosed:
            return

        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")

    def next(self):
        """Required, write trading strategy logic"""
        # Simply log the closing price of the series from the reference
        self.log(f"Close, {self.dataclose[0]:.2f}")

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log(f"BUY CREATE, {self.dataclose[0]:.2f}")

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log(f"SELL CREATE, {self.dataclose[0]:.2f}")

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


# Instantiate cerebro
cerebro = bt.Cerebro()
# Read data via feeds
# daily_price = pd.read_csv("daily_price.csv", parse_dates=['datetime'])
# # Pass data to the 'brain'
# # Loop through each stock code and pass data
# for stock in daily_price['sec_code'].unique():
#     # Date alignment
#     data = pd.DataFrame(index=daily_price.index.unique()) # Get all trading days in the backtest period
#     df = daily_price.query(f"sec_code=='{stock}'")[['open','high','low','close','volume','openinterest']]
#     data_ = pd.merge(data, df, left_index=True, right_index=True, how='left')
#     # Handle missing values: date alignment may cause some trading days to have missing data, so missing data needs to be filled
#     # For missing trading day market data, fill missing data. For example, fill missing volume with 0 to indicate the stock cannot be traded; forward fill missing open/high/low/close; fill missing open/high/low/close before listing with 0, etc.
#     data_.loc[:,['volume','openinterest']] = data_.loc[:,['volume','openinterest']].fillna(0)
#     data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(method='pad')
#     data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(0)
#     # Import data
#     datafeed = btfeeds.PandasData(dataname=data_, fromdate=datetime.datetime(2019,1,2), todate=datetime.datetime(2021,1,28))
#     cerebro.adddata(datafeed, name=stock) # Pass data set and stock one-to-one via name
#     print(f"{stock} Done !")
modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
datapath = os.path.join(modpath, "../../datas/stock/zh_a/000517.csv")

# Create a Data Feed
data = StockCsvData(
    dataname=datapath,
    # Do not pass values before this date
    fromdate=datetime.datetime(2003, 1, 1),
    # Do not pass values after this date
    todate=datetime.datetime(2003, 12, 31),
    reverse=False,
)

# Add the Data Feed to Cerebro
cerebro.adddata(data)

# Set initial capital via broker
cerebro.broker.setcash(1000000)
# Set the quantity per trade
cerebro.addsizer(bt.sizers.FixedSize, stake=10)
# Set trading commission
cerebro.broker.setcommission(commission=0.0003)
# Slippage: 0.0001 per side
cerebro.broker.set_slippage_perc(perc=0.0001)
# Add strategy
cerebro.addstrategy(TestStrategy, maperiod=20)
# Add strategy analyzers
# Return time series data of return rate
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="pnl")
cerebro.addanalyzer(
    bt.analyzers.AnnualReturn, _name="_AnnualReturn"
)  # Annual return rate
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="_SharpeRatio")  # Sharpe ratio
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="_DrawDown")  # Drawdown
# Add observers
# cerebro.addobserver(...)
# Start backtest
cerebro.run()
# Visualize backtest results
b = Bokeh(style="bar", scheme=Tradimo())
cerebro.plot(b)
