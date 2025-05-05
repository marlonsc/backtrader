import backtrader as bt  # Import Backtrader
import backtrader.indicators as btind  # Import strategy indicator module
from backtest.feeds.datafeeds import StockCsvData


# Create strategy
class StrategyTemplate(bt.Strategy):
    # Optional, set backtest parameters: e.g., moving average period
    params = ((..., ...),)  # It is best not to delete the last comma!

    def log(self, txt, dt=None):
        """Optional, build a function to print strategy logs: can be used to print order or trade records, etc."""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        """Required, initialize attributes, calculate indicators, etc."""
        pass

    def start(self):
        """Called before backtest starts, corresponds to bar 0"""
        # Logic to be processed before the backtest starts can be written here
        # By default, calls an empty start() function to start the backtest
        pass

    def prenext(self):
        """Strategy preparation phase, corresponds to bar 1 to bar min_period-1"""
        # This function is mainly used to wait for indicator calculation; before indicators are ready, prenext() is called by default
        # min_period is the minimum period required to calculate the first value of all indicators in __init__
        pass

    def nextstart(self):
        """First time the strategy runs normally, corresponds to bar min_period"""
        # The strategy only starts running when all indicators in __init__ have values available
        # nextstart() runs only once, mainly to indicate that next() can start running
        # The default implementation of nextstart() simply calls next(), so the logic in next() starts from bar min_period
        pass

    def next(self):
        """Required, write trading strategy logic"""
        sma = btind.SimpleMovingAverage(...)  # Calculate moving average
        pass

    def notify_order(self, order):
        """Optional, print order information"""
        pass

    def notify_trade(self, trade):
        """Optional, print trade information"""
        pass

    def notify_cashvalue(self, cash, value):
        """Notify current cash and total asset value"""
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        """Return current cash, total asset value, fund value, and fund shares"""
        pass

    def notify_store(self, msg, *args, **kwargs):
        """Return notifications sent by the broker/store"""
        pass

    def notify_data(self, data, status, *args, **kwargs):
        """Return data-related notifications"""
        pass

    def notify_timer(self, timer, when, *args, **kwargs):
        """Return timer notifications"""
        # Timers can be added via add_time()
        pass


# Instantiate cerebro
cerebro = bt.Cerebro()
# Read data via feeds
data = StockCsvData(...)
# Pass data to the 'brain'
cerebro.adddata(data)
# Set initial capital via broker
cerebro.broker.setcash(...)
# Set the quantity per trade
cerebro.addsizer(...)
# Set trading commission, 0.0003 per side
cerebro.broker.setcommission(commission=0.0003)
# Set slippage, 0.0001 per side
cerebro.broker.set_slippage_perc(perc=0.0001)
# Order volume does not exceed 50% of daily volume
cerebro.broker.set_filler(bt.broker.fillers.FixedBarPerc(perc=50))
# Add strategy
cerebro.addstrategy(...)
# Optimize strategy
# cerebro.optstrategy(StrategyTemplate, maperiod=range(10, 31))
# Add strategy analyzers
cerebro.addanalyzer(...)
# Add observers
cerebro.addobserver(...)
# Start backtest
result = cerebro.run()
# Extract backtest results from result
# strat = result[0]
# Return daily return series
# daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
# Visualize backtest results
cerebro.plot()
