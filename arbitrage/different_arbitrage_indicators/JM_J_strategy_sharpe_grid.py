"""JM_J_strategy_sharpe_grid.py module.

Description of the module functionality."""


import backtrader as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Sharpe Difference Bollinger Band Strategy
class SharpeDiffStrategy(bt.Strategy):
    """Strategy based on the difference of Sharpe ratios between two assets with Bollinger Bands"""

    params = (
        ("return_period", 15),  # Period for calculating returns (15-day returns)
        ("ma_period", 10),  # Period for calculating moving average (20-day moving average)
        ("entry_std_multiplier", 0.3),  # Entry standard deviation multiplier
        ("max_hold_days", 15),  # Maximum holding days
        ("printlog", False),
    )

    def __init__(self):
        """Initialize the strategy variables"""
        # Store Sharpe ratio series for plotting
        self.sharpe_j_values = []
        self.sharpe_jm_values = []
        self.delta_sharpe_values = []
        self.dates = []

        # Bollinger Bands data
        self.delta_sharpe_ma = []  # Moving average
        self.delta_sharpe_std = []  # Standard deviation
        self.upper_band = []  # Upper band
        self.lower_band = []  # Lower band

        # Store J and JM return series
        self.returns_j = []
        self.returns_jm = []

        # Initialize trade-related variables
        self.order = None
        self.position_type = None
        self.entry_day = 0

        # Store historical price data
        self.j_prices = []
        self.jm_prices = []

    def next(self):
        """Main strategy logic executed on each bar"""
        if self.order:
            return

        # Add date to list
        self.dates.append(self.data0.datetime.date())

        # Save latest prices
        self.j_prices.append(self.data0.close[0])
        self.jm_prices.append(self.data1.close[0])

        # Skip when price data is insufficient
        if len(self.j_prices) < self.p.return_period + 1:
            return

        # Calculate 15-day returns
        j_ret_15d = (self.j_prices[-1] / self.j_prices[-self.p.return_period - 1]) - 1
        jm_ret_15d = (
            self.jm_prices[-1] / self.jm_prices[-self.p.return_period - 1]
        ) - 1

        # Save daily returns for volatility calculation
        if len(self) > 1:  # Ensure there's a previous price
            ret_j = (self.data0.close[0] / self.data0.close[-1]) - 1
            ret_jm = (self.data1.close[0] / self.data1.close[-1]) - 1
            self.returns_j.append(ret_j)
            self.returns_jm.append(ret_jm)
        else:
            return  # First bar has no previous day price, skip

        # Skip when return data is insufficient
        if len(self.returns_j) < self.p.return_period:
            return

        # Calculate 15-day volatility
        j_vol_15d = np.std(self.returns_j[-self.p.return_period:]) * np.sqrt(
            self.p.return_period
        )
        jm_vol_15d = np.std(self.returns_jm[-self.p.return_period :]) * np.sqrt(
            self.p.return_period
        )

        # Calculate Sharpe ratio
        sharpe_j = j_ret_15d / j_vol_15d if j_vol_15d > 0 else 0
        sharpe_jm = jm_ret_15d / jm_vol_15d if jm_vol_15d > 0 else 0

        # Store Sharpe ratios for plotting
        self.sharpe_j_values.append(sharpe_j)
        self.sharpe_jm_values.append(sharpe_jm)

        # Calculate Sharpe difference ΔSharpe = μJ/σJ - μJM/σJM
        delta_sharpe = sharpe_j - sharpe_jm
        self.delta_sharpe_values.append(delta_sharpe)

        # Calculate 20-day moving average and standard deviation
        if len(self.delta_sharpe_values) >= self.p.ma_period:
            # Calculate 20-day moving average MA(ΔSharpe) = MA20(ΔSharpe)
            ma_delta = np.mean(self.delta_sharpe_values[-self.p.ma_period:])
            self.delta_sharpe_ma.append(ma_delta)

            # Calculate 20-day standard deviation σΔSharpe = Std20(ΔSharpe)
            std_delta = np.std(self.delta_sharpe_values[-self.p.ma_period:])
            self.delta_sharpe_std.append(std_delta)

            # Calculate Bollinger Bands upper and lower bands
            # Upper Band = MAΔSharpe + 2 × σΔSharpe
            upper = ma_delta + self.p.entry_std_multiplier * std_delta
            self.upper_band.append(upper)

            # Lower Band = MAΔSharpe - 2 × σΔSharpe
            lower = ma_delta - self.p.entry_std_multiplier * std_delta
            self.lower_band.append(lower)
        else:
            # Skip when data is insufficient to calculate moving average and standard deviation
            return

        # Trading logic - based on Sharpe difference and Bollinger Bands relationship

        if self.position_type is not None:
            days_in_trade = len(self) - self.entry_day

            # Decide whether to close positions based on position direction and Sharpe difference
            if (
                self.position_type == "long_j_short_jm" and delta_sharpe >= ma_delta
            ) or days_in_trade >= self.p.max_hold_days:
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Close position: J-JM Sharpe diff={delta_sharpe:.4f},"
                        f" Days held={days_in_trade}, Mean={ma_delta:.4f}"
                    )

            elif (
                self.position_type == "short_j_long_jm" and delta_sharpe <= ma_delta
            ) or days_in_trade >= self.p.max_hold_days:
                self.close(data=self.data0)
                self.close(data=self.data1)
                self.position_type = None
                if self.p.printlog:
                    print(
                        f"Close position: J-JM Sharpe diff={delta_sharpe:.4f},"
                        f" Days held={days_in_trade}, Mean={ma_delta:.4f}"
                    )

        else:
            # Entry logic
            if delta_sharpe >= upper:
                # Sharpe difference breaks upper band, go long J, short JM
                self.order = self.buy(data=self.data0, size=10)
                self.order = self.sell(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = "long_j_short_jm"
                if self.p.printlog:
                    print(
                        f"Open position: Long J, Short JM, Sharpe diff={delta_sharpe:.4f},"
                        f" Upper band={upper:.4f}"
                    )

            elif delta_sharpe <= lower:
                # Sharpe difference breaks lower band, go short J, long JM
                self.order = self.sell(data=self.data0, size=10)
                self.order = self.buy(data=self.data1, size=14)
                self.entry_day = len(self)
                self.position_type = "short_j_long_jm"
                if self.p.printlog:
                    print(
                        f"Open position: Short J, Long JM, Sharpe diff={delta_sharpe:.4f},"
                        f" Lower band={lower:.4f}"
                    )

    def notify_order(self, order):
"""Called when order status changes

Args::
            order: The order that has changed status"""
        """
        if order.status in [order.Completed]:
            if self.p.printlog:
                if order.isbuy():
                    print(
                        f"Buy executed: Price={order.executed.price:.2f},"
                        f" Cost={order.executed.value:.2f},"
                        f" Commission={order.executed.comm:.2f}"
                    )
                else:
                    print(
                        f"Sell executed: Price={order.executed.price:.2f},"
                        f" Cost={order.executed.value:.2f},"
                        f" Commission={order.executed.comm:.2f}"
                    )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order canceled/rejected")

        self.order = None


# Data loading function, handling index issues
def load_data(symbol1, symbol2, fromdate, todate):
"""Load data for two symbols from HDF5 file

Args::
        symbol1: First symbol to load
        symbol2: Second symbol to load
        fromdate: Start date for data
        todate: End date for data

Returns::
        Tuple of two backtrader data feeds"""
    """
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"

    try:
        # Load data without preserving original index structure
        df0 = pd.read_hdf(output_file, key=symbol1).reset_index()
        df1 = pd.read_hdf(output_file, key=symbol2).reset_index()

        # Find date column (compatible with different naming)
        date_col = [col for col in df0.columns if "date" in col.lower()]
        if not date_col:
            raise ValueError("Date column not found in dataset")

        # Set date index
        df0 = df0.set_index(pd.to_datetime(df0[date_col[0]]))
        df1 = df1.set_index(pd.to_datetime(df1[date_col[0]]))
        df0 = df0.sort_index().loc[fromdate:todate]
        df1 = df1.sort_index().loc[fromdate:todate]

        # Create data feeds using 'dataname' for compatibility
        data0 = bt.feeds.PandasData()
        data0.dataname = df0
        data1 = bt.feeds.PandasData()
        data1.dataname = df1
        return data0, data1
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None


# Run grid search backtest and plot heatmap
def run_grid_search():
"""Run a grid search to optimize strategy parameters and visualize results

Returns::
        Tuple containing results array, ma_periods list, and entry_multipliers list"""
    """
    # Define parameter grid
    ma_periods = [5, 10, 15, 20, 25, 30, 35, 40]  # Moving average periods
    entry_multipliers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1.0, 1.5]  # Standard deviation multipliers

    # Store results
    results = np.zeros((len(ma_periods), len(entry_multipliers)))

    # Set initial dates
    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # Load data once (can be reused)
    data0, data1 = load_data("/J", "/JM", fromdate, todate)

    if data0 is None or data1 is None:
        print("Unable to load data, please check file path and data format")
        return

    print("Starting grid search...")
    print(
        f"Testing parameter combinations: {len(ma_periods)} x {len(entry_multipliers)} ="
        f" {len(ma_periods) * len(entry_multipliers)} combinations"
    )

    # Perform grid search
    for i, ma_period in enumerate(ma_periods):
        for j, entry_multiplier in enumerate(entry_multipliers):
            print(
                f"Testing parameters: ma_period={ma_period},"
                f" entry_std_multiplier={entry_multiplier}"
            )

            try:
                # Create a new cerebro instance
                cerebro = bt.Cerebro()

                # Add the same data
                cerebro.adddata(data0, name="J")
                cerebro.adddata(data1, name="JM")

                # Add strategy with current test parameters
                cerebro.addstrategy(
                    SharpeDiffStrategy,
                    ma_period=ma_period,
                    entry_std_multiplier=entry_multiplier,
                    printlog=False,
                )  # Turn off logging to reduce output

                # Set funds and commission
                cerebro.broker.setcash(100000)
                cerebro.broker.setcommission(commission=0.0003)
                cerebro.broker.set_shortcash(False)

                # Run backtest
                strats = cerebro.run()  # pylint: disable=no-member

                # Get Sharpe ratio - safely handle None values
                sharpe_analysis = strats[0].analyzers.sharperatio.get_analysis()
                sharpe = sharpe_analysis.get("sharperatio", 0) if sharpe_analysis else 0

                # Store results
                results[i, j] = sharpe

                print(f"Sharpe ratio: {sharpe:.2f}")
            except Exception as e:
                print(
                    f"Parameter combination ma_period={ma_period},"
                    f" entry_std_multiplier={entry_multiplier} execution error: {e}"
                )
                results[i, j] = -99  # Use a clearly negative value to mark error items

    # Plot heatmap
    plt.figure(figsize=(12, 8))

    # Use Seaborn's heatmap
    ax = sns.heatmap(
        results,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=entry_multipliers,
        yticklabels=ma_periods,
    )

    # Set title and labels
    plt.title("Sharpe Ratio Heatmap - ma_period vs entry_std_multiplier")
    plt.xlabel("entry_std_multiplier")
    plt.ylabel("ma_period")

    # Display figure
    plt.tight_layout()
    plt.savefig("sharpe_ratio_heatmap.png")
    plt.show()

    print("Heatmap saved as 'sharpe_ratio_heatmap.png'")

    # Clear invalid values (failed backtest results)
    results_clean = np.copy(results)
    results_clean[results_clean == -99] = np.nan

    # Find best parameter combination (excluding invalid values)
    if np.any(~np.isnan(results_clean)):
        # Ensure indices are int for list access
        max_i, max_j = np.unravel_index(
            int(np.nanargmax(results_clean)), results_clean.shape
        )
        best_ma_period = ma_periods[int(max_i)]
        best_entry_multiplier = entry_multipliers[int(max_j)]
        best_sharpe = results_clean[int(max_i), int(max_j)]

        print("\nBest parameter combination:")
        print(f"ma_period: {best_ma_period}")
        print(f"entry_std_multiplier: {best_entry_multiplier}")
        print(f"Sharpe ratio: {best_sharpe:.4f}")
    else:
        print("\nAll parameter combinations had errors, unable to determine best parameters")

    return results, ma_periods, entry_multipliers


# Modified main function to call grid search
if __name__ == "__main__":
    run_grid_search()
