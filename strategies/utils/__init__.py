"""
Utility functions for Backtrader strategies
"""

import datetime
import psycopg2
import pandas as pd
import backtrader as bt


def print_performance_metrics(cerebro, results):
    """
    Print standardized performance metrics from Backtrader's analyzers
    
    Parameters:
    - cerebro: The Cerebro instance
    - results: The results returned from cerebro.run()
    
    Prints:
    - Final Portfolio Value
    - Return
    - Sharpe Ratio
    - Max Drawdown
    - Trade metrics (total, won, lost, win rate)
    - Average Win/Loss
    - Profit Factor
    """
    strat = results[0]
    print('\n==== DETAILED PERFORMANCE METRICS ====')
    
    # Final Portfolio Value
    final_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: ${final_value:.2f}')
    
    # Returns
    try:
        returns = strat.analyzers.returns.get_analysis()
        total_return = returns.get('rtot', 0) * 100
        if total_return is not None:
            print(f'Return: {total_return:.2f}%')
        else:
            print('Return: N/A')
    except Exception as e:
        print(f'Unable to calculate return: {e}')
    
    # Sharpe Ratio
    try:
        sharpe = strat.analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get('sharperatio', 0)
        if sharpe_ratio is not None:
            print(f'Sharpe Ratio: {sharpe_ratio:.4f}')
        else:
            print('Sharpe Ratio: N/A')
    except Exception as e:
        print(f'Unable to calculate Sharpe ratio: {e}')
    
    # Drawdown
    try:
        drawdown = strat.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get('max', {}).get('drawdown', 0)
        if max_dd is not None:
            print(f'Max Drawdown: {max_dd:.2f}%')
        else:
            print('Max Drawdown: N/A')
    except Exception as e:
        print(f'Unable to calculate Max Drawdown: {e}')
    
    # Trade Analysis
    try:
        trades = strat.analyzers.trades.get_analysis()
        
        # Total Trades
        total_trades = trades.get('total', {}).get('total', 0)
        print(f'Total Trades: {total_trades}')
        
        if total_trades > 0:
            # Won Trades
            won_trades = trades.get('won', {}).get('total', 0)
            print(f'Won Trades: {won_trades}')
            
            # Lost Trades
            lost_trades = trades.get('lost', {}).get('total', 0)
            print(f'Lost Trades: {lost_trades}')
            
            # Win Rate
            win_rate = won_trades / total_trades * 100 if total_trades > 0 else 0
            print(f'Win Rate: {win_rate:.2f}%')
            
            # Average Win
            avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
            print(f'Average Win: ${avg_win:.2f}')
            
            # Average Loss
            avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
            print(f'Average Loss: ${avg_loss:.2f}')
            
            # Profit Factor
            gross_profit = trades.get('won', {}).get('pnl', {}).get('total', 0)
            gross_loss = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
            
            if gross_loss != 0:
                profit_factor = gross_profit / gross_loss
            else:
                profit_factor = float('inf') if gross_profit > 0 else 0.0
                
            print(f'Profit Factor: {profit_factor:.2f}')
        else:
            print('No trades executed during the backtest period')
    except Exception as e:
        print(f'Unable to calculate trade statistics: {e}')


def get_db_data(symbol, dbuser, dbpass, dbname, fromdate, todate):
    """
    Fetch historical price data from PostgreSQL database
    
    Parameters:
    - symbol: The symbol to fetch data for
    - dbuser: PostgreSQL username
    - dbpass: PostgreSQL password
    - dbname: PostgreSQL database name
    - fromdate: Start date as datetime object
    - todate: End date as datetime object
    
    Returns:
    - DataFrame with OHLCV data
    """
    # Format dates for database query
    from_str = fromdate.strftime('%Y-%m-%d %H:%M:%S')
    to_str = todate.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Fetching data from PostgreSQL database for {symbol} from {from_str} to {to_str}")
    
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host="localhost",
            user=dbuser,
            password=dbpass,
            database=dbname
        )
        
        # Create a cursor to execute queries
        cursor = connection.cursor()
        
        # Query the data
        query = """
        SELECT date, open, high, low, close, volume, rsi
        FROM stock_price_data
        WHERE symbol = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """
        
        # Execute the query
        cursor.execute(query, (symbol, from_str, to_str))
        rows = cursor.fetchall()
        
        # Check if any data was retrieved
        if not rows:
            raise Exception(f"No data found for {symbol} in the specified date range")
        
        # Convert to pandas DataFrame
        if len(rows[0]) > 6:  # Check if RSI is included
            df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI'])
        else:
            df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Convert 'Date' to datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # Ensure numeric data types
        df['Open'] = pd.to_numeric(df['Open'])
        df['High'] = pd.to_numeric(df['High'])
        df['Low'] = pd.to_numeric(df['Low'])
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        if 'RSI' in df.columns:
            df['RSI'] = pd.to_numeric(df['RSI'])
        
        print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")
        
        # Close the database connection
        cursor.close()
        connection.close()
        
        return df
        
    except psycopg2.Error as err:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        raise Exception(f"Database error: {err}")
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        raise Exception(f"Error fetching data: {e}")


class TradeThrottling:
    """
    Trade throttling functionality that can be added to any strategy
    
    This mixin allows setting a minimum number of days between trades to avoid
    overtrading and to let positions develop. It can be configured through the
    'trade_throttle_days' parameter.
    
    Usage in __init__:
        self.last_trade_date = None
        
    Usage in next method:
        if not self.can_trade_now():
            return
    """
    
    def can_trade_now(self):
        """
        Check if enough days have passed since the last trade for throttling
        
        Returns:
            bool: True if a new trade can be entered, False otherwise
        """
        # If throttling is disabled or no previous trade, allow trading
        if not hasattr(self.p, 'trade_throttle_days') or self.p.trade_throttle_days <= 0 or self.last_trade_date is None:
            return True
            
        # Get current date
        current_date = self.datas[0].datetime.date(0)
        
        # Calculate days passed
        days_passed = (current_date - self.last_trade_date).days
        
        # Allow trading if enough days have passed
        return days_passed >= self.p.trade_throttle_days


# Standard Backtrader analyzer setup
def add_standard_analyzers(cerebro):
    """
    Add the standard set of analyzers to a Cerebro instance
    
    Parameters:
    - cerebro: The Cerebro instance to add analyzers to
    """
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    return cerebro 