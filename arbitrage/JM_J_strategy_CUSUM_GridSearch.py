import argparse
import datetime

import backtrader as bt
import numpy as np
import pandas as pd


def calculate_rolling_spread(
    df0: pd.DataFrame,  # 必含 'date' 与价格列
    df1: pd.DataFrame,
    window: int = 30,
    fields=("open", "high", "low", "close"),
) -> pd.DataFrame:
    """
    Calculate rolling β, and generate spread (spread_x = price0_x - β_{t-1} * price1_x) for specified price fields:
    """
    # 1) Align using close prices (β estimated using close)
    df = (
        df0.set_index("date")[["close"]]
        .rename(columns={"close": "close0"})
        .join(
            df1.set_index("date")[["close"]].rename(columns={"close": "close1"}),
            how="inner",
        )
    )

    # 2) Estimate β_t, and shift one day forward
    beta_raw = (
        df["close0"].rolling(window).cov(df["close1"])
        / df["close1"].rolling(window).var()
    )
    # Prevent future + keep 1 decimal place
    beta_shift = beta_raw.shift(1).round(1)

    # 3) Append β to main table (for later vectorized calculation)
    df = df.assign(beta=beta_shift)

    # 4) Calculate spread for each field
    out_cols = {"date": df.index, "beta": beta_shift}
    for f in fields:
        if f not in ("open", "high", "low", "close"):
            raise ValueError(f"Unknown field {f}")
        p0 = df0.set_index("date")[f]
        p1 = df1.set_index("date")[f]
        aligned = p0.to_frame(name=f"price0_{f}").join(
            p1.to_frame(name=f"price1_{f}"), how="inner"
        )
        spread_f = aligned[f"price0_{f}"] - beta_shift * aligned[f"price1_{f}"]
        out_cols[f"{f}"] = spread_f

    # 5) Clean up output
    out = pd.DataFrame(out_cols).dropna().reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"])
    return out


# Create custom data class to support beta column


class SpreadData(bt.feeds.PandasData):
    lines = ("beta",)  # Add beta line

    params = (
        ("datetime", "date"),  # Date column
        ("close", "close"),  # Spread as close
        ("beta", "beta"),  # beta column
        ("nocase", True),  # Column names are case insensitive
    )


class DynamicSpreadCUSUMStrategy(bt.Strategy):
    params = (
        ("win", 20),  # Rolling window
        ("k_coeff", 0.5),  # κ = k_coeff * σ
        ("h_coeff", 5.0),  # h = h_coeff * σ
        ("base_holding_days", 3),  # Base holding days
        ("days_factor", 2.0),  # Days factor for dynamic adjustment
        ("verbose", False),  # Whether to print detailed information
    )

    def __init__(self):
        # Save two cumulative sums
        self.g_pos, self.g_neg = 0.0, 0.0  # CUSUM state
        # Convenient access to recent win spread series
        self.spread_series = self.data2.close

        ########### New: Initialize array to store rolling means ###########
        self.rolling_mu = bt.ind.SMA(
            self.data2.close, period=self.p.win
        )  # Rolling mean

        # New: Holding days counter
        self.holding_counter = 0
        self.target_holding_days = (
            0  # Target holding days, will be dynamically calculated
        )
        self.in_position = False

        # Statistics
        self.total_trades = 0
        self.total_holding_days = 0
        self.holding_days_list = []  # Record holding days for each trade
        self.trade_start_date = None

    # ---------- Transaction helper (keep original logic) ----------
    def _open_position(self, short, signal_strength):
        if not hasattr(self, "size0"):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:  # Short spread
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:  # Long spread
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)

        # Dynamic calculation of target holding days based on signal strength
        # Stronger signal, longer holding days
        dynamic_days = int(self.p.days_factor * signal_strength)
        self.target_holding_days = max(
            self.p.base_holding_days, self.p.base_holding_days + dynamic_days
        )

        if self.p.verbose:
            print(
                f"Signal strength: {signal_strength:.2f}, Target holding days:"
                f" {self.target_holding_days}"
            )

        # Reset holding counter
        self.holding_counter = 0
        self.in_position = True
        self.total_trades += 1
        self.trade_start_date = self.datetime.date()

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)
        self.in_position = False

        # Update statistics
        self.total_holding_days += self.holding_counter
        self.holding_days_list.append(self.holding_counter)

        if self.p.verbose:
            print(
                f"Trade holding days: {self.holding_counter} days, "
                f"from {self.trade_start_date} to {self.datetime.date()}"
            )

    def next(self):
        # ---------- Main loop ----------
        ########### Modified: Calculate dynamic mean μ ###########
        # Take previous win spread series (excluding current day)
        hist = self.spread_series.get(size=self.p.win, ago=0)
        mu = np.mean(hist)
        sigma = np.std(hist, ddof=1)

        if np.isnan(sigma) or sigma == 0:
            return

        kappa = self.p.k_coeff * sigma
        h = self.p.h_coeff * sigma

        s_t = self.spread_series[0]

        ########### Key modification: Use corrected spread ###########
        s_t_corrected = s_t - mu  # Corrected spread

        # 3) Update positive/negative cumulative sums (using corrected spread)
        self.g_pos = max(0, self.g_pos + s_t_corrected - kappa)
        self.g_neg = max(0, self.g_neg - s_t_corrected - kappa)

        position_size = self.getposition(self.data0).size

        # 4) Open position logic (keep unchanged)
        if position_size == 0:
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            if self.g_pos > h:
                # Calculate signal strength: Magnitude of cumulative sum exceeding threshold h
                signal_strength = (self.g_pos - h) / h
                self._open_position(short=True, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0
            elif self.g_neg > h:
                # Calculate signal strength: Magnitude of cumulative sum exceeding threshold h
                signal_strength = (self.g_neg - h) / h
                self._open_position(short=False, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0
        else:
            # Existing position: Increase holding days counter
            if self.in_position:
                self.holding_counter += 1

                # Close position when target holding days are reached
                if self.holding_counter >= self.target_holding_days:
                    if self.p.verbose:
                        print(
                            f"Reached target days {self.target_holding_days} days,"
                            " closing"
                        )
                    self._close_positions()

    def notify_trade(self, trade):
        if not self.p.verbose:
            return

        if trade.isclosed:
            print(
                "TRADE %s CLOSED %s, PROFIT: GROSS %.2f, NET %.2f, PRICE %d"
                % (
                    trade.ref,
                    bt.num2date(trade.dtclose),
                    trade.pnl,
                    trade.pnlcomm,
                    trade.value,
                )
            )
        elif trade.justopened:
            print(
                "TRADE %s OPENED %s  , SIZE %2d, PRICE %d "
                % (trade.ref, bt.num2date(trade.dtopen), trade.size, trade.value)
            )

    def get_stats(self):
        """Return strategy statistics"""
        stats = {
            "total_trades": self.total_trades,
            "total_holding_days": self.total_holding_days,
            "avg_holding_days": self.total_holding_days / max(1, self.total_trades),
            "holding_days_list": self.holding_days_list,
            "max_holding_days": (
                max(self.holding_days_list) if self.holding_days_list else 0
            ),
            "min_holding_days": (
                min(self.holding_days_list) if self.holding_days_list else 0
            ),
        }
        return stats


def run_strategy(
    data0,
    data1,
    data2,
    win,
    k_coeff,
    h_coeff,
    base_holding_days,
    days_factor,
    spread_window=60,
    initial_cash=100000,
):
    """Run single backtest"""
    # Create backtest engine
    cerebro = bt.Cerebro()
    cerebro.adddata(data0, name="data0")
    cerebro.adddata(data1, name="data1")
    cerebro.adddata(data2, name="spread")

    # Add strategy
    cerebro.addstrategy(
        DynamicSpreadCUSUMStrategy,
        win=win,
        k_coeff=k_coeff,
        h_coeff=h_coeff,
        base_holding_days=base_holding_days,  # Base holding days
        days_factor=days_factor,  # Days adjustment factor
        verbose=False,
    )

    # Set initial cash
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.set_shortcash(False)

    # Add analyzers
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        timeframe=bt.TimeFrame.Days,
        riskfreerate=0,
        annualize=True,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    # Run backtest
    results = cerebro.run()

    # Get analysis results
    strat = results[0]
    sharpe = strat.analyzers.sharperatio.get_analysis().get("sharperatio", 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)
    returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0)
    trades = strat.analyzers.tradeanalyzer.get_analysis()

    # Get trade statistics
    total_trades = trades.get("total", {}).get("total", 0)
    win_trades = trades.get("won", {}).get("total", 0)
    loss_trades = trades.get("lost", {}).get("total", 0)
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

    # Get strategy custom statistics
    strategy_stats = strat.get_stats()

    return {
        "sharpe": sharpe,
        "drawdown": drawdown,
        "returns": returns,
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate": win_rate,
        "avg_holding_days": strategy_stats["avg_holding_days"],
        "max_holding_days": strategy_stats["max_holding_days"],
        "min_holding_days": strategy_stats["min_holding_days"],
        "params": {
            "win": win,
            "k_coeff": k_coeff,
            "h_coeff": h_coeff,
            "base_holding_days": base_holding_days,
            "days_factor": days_factor,
            "spread_window": spread_window,
        },
    }


def grid_search(
    pair1=None,
    pair2=None,
    initial_cash=100000,
    win_values=None,
    k_coeff_values=None,
    h_coeff_values=None,
    base_holding_days_values=None,
    days_factor_values=None,
    spread_windows=None,
):
    """Execute grid search to find optimal parameters"""
    # Read data
    output_file = "/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5"

    # Use default for '/J' and '/JM' if not specified
    pair1 = pair1 or "/J"
    pair2 = pair2 or "/JM"

    df0 = pd.read_hdf(output_file, key=pair1).reset_index()
    df1 = pd.read_hdf(output_file, key=pair2).reset_index()

    # Ensure date column format is correct
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])

    fromdate = datetime.datetime(2017, 1, 1)
    todate = datetime.datetime(2025, 1, 1)

    # Use default parameter grid (if not specified)
    if win_values is None:
        win_values = [7, 14]

    if k_coeff_values is None:
        k_coeff_values = [0.2, 0.5, 0.8, 1.0]

    if h_coeff_values is None:
        h_coeff_values = [4.0, 8.0, 12.0]

    if base_holding_days_values is None:
        base_holding_days_values = [3, 5]

    if days_factor_values is None:
        days_factor_values = [1, 3, 5, 7]

    if spread_windows is None:
        spread_windows = [15, 30]

    # Generate parameter combinations
    param_combinations = []
    for spread_window in spread_windows:
        # Calculate rolling spread for current window
        print(f"Calculating rolling spread (window={spread_window})...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)

        # Add data
        df0_bt = df0[(df0["date"] >= fromdate) & (df0["date"] <= todate)]
        df1_bt = df1[(df1["date"] >= fromdate) & (df1["date"] <= todate)]
        df_spread_bt = df_spread[
            (df_spread["date"] >= fromdate) & (df_spread["date"] <= todate)
        ]
        data0 = bt.feeds.PandasData(dataname=df0_bt, datetime="date")
        data1 = bt.feeds.PandasData(dataname=df1_bt, datetime="date")
        data2 = SpreadData(dataname=df_spread_bt, datetime="date")

        for win in win_values:
            for k_coeff in k_coeff_values:
                for h_coeff in h_coeff_values:
                    for base_holding_days in base_holding_days_values:
                        for days_factor in days_factor_values:
                            param_combinations.append((
                                data0,
                                data1,
                                data2,
                                win,
                                k_coeff,
                                h_coeff,
                                base_holding_days,
                                days_factor,
                                spread_window,
                            ))

    # Execute grid search
    results = []
    total_combinations = len(param_combinations)

    print(f"Starting grid search, {total_combinations} parameter combinations...")

    for i, (
        data0,
        data1,
        data2,
        win,
        k_coeff,
        h_coeff,
        base_holding_days,
        days_factor,
        spread_window,
    ) in enumerate(param_combinations):
        print(
            f"Testing parameter combination {i + 1}/{total_combinations}: win={win},"
            f" k_coeff={k_coeff:.1f}, h_coeff={h_coeff:.1f},"
            f" base_days={base_holding_days}, factor={days_factor:.1f},"
            f" spread_window={spread_window}"
        )

        # try:
        result = run_strategy(
            data0,
            data1,
            data2,
            win,
            k_coeff,
            h_coeff,
            base_holding_days,
            days_factor,
            spread_window,
            initial_cash,
        )
        results.append(result)

        # Print current result
        print(
            f"   Sharpe ratio: {result['sharpe']:.4f}, Maximum drawdown:"
            f" {result['drawdown']:.2f}%, Annualized return: {result['returns']:.2f}%,"
            f" Win rate: {result['win_rate']:.2f}%"
        )
        print(
            f"   Number of trades: {result['total_trades']}, Average holding days:"
            f" {result['avg_holding_days']:.2f} days (Shortest:"
            f" {result['min_holding_days']} days, Longest:"
            f" {result['max_holding_days']} days)"
        )

        # except Exception as e:
        #     print(f"   Parameter combination error: {e}")

    # Find best parameter combination
    if results:
        # Sort by Sharpe ratio
        sorted_results = sorted(
            results,
            key=lambda x: x["sharpe"] if x["sharpe"] is not None else -float("inf"),
            reverse=True,
        )
        best_result = sorted_results[0]

        print("\n========= Best parameter combination =========")
        print(f"Pairs: {pair1}/{pair2}")
        print(f"Spread calculation window: {best_result['params']['spread_window']}")
        print(f"Rolling window (win): {best_result['params']['win']}")
        print(f"κ coefficient (k_coeff): {best_result['params']['k_coeff']:.2f}")
        print(f"h coefficient (h_coeff): {best_result['params']['h_coeff']:.2f}")
        print(f"Base holding days: {best_result['params']['base_holding_days']}")
        print(f"Days adjustment factor: {best_result['params']['days_factor']:.2f}")
        print(f"Sharpe ratio: {best_result['sharpe']:.4f}")
        print(f"Maximum drawdown: {best_result['drawdown']:.2f}%")
        print(f"Annualized return: {best_result['returns']:.2f}%")
        print(f"Total trades: {best_result['total_trades']}")
        print(f"Win rate: {best_result['win_rate']:.2f}%")
        print(f"Average holding days: {best_result['avg_holding_days']:.2f} days")
        print(
            f"Holding days range: {best_result['min_holding_days']} to"
            f" {best_result['max_holding_days']} days"
        )

        # Display all results, sorted by Sharpe ratio
        print(
            "\n========= All parameter combinations results (sorted by Sharpe"
            " ratio)========="
        )
        for i, result in enumerate(sorted_results[:10]):  # Display top 10 best results
            print(
                f"{i + 1}. spread_window={result['params']['spread_window']}, "
                f"win={result['params']['win']}, "
                f"k_coeff={result['params']['k_coeff']:.2f}, "
                f"h_coeff={result['params']['h_coeff']:.2f}, "
                f"base_days={result['params']['base_holding_days']}, "
                f"factor={result['params']['days_factor']:.2f}, "
                f"sharpe={result['sharpe']:.4f}, "
                f"drawdown={result['drawdown']:.2f}%, "
                f"return={result['returns']:.2f}%, "
                f"win_rate={result['win_rate']:.2f}%, "
                f"trades={result['total_trades']}, "
                f"avg_days={result['avg_holding_days']:.1f}"
            )
    else:
        print("No valid parameter combinations found")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Dynamic CUSUM strategy parameter grid search"
    )

    # Pair arguments
    parser.add_argument(
        "--pair1", type=str, default="/J", help="First contract code (default: /J)"
    )
    parser.add_argument(
        "--pair2", type=str, default="/JM", help="Second contract code (default: /JM)"
    )

    # Initial cash
    parser.add_argument(
        "--cash", type=int, default=100000, help="Initial cash (default: 100000)"
    )

    # Strategy parameters
    parser.add_argument(
        "--win",
        nargs="+",
        type=int,
        default=[7, 14],
        help="Rolling window value list (default: 7 14)",
    )
    parser.add_argument(
        "--k-coeff",
        nargs="+",
        type=float,
        default=[0.2, 0.5, 0.8, 1.0],
        help="κ coefficient value list (default: 0.2 0.5 0.8 1.0)",
    )
    parser.add_argument(
        "--h-coeff",
        nargs="+",
        type=float,
        default=[4, 8.0, 12.0],
        help="h coefficient value list (default: 4 8.0 12.0)",
    )
    parser.add_argument(
        "--base-days",
        nargs="+",
        type=int,
        default=[1],
        help="Base holding days list (default: 1)",
    )
    parser.add_argument(
        "--days-factor",
        nargs="+",
        type=float,
        default=[1, 3, 5, 7],
        help="Days adjustment factor list (default: 1 3 5 7)",
    )
    parser.add_argument(
        "--spread-windows",
        nargs="+",
        type=int,
        default=[15, 30],
        help="Spread calculation window list (default: 15 30)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    grid_search(
        pair1=args.pair1,
        pair2=args.pair2,
        initial_cash=args.cash,
        win_values=args.win,
        k_coeff_values=args.k_coeff,
        h_coeff_values=args.h_coeff,
        base_holding_days_values=args.base_days,
        days_factor_values=args.days_factor,
        spread_windows=args.spread_windows,
    )


# ========= Best parameter combination =========
# Spread calculation window: 15
# Rolling window (win): 14
# κ coefficient (k_coeff): 0.50
# h coefficient (h_coeff): 4.00
# Base holding days: 5
# Days adjustment factor: 5.00
# Sharpe ratio: 0.5480
# Maximum drawdown: 9.04%
# Annualized return: 2.53%
# Total trades: 340
# Win rate: 49.71%
# Average holding days: 6.13 days
# Holding days range: 5 to 25 days

# ========= All parameter combinations results (sorted by Sharpe ratio)=========
# 1. spread_window=15, win=14, k_coeff=0.50, h_coeff=4.00, base_days=5, factor=5.00, sharpe=0.5480, drawdown=9.04%, return=2.53%, win_rate=49.71%, trades=340, avg_days=6.1
# 2. spread_window=30, win=7, k_coeff=0.80, h_coeff=8.00, base_days=5, factor=3.00, sharpe=0.4927, drawdown=5.67%, return=1.83%, win_rate=51.37%, trades=146, avg_days=5.7
# 3. spread_window=15, win=7, k_coeff=0.50, h_coeff=8.00, base_days=5, factor=1.00, sharpe=0.4886, drawdown=6.48%, return=1.90%, win_rate=51.01%, trades=198, avg_days=5.2
# 4. spread_window=15, win=7, k_coeff=1.00, h_coeff=8.00, base_days=3, factor=1.00, sharpe=0.4716, drawdown=0.65%, return=0.29%, win_rate=57.14%, trades=28, avg_days=3.0
# 5. spread_window=30, win=14, k_coeff=0.80, h_coeff=4.00, base_days=3, factor=3.00, sharpe=0.4713, drawdown=6.41%, return=1.50%, win_rate=52.58%, trades=310, avg_days=3.1
# 6. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=3.00, sharpe=0.4692, drawdown=5.93%, return=1.80%, win_rate=49.46%, trades=186, avg_days=6.0
# 7. spread_window=30, win=14, k_coeff=0.80, h_coeff=4.00, base_days=3, factor=1.00, sharpe=0.4631, drawdown=7.47%, return=1.49%, win_rate=51.27%, trades=314, avg_days=3.0
# 8. spread_window=30, win=14, k_coeff=0.20, h_coeff=4.00, base_days=5, factor=5.00, sharpe=0.4602, drawdown=10.94%, return=2.59%, win_rate=45.45%, trades=198, avg_days=17.1
# 9. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=1.00, sharpe=0.4600, drawdown=5.11%, return=1.73%, win_rate=49.46%, trades=186, avg_days=5.2
# 10. spread_window=30, win=7, k_coeff=0.50, h_coeff=12.00, base_days=5, factor=5.00, sharpe=0.4518, drawdown=7.10%, return=1.82%, win_rate=47.80%, trades=182, avg_days=7.0
