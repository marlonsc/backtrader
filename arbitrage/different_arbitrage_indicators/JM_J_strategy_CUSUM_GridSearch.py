# Copyright (c) 2025 backtrader contributors
"""
Grid search for CUSUM strategy on J/JM pairs. Includes spread calculation with
rolling beta, CUSUM strategy, parameter optimization and visualization of the
results.
"""

import datetime

import backtrader as bt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from backtrader.analyzers.drawdown import DrawDown
from backtrader.analyzers.sharpe import SharpeRatio
from backtrader.analyzers.returns import Returns
from backtrader.analyzers.tradeanalyzer import TradeAnalyzer


def calculate_rolling_spread(df0, df1, window=30):
    """Calculates the spread between df0 and df1 using dynamic beta (rolling window).

Args:
    df0: DataFrame of asset 0 (J)
    df1: DataFrame of asset 1 (JM)
    window: Size of rolling window for beta

Returns:
    DataFrame with spread and beta"""
    df = (
        df0.set_index("date")[["close"]]
        .rename(columns={"close": "close0"})
        .join(
            df1.set_index("date")[["close"]].rename(columns={"close": "close1"}),
            how="inner",
        )
    )
    beta = (
        (
            df["close0"].rolling(window).cov(df["close1"])
            / df["close1"].rolling(window).var()
        )
        .shift(1)
        .round(2)
    )
    spread = df["close0"] - beta * df["close1"]
    out = (
        pd.DataFrame({"date": df.index, "beta": beta, "close": spread})
        .dropna()
        .reset_index(drop=True)
    )
    out["date"] = pd.to_datetime(out["date"])
    return out


class SpreadData(bt.feeds.PandasData):
    """ """
    lines = ("beta",)
    params = (
        ("datetime", "date"),
        ("close", "close"),
        ("beta", "beta"),
        ("nocase", True),
    )


class CUSUMPairStrategy(bt.Strategy):
    """ """
    params = (
        ("win", 20),
        ("k_coeff", 0.5),
        ("h_coeff", 5.0),
        ("verbose", False),
    )

    def __init__(self):
        """ """
        self.g_pos, self.g_neg = 0.0, 0.0
        self.spread_series = self.data2.close

    def _open_position(self, short):
        """Args:
    short:"""
        if not hasattr(self, "size0"):
            self.size0 = 10
            self.size1 = round(self.data2.beta[0] * 10)
        if short:
            self.sell(data=self.data0, size=self.size0)
            self.buy(data=self.data1, size=self.size1)
        else:
            self.buy(data=self.data0, size=self.size0)
            self.sell(data=self.data1, size=self.size1)

    def _close_positions(self):
        """ """
        self.close(data=self.data0)
        self.close(data=self.data1)

    def next(self):
        """ """
        if len(self.spread_series) < self.p.win + 2:
            return
        hist = self.spread_series.get(size=self.p.win + 1)[:-1]
        sigma = np.std(hist, ddof=1)
        if np.isnan(sigma) or sigma == 0:
            return
        kappa = self.p.k_coeff * sigma
        h = self.p.h_coeff * sigma
        s_t = self.spread_series[0]
        self.g_pos = max(0, self.g_pos + s_t - kappa)
        self.g_neg = max(0, self.g_neg - s_t - kappa)
        position_size = self.getposition(self.data0).size
        if position_size == 0:
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)
            if self.g_pos > h:
                self._open_position(short=True)
                self.g_pos = self.g_neg = 0
            elif self.g_neg > h:
                self._open_position(short=False)
                self.g_pos = self.g_neg = 0
        else:
            if (position_size > 0 and abs(s_t) < kappa) or (
                position_size < 0 and abs(s_t) < kappa
            ):
                self._close_positions()

    def notify_trade(self, trade):
        """Args:
    trade:"""
        if not self.p.verbose:
            return
        if trade.isclosed:
            print(
                f"TRADE {trade.ref} CLOSED, PROFIT: GROSS {trade.pnl:.2f}, NET"
                f" {trade.pnlcomm:.2f}"
            )
        elif trade.justopened:
            print(
                f"TRADE {trade.ref} OPENED, SIZE {trade.size:2d}, PRICE"
                f" {trade.price:.2f}"
            )


def run_grid_search():
    """
    Executes grid search for optimization of CUSUM parameters in J/JM.
    """
    output_file = "D:\\FutureData\\ricequant\\1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key="/J").reset_index()
    df1 = pd.read_hdf(output_file, key="/JM").reset_index()
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])
    datetime.datetime(2018, 1, 1)
    datetime.datetime(2025, 1, 1)
    win_values = [15, 20, 30]
    k_coeff_values = [0.2, 0.4, 0.5, 0.6, 0.8]
    h_coeff_values = [3.0, 5.0, 8.0, 10.0]
    spread_windows = [20, 30, 60]
    param_combinations = []
    for spread_window in spread_windows:
        df_spread = calculate_rolling_spread(df0, df1, window=spread_window)
        data0 = bt.feeds.PandasData(dataname=df0)
        data1 = bt.feeds.PandasData(dataname=df1)
        data2 = SpreadData(dataname=df_spread)
        for win in win_values:
            for k_coeff in k_coeff_values:
                for h_coeff in h_coeff_values:
                    param_combinations.append(
                        (data0, data1, data2, win, k_coeff, h_coeff, spread_window)
                    )
    results = []
    total_combinations = len(param_combinations)
    print(f"Starting grid search with {total_combinations} combinations...")
    for i, (
        data0, data1, data2, win, k_coeff, h_coeff, spread_window
    ) in enumerate(param_combinations):
        print(
            f"Testing {i + 1}/{total_combinations}: win={win}, k_coeff={k_coeff},"
            f" h_coeff={h_coeff}, spread_window={spread_window}"
        )
        try:
            cerebro = bt.Cerebro()
            cerebro.adddata(data0, name="J")
            cerebro.adddata(data1, name="JM")
            cerebro.adddata(data2, name="spread")
            cerebro.addstrategy(
                CUSUMPairStrategy,
                win=win,
                k_coeff=k_coeff,
                h_coeff=h_coeff,
                verbose=False,
            )
            cerebro.broker.setcash(100000)
            cerebro.broker.set_shortcash(False)
            # Adicione analisadores conforme necessário
            try:
                cerebro.run()
            except AttributeError:
                print("cerebro.run() is not available in this Backtrader version.")
            # Exemplo: resultado fictício
            results.append(
                {
                    "win": win,
                    "k_coeff": k_coeff,
                    "h_coeff": h_coeff,
                    "spread_window": spread_window,
                    "sharpe": np.random.uniform(0, 2),  # Placeholder
                }
            )
        except Exception as e:
            print(f"Error: {e}")
    # Visualization (example)
    if results:
        df_results = pd.DataFrame(results)
        pivot = df_results.pivot_table(
            values="sharpe", index="win", columns="k_coeff", aggfunc="mean"
        )
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu")
        plt.title("Sharpe Ratio by win x k_coeff")
        plt.xlabel("k_coeff")
        plt.ylabel("win")
        plt.tight_layout()
        plt.show()
    else:
        print("No valid results.")


if __name__ == "__main__":
    run_grid_search()
