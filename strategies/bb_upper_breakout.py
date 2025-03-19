#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2023-2025
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
"""
BOLLINGER BANDS UPPER BREAKOUT STRATEGY - (bb_upper_breakout)
===============================================================

This strategy is based on the Bollinger Bands breakout concept, where prices breaking
out above the upper Bollinger Band are considered a sign of strength and momentum,
potentially signaling the beginning of a new trend.

STRATEGY LOGIC:
--------------
- Go LONG when price CLOSES ABOVE the UPPER Bollinger Band
- Exit LONG when price CLOSES BELOW the MIDDLE Bollinger Band or a trailing stop is hit
- Optional stop loss at a fixed percentage below entry

MARKET CONDITIONS:
----------------
*** THIS STRATEGY IS SPECIFICALLY DESIGNED FOR TRENDING MARKETS ***
- PERFORMS BEST: During the start of strong uptrends or in momentum-driven markets
- AVOID USING: During sideways/ranging/choppy markets which can lead to false breakouts
- IDEAL TIMEFRAMES: 1-hour, 4-hour, and daily charts
- OPTIMAL MARKET CONDITION: Markets transitioning from consolidation to trend

The strategy will struggle in sideways markets as breakouts are often false and lead
to rapid reversals. This strategy aims to capture the beginning of new trends and
is most effective when combined with volume confirmation.

BOLLINGER BANDS:
--------------
Bollinger Bands consist of:
- A middle band (typically a 20-period moving average)
- An upper band (middle band + 2 standard deviations)
- A lower band (middle band - 2 standard deviations)

These bands adapt to volatility - widening during volatile periods and 
narrowing during less volatile periods.

POSITION SIZING & RISK MANAGEMENT:
---------------------------------
- Uses risk-based position sizing
- Optional trailing stop to lock in profits
- Fixed stop loss option to limit downside risk
- Maximum position size limit to prevent overexposure

USAGE:
------
python strategies/bb_upper_breakout.py --data SYMBOL --fromdate YYYY-MM-DD --todate YYYY-MM-DD [options]

REQUIRED ARGUMENTS:
------------------
--data, -d      : Stock symbol to retrieve data for (e.g., AAPL, MSFT, TSLA)
--fromdate, -f  : Start date for historical data in YYYY-MM-DD format (default: 2024-01-01)
--todate, -t    : End date for historical data in YYYY-MM-DD format (default: 2024-12-31)

DATABASE PARAMETERS:
------------------
--dbuser, -u    : PostgreSQL username (default: jason)
--dbpass, -pw   : PostgreSQL password (default: fsck)
--dbname, -n    : PostgreSQL database name (default: market_data)
--cash, -c      : Initial cash for the strategy (default: $100,000)

BOLLINGER BANDS PARAMETERS:
-------------------------
--bb-length, -bl: Period for Bollinger Bands calculation (default: 20)
--bb-mult, -bm  : Multiplier for standard deviation (default: 2.0)
--matype, -mt   : Moving average type for Bollinger Bands basis (default: SMA, options: SMA, EMA, WMA, SMMA)
--volume-mult, -vm: Volume multiplier for breakout confirmation (default: 1.5)
--check-volume, -cv: Consider volume for breakout confirmation (default: False)

EXIT PARAMETERS:
---------------
--use-stop, -us : Use stop loss (default: True) 
--stop-pct, -sp : Stop loss percentage (default: 2.0)
--trailing-stop, -ts : Enable trailing stop loss (default: True)
--trail-percent, -tp : Trailing stop percentage (default: 2.0)

POSITION SIZING:
---------------
--risk-percent, -rp  : Percentage of equity to risk per trade (default: 1.0)
--max-position, -mp  : Maximum position size as percentage of equity (default: 20.0)

TRADE THROTTLING:
---------------
--trade-throttle-days, -ttd : Minimum days between trades (default: 1)

OTHER:
-----
--plot, -pl     : Generate and show a plot of the trading activity

EXAMPLE:
--------
python strategies/bb_upper_breakout.py --data AAPL --fromdate 2023-01-01 --todate 2023-12-31 --check-volume --volume-mult 1.8 --trailing-stop --trail-percent 3.0 --plot
"""

from __future__ import (absolute_import, division, print_function,
                      unicode_literals)

import argparse
import datetime
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.indicators as btind

# Import utility functions
from strategies.utils import get_db_data, print_performance_metrics, TradeThrottling, add_standard_analyzers

# Add the parent directory to the Python path to import shared modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class StockPriceData(bt.feeds.PandasData):
    """
    Stock Price Data Feed
    """
    params = (
        ('datetime', None),  # Column containing the date (index)
        ('open', 'Open'),    # Column containing the open price
        ('high', 'High'),    # Column containing the high price
        ('low', 'Low'),      # Column containing the low price
        ('close', 'Close'),  # Column containing the close price
        ('volume', 'Volume'), # Column containing the volume
        ('openinterest', None)  # Column for open interest (not available)
    )


class BBUpperBreakoutStrategy(bt.Strategy, TradeThrottling):
    """
    Bollinger Bands Upper Breakout Strategy

    This strategy attempts to capture breakouts by:
    1. Buying when price closes above the upper Bollinger Band (with optional volume confirmation)
    2. Selling when price closes below the middle Bollinger Band
    
    Additional exit mechanisms include:
    - Stop loss to limit potential losses
    - Trailing stop loss to lock in profits
    
    Strategy Logic:
    - Buy when price closes above the upper Bollinger Band with volume confirmation
    - Exit when price closes below the middle Bollinger Band or hits a stop
    - Uses risk-based position sizing for proper money management
    - Implements cool down period to avoid overtrading 
    
    ** IMPORTANT: This strategy is specifically designed for trending markets **
    It performs poorly in sideways/ranging markets where breakouts are often false.
    
    Best Market Conditions:
    - Strong uptrending markets with momentum
    - Periods following consolidation or base building
    - Market environments with sector rotation into new leadership
    - Avoid using in choppy, sideways, or range-bound markets
    """

    params = (
        # Bollinger Bands parameters
        ('bb_period', 20),               # Period for Bollinger Bands
        ('bb_dev', 2.0),                 # Standard deviations for Bollinger Bands
        ('bb_matype', 'SMA'),            # Moving average type for Bollinger Bands
        
        # Entry parameters
        ('require_volume', True),        # Require volume confirmation for entry
        ('vol_factor', 1.5),             # Volume must be this times the average
        ('vol_lookback', 20),            # Period for volume average calculation
        
        # Exit parameters
        ('exit_below_middle', True),     # Exit when price closes below middle band
        
        # Stop loss parameters
        ('use_stop_loss', True),         # Use a stop loss
        ('stop_pct', 5.0),               # Stop loss percentage below entry
        ('use_trailing_stop', True),     # Use a trailing stop
        ('trail_pct', 5.0),              # Trailing stop percentage
        
        # Risk management
        ('risk_percent', 1.0),           # Percentage of equity to risk per trade
        ('max_position', 20.0),          # Maximum position size as percentage
        
        # Trade throttling
        ('trade_throttle_days', 5),      # Minimum days between trades
        
        # Logging
        ('loglevel', 'info'),            # Logging level: debug, info, warning, error
    )

    def log(self, txt, dt=None, level='info'):
        """Logging function"""
        if level == 'debug' and self.p.loglevel != 'debug':
            return
            
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def __init__(self):
        # Store references to price data
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # Order and position tracking
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_price = None
        self.trail_price = None
        self.highest_price = None
        
        # For trade throttling
        self.last_trade_date = None
        
        # Determine MA type for Bollinger Bands
        if self.p.bb_matype == 'SMA':
            ma_class = bt.indicators.SimpleMovingAverage
        elif self.p.bb_matype == 'EMA':
            ma_class = bt.indicators.ExponentialMovingAverage
        elif self.p.bb_matype == 'WMA':
            ma_class = bt.indicators.WeightedMovingAverage
        elif self.p.bb_matype == 'SMMA':
            ma_class = bt.indicators.SmoothedMovingAverage
        else:
            # Default to SMA
            ma_class = bt.indicators.SimpleMovingAverage
            
        # Create Bollinger Bands
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.p.bb_period,
            devfactor=self.p.bb_dev,
            movav=ma_class
        )
        
        # Volume moving average for comparison
        self.volume_ma = bt.indicators.SimpleMovingAverage(
            self.datavolume, period=self.p.vol_lookback
        )
        
        # Create crossover indicators for signal generation
        self.price_cross_upper = bt.indicators.CrossUp(
            self.dataclose, self.bbands.lines.top
        )
        
        self.price_cross_middle = bt.indicators.CrossDown(
            self.dataclose, self.bbands.lines.mid
        )
        
        # Add ATR for stop loss calculation
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

    def calculate_position_size(self):
        """Calculate position size based on risk percentage"""
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        current_price = self.dataclose[0]
        
        # Calculate size based on risk percentage
        risk_amount = value * (self.p.risk_percent / 100)
        risk_per_share = current_price * (self.p.stop_pct / 100)
        
        if risk_per_share > 0:
            size = int(risk_amount / risk_per_share)
        else:
            # Fallback calculation based on max position
            size = int((value * self.p.max_position / 100) / current_price)
        
        # Make sure we don't exceed maximum position size
        max_size = int((cash * self.p.max_position / 100) / current_price)
        return min(size, max_size)

    def check_volume_confirmation(self):
        """Check if volume is high enough to confirm the breakout"""
        if not self.p.require_volume:
            return True
            
        current_volume = self.datavolume[0]
        avg_volume = self.volume_ma[0]
        
        # Volume should be at least X times the average
        return current_volume >= (avg_volume * self.p.vol_factor)

    def next(self):
        # If an order is pending, we cannot send a new one
        if self.order:
            return
            
        # Check for trailing stop if enabled
        if self.position and self.p.use_trailing_stop and self.trail_price is not None:
            # Update the trailing stop if price moves higher
            if self.datahigh[0] > self.highest_price:
                self.highest_price = self.datahigh[0]
                self.trail_price = self.highest_price * (1.0 - self.p.trail_pct / 100.0)
                self.log(f'Trailing stop updated to: {self.trail_price:.2f}')
            
            # Check if trailing stop is hit
            if self.datalow[0] <= self.trail_price:
                self.log(f'SELL CREATE (Trailing Stop): {self.dataclose[0]:.2f}')
                self.order = self.sell()
                return
        
        # Check for stop loss if we're in the market and stop loss is enabled
        if self.position and self.p.use_stop_loss and self.stop_price is not None:
            if self.datalow[0] < self.stop_price:
                self.log(f'STOP LOSS TRIGGERED: Price: {self.datalow[0]:.2f}, Stop: {self.stop_price:.2f}')
                self.order = self.close()
                return
                
        # Check for price crossing below middle band - exit signal
        if self.position and self.price_cross_middle[0]:
            self.log(f'MIDDLE BAND EXIT: Price: {self.dataclose[0]:.2f}, Middle Band: {self.bbands.lines.mid[0]:.2f}')
            self.order = self.close()
            return
        
        # If we are not in the market, look for a buy signal
        if not self.position:
            # Check if we can trade now (throttling)
            if not self.can_trade_now():
                return
                
            # Buy if price closes above upper band with volume confirmation
            if self.dataclose[0] > self.bbands.lines.top[0] and self.check_volume_confirmation():
                # Calculate position size
                size = self.calculate_position_size()
                
                volume_msg = ""
                if self.p.require_volume:
                    volume_msg = f', Volume: {self.datavolume[0]:.0f} (Avg: {self.volume_ma[0]:.0f})'
                
                self.log(f'BUY SIGNAL: Price: {self.dataclose[0]:.2f}, Upper Band: {self.bbands.lines.top[0]:.2f}{volume_msg}')
                
                if size > 0:
                    self.order = self.buy(size=size)
                    
                    # Set stop loss price if enabled
                    if self.p.use_stop_loss:
                        self.stop_price = self.dataclose[0] * (1.0 - self.p.stop_pct / 100.0)
                        self.log(f'Stop loss set at {self.stop_price:.2f}')
                    
                    # Set trailing stop if enabled
                    if self.p.use_trailing_stop:
                        self.highest_price = self.dataclose[0]
                        self.trail_price = self.dataclose[0] * (1.0 - self.p.trail_pct / 100.0)
                        self.log(f'Initial trailing stop set at {self.trail_price:.2f}')
                    
                    # Update last trade date for throttling
                    self.last_trade_date = self.datas[0].datetime.date(0)

    def stop(self):
        """Called when backtest is complete"""
        self.log('Bollinger Bands Upper Breakout Strategy completed', level='info')
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}', level='info')
        
        # Add a note about market conditions
        self.log('NOTE: This strategy is specifically designed for TRENDING MARKETS', level='info')
        self.log('      It performs poorly in sideways markets with frequent false breakouts', level='info')

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order pending, do nothing
            return

        # Check if order was completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.2f}, Size: {order.executed.size}, '
                       f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # sell
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.2f}, Size: {order.executed.size}, '
                       f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.status}')
        
        # Reset order status
        self.order = None

    def notify_trade(self, trade):
        """Track completed trades"""
        if not trade.isclosed:
            return
        
        self.log(f'TRADE COMPLETED: PnL: Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Bollinger Bands Upper Breakout Strategy',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    # Basic input parameters
    parser.add_argument('--data', '-d',
                       required=True,
                       help='Stock symbol to retrieve data for')
    
    parser.add_argument('--dbuser', '-u',
                       default='jason',
                       help='PostgreSQL username')
    
    parser.add_argument('--dbpass', '-pw',
                       default='fsck',
                       help='PostgreSQL password')
    
    parser.add_argument('--dbname', '-n',
                       default='market_data',
                       help='PostgreSQL database name')
    
    parser.add_argument('--fromdate', '-f',
                       default='2024-01-01',
                       help='Starting date in YYYY-MM-DD format')
    
    parser.add_argument('--todate', '-t',
                       default='2024-12-31',
                       help='Ending date in YYYY-MM-DD format')
    
    parser.add_argument('--cash', '-c',
                       default=100000.0, type=float,
                       help='Starting cash')
    
    # Bollinger Bands parameters
    parser.add_argument('--bb-length', '-bl',
                       default=20, type=int,
                       help='Period for Bollinger Bands calculation')
    
    parser.add_argument('--bb-mult', '-bm',
                       default=2.0, type=float,
                       help='Multiplier for standard deviation')
    
    parser.add_argument('--matype', '-mt',
                       default='SMA',
                       choices=['SMA', 'EMA', 'WMA', 'SMMA'],
                       help='Moving average type for Bollinger Bands basis')
    
    parser.add_argument('--check-volume', '-cv',
                       action='store_true',
                       help='Consider volume for breakout confirmation')
    
    parser.add_argument('--volume-mult', '-vm',
                       default=1.5, type=float,
                       help='Volume multiplier for breakout confirmation')
    
    # Exit parameters
    parser.add_argument('--use-stop', '-us',
                       action='store_true',
                       help='Use stop loss')
    
    parser.add_argument('--stop-pct', '-sp',
                       default=2.0, type=float,
                       help='Stop loss percentage')
    
    parser.add_argument('--trailing-stop', '-ts',
                       action='store_true',
                       help='Enable trailing stop loss')
    
    parser.add_argument('--trail-percent', '-tp',
                       default=2.0, type=float,
                       help='Trailing stop percentage')
    
    # Position sizing parameters
    parser.add_argument('--risk-percent', '-rp',
                       default=1.0, type=float,
                       help='Percentage of equity to risk per trade')
    
    parser.add_argument('--max-position', '-mp',
                       default=20.0, type=float,
                       help='Maximum position size as percentage of equity')
    
    # Trade throttling
    parser.add_argument('--trade-throttle-days', '-ttd',
                       default=1, type=int,
                       help='Minimum days between trades')
    
    # Plotting
    parser.add_argument('--plot', '-pl',
                       action='store_true',
                       help='Generate and show a plot of the trading activity')
    
    return parser.parse_args()


def main():
    """Main function to run the backtest"""
    args = parse_args()
    
    # Convert date strings to datetime objects
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    
    # Get data from database
    df = get_db_data(args.data, args.dbuser, args.dbpass, args.dbname, fromdate, todate)
    
    # Create a Data Feed
    data = StockPriceData(dataname=df)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    
    # Add the data feed to cerebro
    cerebro.adddata(data)
    
    # Add strategy to cerebro
    cerebro.addstrategy(
        BBUpperBreakoutStrategy,
        # Bollinger Bands parameters
        bb_period=args.bb_length,
        bb_dev=args.bb_mult,
        bb_matype=args.matype,
        
        # Entry parameters
        require_volume=args.check_volume,
        vol_factor=args.volume_mult,
        
        # Exit parameters
        exit_below_middle=args.use_stop,
        
        # Stop loss parameters
        use_stop_loss=args.use_stop,
        stop_pct=args.stop_pct,
        use_trailing_stop=args.trailing_stop,
        trail_pct=args.trail_percent,
        
        # Risk management parameters
        risk_percent=args.risk_percent,
        max_position=args.max_position,
        
        # Trade throttling
        trade_throttle_days=args.trade_throttle_days,
    )
    
    # Set initial cash
    cerebro.broker.setcash(args.cash)
    
    # Set commission - 0.1%
    cerebro.broker.setcommission(commission=0.001)
    
    # Add standard analyzers
    add_standard_analyzers(cerebro)
    
    # Print out the starting conditions
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')
    
    # Run the strategy
    results = cerebro.run()
    
    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: ${final_value:.2f}')
    
    # Print standard performance metrics
    print_performance_metrics(cerebro, results)
    
    # Extract and display detailed performance metrics
    print("\n==== DETAILED PERFORMANCE METRICS ====")
    
    # Get the first strategy instance
    strat = results[0]
    
    # Return
    ret_analyzer = strat.analyzers.returns
    total_return = ret_analyzer.get_analysis()['rtot'] * 100
    print(f"Return: {total_return:.2f}%")
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe_ratio.get_analysis()['sharperatio']
    if sharpe is None:
        sharpe = 0.0
    print(f"Sharpe Ratio: {sharpe:.4f}")
    
    # Max Drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    max_dd = dd.get('max', {}).get('drawdown', 0.0)
    print(f"Max Drawdown: {max_dd:.2f}%")
    
    # Trade statistics
    trade_analysis = strat.analyzers.trade_analyzer.get_analysis()
    
    # Total Trades
    total_trades = trade_analysis.get('total', {}).get('total', 0)
    print(f"Total Trades: {total_trades}")
    
    # Won Trades
    won_trades = trade_analysis.get('won', {}).get('total', 0)
    print(f"Won Trades: {won_trades}")
    
    # Lost Trades
    lost_trades = trade_analysis.get('lost', {}).get('total', 0)
    print(f"Lost Trades: {lost_trades}")
    
    # Win Rate
    if total_trades > 0:
        win_rate = (won_trades / total_trades) * 100
    else:
        win_rate = 0.0
    print(f"Win Rate: {win_rate:.2f}%")
    
    # Average Win
    avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0.0)
    print(f"Average Win: ${avg_win:.2f}")
    
    # Average Loss
    avg_loss = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0.0)
    print(f"Average Loss: ${avg_loss:.2f}")
    
    # Profit Factor
    gross_profit = trade_analysis.get('won', {}).get('pnl', {}).get('total', 0.0)
    gross_loss = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('total', 0.0))
    
    if gross_loss != 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float('inf') if gross_profit > 0 else 0.0
    
    print(f"Profit Factor: {profit_factor:.2f}")
    
    # Plot if requested
    if args.plot:
        cerebro.plot(style='candlestick', barup='green', bardown='red')


if __name__ == '__main__':
    main() 