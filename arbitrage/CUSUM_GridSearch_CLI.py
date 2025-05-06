# Copyright (c) 2025 backtrader contributors
"""
CUSUM grid search CLI for dynamic spread trading using Backtrader. This module
performs parameter optimization for a pair trading strategy with CUSUM logic and
built-in analyzers.
"""

import argparse
import datetime

import backtrader as bt
import numpy as np
import pandas as pd
from backtrader.feeds import PandasData
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.roi import ROIAnalyzer
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer


def calculate_rolling_spread(
    df0: pd.DataFrame,  # Must contain 'date' and price columns
    df1: pd.DataFrame,
    window: int = 30,
    fields=("open", "high", "low", "close"),
) -> pd.DataFrame:
    """Calculate rolling β and generate spread for specified price fields:
spread_x = price0_x - β_{t-1} * price1_x"""
    # 1) Align and merge using close price (β is still estimated with close)
    df = (
        df0.set_index("date")[["close"]]
        .rename(columns={"close": "close0"})
        .join(
            df1.set_index("date")[["close"]].rename(columns={"close": "close1"}),
            how="inner",
        )
    )

    # 2) Estimate β_t, then shift one day forward
    beta_raw = (
        df["close0"].rolling(window).cov(df["close1"])
        / df["close1"].rolling(window).var()
    )
    beta_shift = beta_raw.shift(1).round(1)  # Prevent lookahead + keep 1 decimal

    # 3) Merge β back to main table (for vectorized calculation)
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

    # 5) Organize output
    out = pd.DataFrame(out_cols).dropna().reset_index(drop=True)
    out["date"] = pd.to_datetime(out["date"])
    return out


# Custom data class to support beta column
class SpreadData(PandasData):
    lines = ("beta",)  # Add beta line

    params = (
        ("datetime", "date"),  # Date column
        ("close", "close"),  # Spread column as close
        ("beta", "beta"),  # Beta column
        ("nocase", True),  # Column names are case-insensitive
    )


class DynamicSpreadCUSUMStrategy(bt.Strategy):
    params = (
        ("win", 20),  # rolling window
        ("k_coeff", 0.5),  # κ = k_coeff * σ
        ("h_coeff", 5.0),  # h = h_coeff * σ
        ("verbose", False),  # Whether to print detailed info
    )

    def __init__(self):
        # Store two cumulative sums
        self.g_pos, self.g_neg = 0.0, 0.0  # CUSUM state
        # For easy access to the last win spreads
        self.spread_series = self.data2.close

    # ---------- Trading helpers (same logic as before) ----------
    def _open_position(self, short):
        if not hasattr(self, "size0"):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:  # Short the spread
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:  # Long the spread
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)

    def _close_positions(self):
        self.close(data=self.data0)
        self.close(data=self.data1)

    # ---------- Main loop ----------
    def next(self):
        # 1) Ensure enough history for σ estimation
        if len(self.spread_series) < self.p.win + 2:
            return

        # 2) Use rolling σ at the end of the previous bar to avoid lookahead
        hist = self.spread_series.get(size=self.p.win + 1)[:-1]  # Exclude current
        sigma = np.std(hist, ddof=1)
        if np.isnan(sigma) or sigma == 0:
            return

        kappa = self.p.k_coeff * sigma
        h = self.p.h_coeff * sigma
        s_t = self.spread_series[0]

        # 3) Update positive/negative cumulative sums
        self.g_pos = max(0, self.g_pos + s_t - kappa)
        self.g_neg = max(0, self.g_neg - s_t - kappa)

        position_size = self.getposition(self.data0).size

        # 4) Open position logic—when g exceeds h
        if position_size == 0:
            # Calculate dynamic ratio (same as before)
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            if self.g_pos > h:  # Spread keeps rising → short the spread
                self._open_position(short=True)
                self.g_pos = self.g_neg = 0  # Reset cumulative sums
            elif self.g_neg > h:  # Spread keeps falling → long the spread
                self._open_position(short=False)
                self.g_pos = self.g_neg = 0
        else:
            # 5) Close position logic—spread returns near 0
            if position_size > 0 and abs(s_t) < kappa:
                self._close_positions()
            elif position_size < 0 and abs(s_t) < kappa:
                self._close_positions()

    def notify_trade(self, trade):
        if not self.p.verbose:
            return

        if trade.isclosed:
            print(
                f"TRADE {trade.ref} CLOSED, PROFIT: GROSS {trade.pnl:.2f}, NET {
                    trade.pnlcomm:.2f
                }, PRICE {trade.value}"
            )
        elif trade.justopened:
            print(
                f"TRADE {trade.ref} OPENED {trade.dtopen}, SIZE {trade.size}, PRICE {
                    trade.value
                }"
            )


def run_strategy(
    data0,
    data1,
    data2,
    win,
    k_coeff,
    h_coeff,
    spread_window=60,
    initial_cash=100000,
):
    """Run a single backtest iteration."""
    cerebro = bt.Cerebro()
    cerebro.adddata(data0, name="data0")
    cerebro.adddata(data1, name="data1")
    cerebro.adddata(data2, name="spread")
    cerebro.addstrategy(
        DynamicSpreadCUSUMStrategy,
        win=win,
        k_coeff=k_coeff,
        h_coeff=h_coeff,
        verbose=False,
    )
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.set_shortcash(False)
    cerebro.addanalyzer(SharpeRatio, timeframe=bt.TimeFrame.Days, riskfreerate=0, annualize=True)
    cerebro.addanalyzer(DrawDown)
    cerebro.addanalyzer(Returns)
    cerebro.addanalyzer(ROIAnalyzer, period=bt.TimeFrame.Days)
    cerebro.addanalyzer(TradeAnalyzer)
    results = cerebro.run()

    # 获取分析结果
    strat = results[0]
    sharpe = strat.analyzers.sharperatio.get_analysis().get("sharperatio", 0)
    drawdown = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)
    returns = strat.analyzers.returns.get_analysis().get("rnorm100", 0)
    roi = strat.analyzers.tradeanalyzer.get_analysis().get("roi", 0)
    trades = strat.analyzers.tradeanalyzer.get_analysis()

    # 获取交易统计
    total_trades = trades.get("total", {}).get("total", 0)
    win_trades = trades.get("won", {}).get("total", 0)
    loss_trades = trades.get("lost", {}).get("total", 0)
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

    return {
        "sharpe": sharpe,
        "drawdown": drawdown,
        "returns": returns,
        "roi": roi,
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate": win_rate,
        "params": {
            "win": win,
            "k_coeff": k_coeff,
            "h_coeff": h_coeff,
            "spread_window": spread_window,
        },
    }


def grid_search(
    contract1,
    contract2,
    fromdate_str=None,
    todate_str=None,
    win_values=None,
    k_coeff_values=None,
    h_coeff_values=None,
    spread_windows=None,
    initial_cash=100000,
):
    """Perform grid search to find the best parameters."""
    data_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    # Read data
    print(f"Reading {contract1} and {contract2} from {data_file} ...")
    df0 = pd.read_hdf(data_file, key=contract1).reset_index()
    df1 = pd.read_hdf(data_file, key=contract2).reset_index()

    # Ensure date column format is correct
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])

    # Set backtest date range
    if fromdate_str:
        fromdate = datetime.datetime.strptime(fromdate_str, "%Y-%m-%d")
    else:
        fromdate = datetime.datetime(2018, 1, 1)

    if todate_str:
        todate = datetime.datetime.strptime(todate_str, "%Y-%m-%d")
    else:
        todate = datetime.datetime(2025, 1, 1)

    print(
        f"Backtest date range: {fromdate.strftime('%Y-%m-%d')} to"
        f" {todate.strftime('%Y-%m-%d')}"
    )

    # Use default or custom parameter values
    if win_values is None:
        win_values = [15, 20, 30]
    if k_coeff_values is None:
        k_coeff_values = [0.2, 0.4, 0.5, 0.6, 0.8]
    if h_coeff_values is None:
        h_coeff_values = [3.0, 5.0, 8.0, 10.0]
    if spread_windows is None:
        spread_windows = [20, 30, 60]

    print("Grid search parameters:")
    print(f"  Window size (win): {win_values}")
    print(f"  k coefficient (k_coeff): {k_coeff_values}")
    print(f"  h coefficient (h_coeff): {h_coeff_values}")
    print(f"  Spread window (spread_window): {spread_windows}")

    # Generate parameter combinations
    param_combinations = []
    for spread_window in spread_windows:
        # Calculate rolling spread for current window
        print(f"Calculating rolling spread (window={spread_window}) ...")
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)

        # Add data
        data0 = PandasData(dataname=df0)
        data1 = PandasData(dataname=df1)
        data2 = SpreadData(dataname=df_spread)

        for win in win_values:
            for k_coeff in k_coeff_values:
                for h_coeff in h_coeff_values:
                    param_combinations.append(
                        (
                            data0,
                            data1,
                            data2,
                            win,
                            k_coeff,
                            h_coeff,
                            spread_window,
                        )
                    )

    # Perform grid search
    results = []
    total_combinations = len(param_combinations)

    print(f"Starting grid search, total {total_combinations} parameter combinations ...")

    for i, (
        data0,
        data1,
        data2,
        win,
        k_coeff,
        h_coeff,
        spread_window,
    ) in enumerate(param_combinations):
        print(
            f"Testing parameter set {i + 1}/{total_combinations}: win={win},"
            f" k_coeff={k_coeff:.1f}, h_coeff={h_coeff:.1f},"
            f" spread_window={spread_window}"
        )

        try:
            result = run_strategy(
                data0,
                data1,
                data2,
                win,
                k_coeff,
                h_coeff,
                spread_window,
                initial_cash,
            )
            results.append(result)

            # Print current result
            print(
                f"  Sharpe Ratio: {result['sharpe']:.4f}, Max Drawdown:"
                f" {result['drawdown']:.2f}%, Annualized Return: {result['returns']:.2f}%, Win Rate:"
                f" {result['win_rate']:.2f}%"
            )
        except Exception as e:
            print(f"  Error in parameter set: {e}")

    # Find the best parameter set
    if results:
        # Sort by Sharpe Ratio
        sorted_results = sorted(
            results,
            key=lambda x: (x["sharpe"] if x["sharpe"] is not None else -float("inf")),
            reverse=True,
        )
        best_result = sorted_results[0]

        print("\n========= Best Parameter Set =========")
        print(f"Contract pair: {contract1} - {contract2}")
        print(f"Spread calculation window: {best_result['params']['spread_window']}")
        print(f"Rolling window (win): {best_result['params']['win']}")
        print(f"k coefficient (k_coeff): {best_result['params']['k_coeff']:.2f}")
        print(f"h coefficient (h_coeff): {best_result['params']['h_coeff']:.2f}")
        print(f"Sharpe Ratio: {best_result['sharpe']:.4f}")
        print(f"Max Drawdown: {best_result['drawdown']:.2f}%")
        print(f"Annualized Return: {best_result['returns']:.2f}%")
        print(f"Total ROI: {best_result['roi']:.2f}%")
        print(f"Total trades: {best_result['total_trades']}")
        print(f"Win rate: {best_result['win_rate']:.2f}%")

        # Show all results, sorted by Sharpe Ratio
        print("\n========= All Parameter Sets (Top 10 by Sharpe Ratio) =========")
        for i, result in enumerate(sorted_results[:10]):  # Show only top 10
            print(
                f"{i + 1}. spread_window={result['params']['spread_window']}, "
                f"win={result['params']['win']}, "
                f"k_coeff={result['params']['k_coeff']:.2f}, "
                f"h_coeff={result['params']['h_coeff']:.2f}, "
                f"sharpe={result['sharpe']:.4f}, "
                f"drawdown={result['drawdown']:.2f}%, "
                f"return={result['returns']:.2f}%, "
                f"win_rate={result['win_rate']:.2f}%"
            )

        # Return the best result
        return best_result
    else:
        print("No valid parameter set found.")
        return None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Futures contract pair CUSUM strategy parameter optimization tool")

    # Required arguments
    parser.add_argument(
        "--contract1", required=True, help="First futures contract code, e.g. /OI"
    )
    parser.add_argument(
        "--contract2", required=True, help="Second futures contract code, e.g. /Y"
    )

    # Optional arguments - date range
    parser.add_argument("--fromdate", help="Backtest start date, format: YYYY-MM-DD")
    parser.add_argument("--todate", help="Backtest end date, format: YYYY-MM-DD")

    # Optional arguments - grid search parameters
    parser.add_argument(
        "--win", type=int, nargs="+", help="List of rolling window sizes, e.g.: 15 20 30"
    )
    parser.add_argument(
        "--k-coeff", type=float, nargs="+", help="List of k coefficients, e.g.: 0.2 0.5 0.8"
    )
    parser.add_argument(
        "--h-coeff", type=float, nargs="+", help="List of h coefficients, e.g.: 3.0 5.0 8.0"
    )
    parser.add_argument(
        "--spread-window",
        type=int,
        nargs="+",
        help="List of spread calculation windows, e.g.: 20 30 60",
    )

    # Output directory
    parser.add_argument("--output-dir", help="Result output directory")

    # Initial cash
    parser.add_argument(
        "--cash",
        type=float,
        default=100000,
        help="Initial backtest cash amount, default: 100000",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 运行网格搜索
    grid_search(
        contract1=args.contract1,
        contract2=args.contract2,
        fromdate_str=args.fromdate,
        todate_str=args.todate,
        win_values=args.win,
        k_coeff_values=args.k_coeff,
        h_coeff_values=args.h_coeff,
        spread_windows=args.spread_window,
        initial_cash=args.cash,
    )
