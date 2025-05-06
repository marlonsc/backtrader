"""test_feedspread_yearly.py module.

Description of the module functionality."""


import backtrader as bt
import numpy as np
import pandas as pd

# warnings.filterwarnings("ignore", category=UserWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")

# 1. First confirm that the indexes of two DataFrames are the same


def check_and_align_data(df1, df2, date_column="date"):
"""Check and align data from two DataFrames

Args::
    df1: 
    df2: 
    date_column: (Default value = "date")"""
    date_column: (Default value = "date")"""
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

Args::
    df_I: 
    df_RB: 
    columns: (Default value = ["open","high","low","close","volume"])"""
    columns: (Default value = ["open","high","low","close","volume"])"""
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
""""""
""""""
""""""
"""Args::
    order:"""
""""""
""""""
""""""
""""""
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
try:
    cerebro.run(oldsync=True)
except AttributeError:
    print("cerebro.run() is not available in this Backtrader version.")

# Plot results
cerebro.plot(volume=False, spread=True)
# cerebro.plot(volume=False)
