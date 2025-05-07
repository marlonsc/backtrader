import datetime
import os
import sys

import backtrader as bt  # Import Backtrader
from backtest.feeds.datafeeds import StockCsvData

# from backtrader_plotting import Bokeh  # Commented out: not installed
# from backtrader_plotting.schemes import Tradimo  # Commented out: not
# installed


# Create strategy
class TestStrategy(bt.Strategy):
    """Example Backtrader strategy for demonstration and testing purposes."""

    params = (("maperiod", 15),)

    def log(self, txt, dt=None):
        """Print strategy logs (order/trade records, etc.).

Args:
    txt: Log message.
    dt: Date for the log. Defaults to None."""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def __init__(self):
        """Initialize attributes and calculate indicators."""
        super().__init__()
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Add a Simple Moving Average indicator
        self.sma = bt.indicators.SMA(self.datas[0], period=self.params.maperiod)
        # Only supported indicators (others removed for linter compliance)
        bt.indicators.RSI(self.datas[0])
        bt.indicators.ATR(self.datas[0])

    def notify_order(self, order):
        """Print order information.

Args:
    order: Order object."""
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(
                    f"SELL EXECUTED, Price: {order.executed.price:.2f}, "
                    f"Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}"
                )
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
        self.order = None

    def notify_trade(self, trade):
        """Print trade information.

Args:
    trade: Trade object."""
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")

    def next(self):
        """Trading strategy logic for each new bar."""
        self.log(f"Close, {self.dataclose[0]:.2f}")
        if self.order:
            return
        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log(f"BUY CREATE, {self.dataclose[0]:.2f}")
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.sma[0]:
                self.log(f"SELL CREATE, {self.dataclose[0]:.2f}")
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
# Visualization requires backtrader_plotting, which is not installed
# b = Bokeh(style="bar", scheme=Tradimo())
# cerebro.plot(b)
