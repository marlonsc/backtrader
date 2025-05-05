import argparse
import datetime

import backtrader as bt
import numpy as np
import pandas as pd

# https://mp.weixin.qq.com/s/na-5duJiRM1fTJF0WrcptA


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="CUSUM strategy parameters")

    # Required arguments
    parser.add_argument(
        "--window", type=int, default=15, help="Rolling spread window size"
    )
    parser.add_argument(
        "--df0_key", type=str, default="/J", help="Key for first dataset"
    )
    parser.add_argument(
        "--df1_key", type=str, default="/JM", help="Key for second dataset"
    )
    parser.add_argument(
        "--fromdate", type=str, default="2017-01-01", help="Backtest start date"
    )
    parser.add_argument(
        "--todate", type=str, default="2025-01-01", help="Backtest end date"
    )
    parser.add_argument(
        "--win", type=int, default=14, help="Rolling window in strategy"
    )
    parser.add_argument("--k_coeff", type=float, default=0.5, help="kappa coefficient")
    parser.add_argument("--h_coeff", type=float, default=4, help="h coefficient")
    parser.add_argument(
        "--base_holding_days", type=int, default=5, help="Base holding days"
    )
    parser.add_argument(
        "--days_factor",
        type=float,
        default=5.0,
        help="Holding days adjustment factor",
    )
    parser.add_argument("--setcash", type=float, default=100000, help="Initial cash")
    parser.add_argument(
        "--plot",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Plot results (True/False)",
    )
    parser.add_argument(
        "--setslippage", type=float, default=0.0, help="Set slippage rate"
    )
    parser.add_argument(
        "--export_csv",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Export backtest data to CSV (True/False)",
    )

    return parser.parse_args()


def calculate_rolling_spread(
    df0: pd.DataFrame,  # Must contain 'date' and price columns
    df1: pd.DataFrame,
    window: int = 30,
    fields=("open", "high", "low", "close"),
) -> pd.DataFrame:
    """
    Calculate rolling β and generate spread for specified price fields:
        spread_x = price0_x - β_{t-1} * price1_x
    """
    # 1) Align using close prices (β still estimated with close)
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
    # Prevent lookahead + keep 1 decimal
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

    # 5) Organize output
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
        ("win", 14),  # rolling window
        ("k_coeff", 0.5),  # κ = k_coeff * σ
        ("h_coeff", 4.0),  # h = h_coeff * σ
        ("base_holding_days", 5),  # base holding days
        ("days_factor", 5.0),  # holding days dynamic adjustment factor
    )

    def __init__(self):
        # Save two cumulative sums
        self.g_pos, self.g_neg = 0.0, 0.0  # CUSUM state
        # Convenient access to recent win spread series
        self.spread_series = self.data2.close

        # Save daily return data
        self.record_dates = []
        self.record_data = []
        self.prev_portfolio_value = self.broker.getvalue()

        # Add minimum cash tracking
        self.min_cash = self.broker.getcash()  # Initialize as current cash
        self.min_cash_date = None  # Record the date of minimum cash

        # Initialize array to store rolling means
        self.rolling_mu = bt.ind.SMA(
            self.data2.close, period=self.p.win
        )  # rolling mean

        # Holding days counter
        self.holding_counter = 0
        self.target_holding_days = 0  # target holding days, dynamically calculated
        self.in_position = False

        # Statistics variables
        self.total_trades = 0
        self.total_holding_days = 0
        self.holding_days_list = []  # record holding days for each trade
        self.trade_start_date = None

    # ---------- Trading helpers (original logic retained) ----------
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

        # Dynamically calculate target holding days based on signal strength
        # Stronger signal, longer holding days
        dynamic_days = int(self.p.days_factor * signal_strength)
        self.target_holding_days = max(
            self.p.base_holding_days, self.p.base_holding_days + dynamic_days
        )

        print(
            f"signal strength: {signal_strength:.2f}, target holding days:"
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

        print(
            f"holding days: {self.holding_counter} days, "
            f"from {self.trade_start_date} to {self.datetime.date()}"
        )

    # ---------- Main loop ----------
    def next(self):
        # Update minimum cash record
        current_cash = self.broker.getcash()
        if current_cash < self.min_cash:
            self.min_cash = current_cash
            self.min_cash_date = self.datetime.date()

        # Record daily return data
        current_value = self.broker.getvalue()
        daily_return = (
            (current_value / self.prev_portfolio_value) - 1.0
            if self.prev_portfolio_value > 0
            else 0
        )
        self.prev_portfolio_value = current_value

        self.record_dates.append(self.datetime.date())
        self.record_data.append(
            {
                "date": self.datetime.date(),
                "close": self.data2.close[0],
                "portfolio_value": current_value,
                "daily_return": daily_return,
                "position": self.getposition(self.data0).size,
                "beta": self.data2.beta[0],
                "g_pos": self.g_pos,
                "g_neg": self.g_neg,
                "holding_days": self.holding_counter,
                "target_days": (self.target_holding_days if self.in_position else 0),
                "cash": current_cash,  # Add cash record
            }
        )

        # Take previous win spread series (excluding current bar)
        hist = self.spread_series.get(size=self.p.win, ago=0)
        mu = np.mean(hist)
        sigma = np.std(hist, ddof=1)

        if np.isnan(sigma) or sigma == 0:
            return

        kappa = self.p.k_coeff * sigma
        h = self.p.h_coeff * sigma

        s_t = self.spread_series[0]

        # Use corrected spread
        s_t_corrected = s_t - mu  # Corrected spread

        # Update positive/negative cumulative sums (using corrected spread)
        self.g_pos = max(0, self.g_pos + s_t_corrected - kappa)
        self.g_neg = max(0, self.g_neg - s_t_corrected - kappa)

        position_size = self.getposition(self.data0).size

        # Open position logic
        if position_size == 0:
            beta_now = self.data2.beta[0]
            if pd.isna(beta_now) or beta_now <= 0:
                return
            self.size0 = 10
            self.size1 = round(beta_now * 10)

            if self.g_pos > h:
                # Calculate signal strength: magnitude of cumulative sum
                # exceeding threshold h
                signal_strength = (self.g_pos - h) / h
                self._open_position(short=True, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0
            elif self.g_neg > h:
                # Calculate signal strength: magnitude of cumulative sum
                # exceeding threshold h
                signal_strength = (self.g_neg - h) / h
                self._open_position(short=False, signal_strength=signal_strength)
                self.g_pos = self.g_neg = 0
        else:
            # Existing position: increase holding days counter
            if self.in_position:
                self.holding_counter += 1

                # Close position when target holding days are reached
                if self.holding_counter >= self.target_holding_days:
                    print(
                        f"holding days reached target {self.target_holding_days} days,"
                        " closing"
                    )
                    self._close_positions()

    def notify_trade(self, trade):
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
                % (
                    trade.ref,
                    bt.num2date(trade.dtopen),
                    trade.size,
                    trade.value,
                )
            )

    def get_backtest_data(self):
        """Get backtest data for export to CSV"""
        return pd.DataFrame(self.record_data)

    def get_stats(self):
        """Return strategy statistics"""
        stats = {
            "total_trades": self.total_trades,
            "total_holding_days": self.total_holding_days,
            "avg_holding_days": (self.total_holding_days / max(1, self.total_trades)),
            "max_holding_days": (
                max(self.holding_days_list) if self.holding_days_list else 0
            ),
            "min_holding_days": (
                min(self.holding_days_list) if self.holding_days_list else 0
            ),
            "min_cash": self.min_cash,  # Add minimum cash
            "min_cash_date": self.min_cash_date,  # Add minimum cash date
        }
        return stats


def main():
    # Parse command line arguments
    args = parse_args()
    print(f"Parsed arguments: {args}")

    # Read data
    output_file = "/Users/f/Desktop/ricequant/1d_2017to2024_noadjust.h5"
    df0 = pd.read_hdf(output_file, key=args.df0_key).reset_index()
    df1 = pd.read_hdf(output_file, key=args.df1_key).reset_index()

    # Ensure date column format is correct
    df0["date"] = pd.to_datetime(df0["date"])
    df1["date"] = pd.to_datetime(df1["date"])

    # Calculate rolling spread
    df_spread = calculate_rolling_spread(df0, df1, window=args.window)
    print("Rolling spread calculation completed, example coefficients:")
    print(df_spread.head())

    # Set backtest date range
    fromdate = datetime.datetime.strptime(args.fromdate, "%Y-%m-%d")
    todate = datetime.datetime.strptime(args.todate, "%Y-%m-%d")

    # Filter dataframes by date before passing to Backtrader
    df0_bt = df0[(df0["date"] >= fromdate) & (df0["date"] <= todate)]
    df1_bt = df1[(df1["date"] >= fromdate) & (df1["date"] <= todate)]
    df_spread_bt = df_spread[
        (df_spread["date"] >= fromdate) & (df_spread["date"] <= todate)
    ]
    data0 = bt.feeds.PandasData(dataname=df0_bt, datetime="date")
    data1 = bt.feeds.PandasData(dataname=df1_bt, datetime="date")
    data2 = SpreadData(dataname=df_spread_bt, datetime="date")

    # Create backtesting engine
    cerebro = bt.Cerebro()
    cerebro.adddata(data0, name=args.df0_key.replace("/", ""))
    cerebro.adddata(data1, name=args.df1_key.replace("/", ""))
    cerebro.adddata(data2, name="spread")

    # Add strategy
    cerebro.addstrategy(
        DynamicSpreadCUSUMStrategy,
        win=args.win,
        k_coeff=args.k_coeff,
        h_coeff=args.h_coeff,
        base_holding_days=args.base_holding_days,
        days_factor=args.days_factor,
    )

    # Set initial cash and slippage
    cerebro.broker.setcash(args.setcash)
    cerebro.broker.set_shortcash(False)
    cerebro.broker.set_slippage_perc(args.setslippage)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.DrawDown)  # Drawdown analyzer
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        timeframe=bt.TimeFrame.Days,  # Use daily data
        riskfreerate=0,  # Default risk-free rate
        annualize=True,  # Do not annualize
    )
    cerebro.addanalyzer(
        bt.analyzers.Returns,
        tann=bt.TimeFrame.Days,  # Annualization factor, 252 trading days
    )
    # The period here can be daily, weekly, monthly, etc.
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.Cash)
    cerebro.addobserver(bt.observers.CumValue)

    # Run backtest
    results = cerebro.run()
    strategy = results[0]  # Get strategy instance

    # Get analysis results
    drawdown = strategy.analyzers.drawdown.get_analysis()
    sharpe = strategy.analyzers.sharperatio.get_analysis()
    roi = strategy.analyzers.roianalyzer.get_analysis()
    total_returns = strategy.analyzers.returns.get_analysis()  # Get total return rate
    cagr = strategy.analyzers.cagranalyzer.get_analysis()
    trades = strategy.analyzers.tradeanalyzer.get_analysis()

    # Get position statistics
    stats = strategy.get_stats()

    # Print analysis results
    print("=============Backtest Results================")
    print(f"\nSharpe Ratio: {sharpe.get('sharperatio', 0):.2f}")
    print(f"Drawdown: {drawdown.get('max', {}).get('drawdown', 0):.2f} %")
    print(f"Annualized/Normalized return: {total_returns.get('rnorm100', 0):.2f}%")
    print(f"Total compound return: {roi.get('roi100', 0):.2f}%")
    print(f"Annualized return: {cagr.get('cagr', 0):.2f} ")
    print(f"Sharpe ratio: {cagr.get('sharpe', 0):.2f}")

    # Trade statistics
    total_trades = trades.get("total", {}).get("total", 0)
    win_trades = trades.get("won", {}).get("total", 0)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    print(f"Total trades: {total_trades}")
    print(f"Win rate: {win_rate:.2f}%")

    # Position statistics
    print(f"Average holding days: {stats['avg_holding_days']:.2f} days")
    print(
        f"Holding days range: {stats['min_holding_days']} to"
        f" {stats['max_holding_days']} days"
    )

    # Print minimum cash information
    print(f"Minimum cash: {stats['min_cash']:.2f}")
    print(f"Minimum cash date: {stats['min_cash_date']}")

    # Export CSV
    if args.export_csv:
        # Get backtest data
        backtest_data = strategy.get_backtest_data()
        # Generate filename
        params_str = f"win{args.win}_k{args.k_coeff}_h{args.h_coeff}_base{
            args.base_holding_days
        }_factor{args.days_factor}"
        filename = f"outcome/CUSUM_backtest_{args.df0_key.replace('/', '')}{
            args.df1_key.replace('/', '')
        }_{params_str}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        # Save CSV
        backtest_data.to_csv(filename, index=False)
        print(f"Backtest data saved to: {filename}")

    # Plot results
    if args.plot:
        cerebro.plot(volume=False, spread=True)


if __name__ == "__main__":
    main()
