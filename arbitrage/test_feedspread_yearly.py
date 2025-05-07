import warnings

import backtrader as bt
import numpy as np
import pandas as pd

# warnings.filterwarnings("ignore", category=UserWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

# 1. First confirm that the indexes of two DataFrames are the same


def check_and_align_data(df1, df2, date_column="date"):
    """Check and align data from two DataFrames

    :param df1:
    :param df2:
    :param date_column:  (Default value = "date")

    """
    # Ensure date column is used as index
    if date_column in df1.columns:
        df1 = df1.set_index(date_column)
    if date_column in df2.columns:
        df2 = df2.set_index(date_column)

    # Find common dates
    common_dates = df1.index.intersection(df2.index)

    # Check for missing dates
    missing_in_df1 = df2.index.difference(df1.index)
    missing_in_df2 = df1.index.difference(df2.index)

    if len(missing_in_df1) > 0:
        print(f"Number of missing dates in df_I: {len(missing_in_df1)}")
    if len(missing_in_df2) > 0:
        print(f"Number of missing dates in df_RB: {len(missing_in_df2)}")

    # Align data
    df1_aligned = df1.loc[common_dates]
    df2_aligned = df2.loc[common_dates]

    return df1_aligned, df2_aligned


# 2. Calculate spread


def calculate_spread(df_I, df_RB, columns=["open", "high", "low", "close", "volume"]):
    """Calculate spread between two DataFrames

    :param df_I:
    :param df_RB:
    :param columns:  (Default value = ["open","high","low","close","volume"])

    """
    # Align data
    df_I_aligned, df_RB_aligned = check_and_align_data(df_I, df_RB)

    # Create spread DataFrame
    df_spread = pd.DataFrame(index=df_I_aligned.index)

    # Subtract each column
    for col in columns:
        if col in df_I_aligned.columns and col in df_RB_aligned.columns:
            df_spread[f"{col}"] = 5 * df_I_aligned[col] - df_RB_aligned[col]

    return df_spread.reset_index()


# Bollinger Band strategy


class SpreadBollingerStrategy(bt.Strategy):
    """ """

    params = (
        ("period", 20),  # Bollinger Band period
        ("devfactor", 2),  # Bollinger Band standard deviation multiplier
        ("size_i", 5),  # Iron Ore trading size
        ("size_rb", 1),  # Rebar trading size
    )

    def __init__(self):
        """ """
        # Bollinger Band indicator
        self.boll = bt.indicators.BollingerBands(
            self.data2.close, period=self.p.period, devfactor=self.p.devfactor
        )

        # Trading status
        self.order = None

        # Record trade information
        self.trades = []
        self.current_trade = None

        # Record annual net values
        self.year_values = {}

    def next(self):
        """ """
        # Skip if there is an outstanding order
        if self.order:
            return

        # Get current spread
        spread = self.data2.close[0]
        upper = self.boll.lines.top[0]
        lower = self.boll.lines.bot[0]

        # Trading logic
        if not self.position:
            # Entry condition
            if spread > upper:
                # Short spread: Sell I and Buy RB
                self.sell(data=self.data0, size=self.p.size_i)  # Sell 5 I
                self.buy(data=self.data1, size=self.p.size_rb)  # Buy 1 RB
                self.current_trade = {
                    "entry_date": self.data.datetime.date(0),
                    "entry_price": spread,
                    "type": "short",
                }

            elif spread < lower:
                # Long spread: Buy I and Sell RB
                self.buy(data=self.data0, size=self.p.size_i)  # Buy 5 I
                self.sell(data=self.data1, size=self.p.size_rb)  # Sell 1 RB
                self.current_trade = {
                    "entry_date": self.data.datetime.date(0),
                    "entry_price": spread,
                    "type": "long",
                }

        else:
            # Exit condition
            if (spread <= self.boll.lines.mid[0] and self.position.size > 0) or (
                spread >= self.boll.lines.mid[0] and self.position.size < 0
            ):
                self.close(data=self.data0)
                self.close(data=self.data1)
                if self.current_trade:
                    self.current_trade["exit_date"] = self.data.datetime.date(0)
                    self.current_trade["exit_price"] = spread
                    self.current_trade["pnl"] = (
                        spread - self.current_trade["entry_price"]
                    ) * (-1 if self.current_trade["type"] == "short" else 1)
                    self.trades.append(self.current_trade)
                    self.current_trade = None

    def notify_order(self, order):
        """

        :param order:

        """
        # Order status notification
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None

    def stop(self):
        """ """
        # Calculate annual maximum drawdown and Sharpe ratio
        self.calculate_annual_metrics()

        # Output trade details
        self.print_trade_details()

        # Output annual metrics
        self.print_annual_metrics()

    def calculate_annual_metrics(self):
        """ """
        # Calculate net value by year
        for trade in self.trades:
            year = trade["entry_date"].year
            if year not in self.year_values:
                self.year_values[year] = []
            self.year_values[year].append(trade["pnl"])

        # Calculate annual maximum drawdown and Sharpe ratio
        self.annual_metrics = {}
        for year, pnls in self.year_values.items():
            cumulative_pnl = np.cumsum(pnls)
            max_drawdown = (
                np.maximum.accumulate(cumulative_pnl) - cumulative_pnl
            ).max()
            sharpe_ratio = np.mean(pnls) / np.std(pnls) if np.std(pnls) != 0 else 0
            self.annual_metrics[year] = {
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
            }

    def print_trade_details(self):
        """ """
        print("\nTrade Details:")
        print("=" * 80)
        print(
            "{:<12} {:<12} {:<12} {:<12} {:<12} {:<12}".format(
                "Type",
                "Entry Date",
                "Entry Price",
                "Exit Date",
                "Exit Price",
                "PnL",
            )
        )
        for trade in self.trades:
            print(
                "{:<12} {:<12} {:<12.2f} {:<12} {:<12.2f} {:<12.2f}".format(
                    trade["type"],  # Trade type
                    trade["entry_date"].strftime("%Y-%m-%d"),  # Entry date
                    trade["entry_price"],  # Entry price
                    trade["exit_date"].strftime("%Y-%m-%d"),  # Exit date
                    trade["exit_price"],  # Exit price
                    trade["pnl"],  # PnL
                )
            )

    def print_annual_metrics(self):
        """ """
        print("\nAnnual Metrics:")
        print("=" * 80)
        print("{:<8} {:<12} {:<12}".format("Year", "Maximum Drawdown", "Sharpe Ratio"))
        for year, metrics in self.annual_metrics.items():
            print(
                "{:<8} {:<12.2f} {:<12.2f}".format(
                    year, metrics["max_drawdown"], metrics["sharpe_ratio"]
                )
            )


# Example usage
# Read data
output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
df_I = pd.read_hdf(output_file, key="/I").reset_index()
df_RB = pd.read_hdf(output_file, key="/RB").reset_index()

# Calculate spread
df_spread = calculate_spread(df_I, df_RB)

# Display results
print("\nShape after data alignment:")
print(f"Spread data shape: {df_spread.shape}")
print("\nFirst few rows of data:")
print(df_spread.head())

# Check for missing values
print("\nMissing value statistics:")
print(df_spread.isnull().sum())

# Basic statistical information
print("\nBasic statistical information:")
print(df_spread.describe())

# Add data
data0 = bt.feeds.PandasData(dataname=df_I)
data1 = bt.feeds.PandasData(dataname=df_RB)
data2 = bt.feeds.PandasData(dataname=df_spread)

# Create backtesting engine
cerebro = bt.Cerebro()
cerebro.adddata(data0, name="I")
cerebro.adddata(data1, name="RB")
cerebro.adddata(data2, name="spread")

# Add strategy
cerebro.addstrategy(SpreadBollingerStrategy)

# Set initial cash
cerebro.broker.setcash(1000000.0)

# Run backtesting
cerebro.run(oldsync=True)

# Plot results
cerebro.plot(volume=False, spread=True)
# cerebro.plot(volume=False)
