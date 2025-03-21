"""
Utility functions for Backtrader strategies
"""

import datetime
import psycopg2
import pandas as pd
import backtrader as bt


def print_performance_metrics(cerebro, results, fromdate=None, todate=None):
    """
    Print standardized performance metrics from Backtrader's analyzers
    
    Parameters:
    - cerebro: The Cerebro instance
    - results: The results returned from cerebro.run()
    - fromdate: Start date for the backtest (optional)
    - todate: End date for the backtest (optional)
    
    Prints:
    - Final Portfolio Value
    - Return
    - Sharpe Ratio
    - Max Drawdown
    - Trade metrics (total, won, lost, win rate)
    - Average Win/Loss
    - Profit Factor
    - Buy & Hold Comparison
    """
    strat = results[0]
    
    # Get key metrics
    final_value = cerebro.broker.getvalue()
    initial_value = cerebro.broker.startingcash
    overall_return = ((final_value / initial_value) - 1.0) * 100
    
    # Trade Analysis for the summary metrics
    try:
        trades = strat.analyzers.trades.get_analysis()
        
        # Get trade metrics
        gross_profit = trades.get('won', {}).get('pnl', {}).get('total', 0)
        gross_loss = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
        net_profit = gross_profit - gross_loss
        
        # Get commission data - total commission sum from all trades
        commission_paid = 0
        for trade_type in ['won', 'lost']:
            if trade_type in trades and 'commission' in trades[trade_type]:
                commission_paid += trades[trade_type]['commission']['total']
        
        # If no commission from direct access, try to calculate from the difference between pnl and pnlcomm
        if commission_paid == 0:
            pnl_total = 0
            pnlcomm_total = 0
            for trade_type in ['won', 'lost']:
                if trade_type in trades and 'pnl' in trades[trade_type]:
                    pnl_total += trades[trade_type]['pnl'].get('total', 0)
                if trade_type in trades and 'pnlcomm' in trades[trade_type]:
                    pnlcomm_total += trades[trade_type]['pnlcomm'].get('total', 0)
            commission_paid = abs(pnl_total - pnlcomm_total)
        
        # Get max contracts held - maximum position size
        max_contracts = 0
        try:
            # Parse logs approach - most reliable method
            if hasattr(results[0], '_logs'):
                for log_entry in results[0]._logs:
                    if isinstance(log_entry, str):
                        # Check various formats where position size might be mentioned
                        size_patterns = [
                            ('BUY EXECUTED', 'Size:'),
                            ('SELL EXECUTED', 'Size:'),
                            ('BUY CREATE', 'Size:'),
                            ('SELL CREATE', 'Size:')
                        ]
                        
                        for pattern in size_patterns:
                            if pattern[0] in log_entry and pattern[1] in log_entry:
                                try:
                                    # Extract the size from the log entry
                                    parts = log_entry.split(pattern[1])[1].strip()
                                    size_str = parts.split(',')[0].strip()
                                    # Handle negative sizes in SELL operations
                                    if size_str.startswith('-'):
                                        size_str = size_str[1:]
                                    size = int(size_str)
                                    if size > max_contracts:
                                        max_contracts = size
                                except Exception:
                                    pass

            # Try to calculate from the strategy's calculate_position_size method output
            if max_contracts == 0 and hasattr(results[0], 'calculate_position_size'):
                try:
                    position_size = results[0].calculate_position_size()
                    if isinstance(position_size, (int, float)) and position_size > 0:
                        max_contracts = position_size
                except Exception:
                    pass
            
            # Check the trade records for position sizes
            if max_contracts == 0:
                # Direct examination of trade records
                for i, strategy in enumerate(results):
                    # Check completed trades
                    if hasattr(strategy, '_trades') and strategy._trades:
                        try:
                            for trade in strategy._trades:
                                if hasattr(trade, 'size'):
                                    size_value = 0
                                    if callable(getattr(trade, 'size', None)):
                                        try:
                                            size_value = trade.size()
                                        except:
                                            pass
                                    else:
                                        size_value = trade.size
                                        
                                    if isinstance(size_value, (int, float)):
                                        size_value = abs(size_value)
                                        if size_value > max_contracts:
                                            max_contracts = size_value
                        except Exception:
                            pass
                            
                    # Also check the trade analyzer data
                    if max_contracts == 0 and hasattr(strategy, 'analyzers'):
                        if hasattr(strategy.analyzers, 'trades') and hasattr(strategy.analyzers.trades, 'get_analysis'):
                            trade_analysis = strategy.analyzers.trades.get_analysis()
                            if 'total' in trade_analysis and 'total' in trade_analysis['total']:
                                if trade_analysis['total']['total'] > 0:
                                    # Find the largest position size from the actual execution logs
                                    for log in strategy._logs:
                                        if 'BUY EXECUTED' in log and 'Size:' in log:
                                            try:
                                                size_part = log.split('Size:')[1].split(',')[0].strip()
                                                size = int(size_part)
                                                max_contracts = max(max_contracts, size)
                                            except:
                                                pass
            
            # Use the calculate_position_size logic from the strategy directly
            if max_contracts == 0 and hasattr(cerebro, 'broker'):
                # Calculate based on the initial cash and first close price
                if hasattr(cerebro.broker, 'getcash') and hasattr(cerebro, 'datas') and cerebro.datas:
                    cash = cerebro.broker.getcash()
                    data = cerebro.datas[0]
                    
                    if hasattr(data, 'close') and len(data.close) > 0:
                        # Get the first price that would have been used
                        first_price = data.close[0] 
                        if first_price > 0:
                            # Similar to the strategy's position sizing logic (see calculate_position_size)
                            size = int(cash * 0.995 / first_price)
                            max_contracts = max(1, size)  # At least 1 share
            
            # Final fallback - analyze execution logs directly based on patterns
            if max_contracts == 0:
                for strat in results:
                    if hasattr(strat, 'notify_order'):
                        # Look for explicit BUY EXECUTED messages in logs
                        for log in getattr(strat, '_logs', []):
                            if 'BUY EXECUTED' in log:
                                # Extract size from pattern like "Size: 210"
                                try:
                                    size_part = log.split('Size:')[1].split(',')[0].strip()
                                    size = int(size_part)
                                    max_contracts = max(max_contracts, size)
                                except:
                                    pass
                
                # If still no max_contracts from logs, scan again with different pattern matching
                if max_contracts == 0 and hasattr(results[0], '_logs'):
                    for log in results[0]._logs:
                        if isinstance(log, str):
                            # Try various patterns to extract sizes
                            try:
                                if 'Size:' in log:
                                    # Generic "Size:" extraction
                                    size_part = log.split('Size:')[1].split()[0].strip(',')
                                    if size_part.startswith('-'):
                                        size_part = size_part[1:]  # Remove negative sign for position size
                                    size = int(size_part)
                                    max_contracts = max(max_contracts, size)
                            except:
                                pass
        
        except Exception as e:
            print(f"Warning: Error calculating max contracts: {e}")
        
        # If all methods failed, fall back to a theoretical estimation
        if max_contracts == 0:
            try:
                # Theoretical position size based on first price
                if hasattr(cerebro, 'datas') and cerebro.datas:
                    data = cerebro.datas[0]
                    if hasattr(data, 'close') and len(data.close) > 0:
                        # Use first close price for estimation
                        first_price = data.close[0]
                        if first_price > 0:
                            max_contracts = int(initial_value * 0.995 / first_price)
                            max_contracts = max(1, max_contracts)
            except Exception as e:
                print(f"Warning: Error calculating theoretical max contracts: {e}")
                # Last resort default
                max_contracts = int(initial_value / 500)  # Reasonable default assuming price around $500
        
        # Get max drawdown from drawdown analyzer
        try:
            drawdown = strat.analyzers.drawdown.get_analysis()
            max_drawdown_value = drawdown.get('max', {}).get('moneydown', 0)
            if max_drawdown_value == 0:  # Try alternative field if first one not available
                max_drawdown_value = drawdown.get('max', {}).get('drawdown', 0) * initial_value / 100
            max_drawdown_pct = drawdown.get('max', {}).get('drawdown', 0)
        except:
            max_drawdown_value = 0
            max_drawdown_pct = 0
        
        # Calculate max equity run-up based on the returns
        try:
            returns_analyzer = strat.analyzers.returns.get_analysis()
            max_runup_pct = returns_analyzer.get('maxup', 0) * 100  # Convert to percentage
            max_runup_value = max_runup_pct * initial_value / 100
        except:
            max_runup_value = 0
            max_runup_pct = 0
            
        # If no max run-up value, use the highest peak minus initial value
        if max_runup_value == 0:
            try:
                # Find the highest peak value during trading
                highest_value = final_value
                for trade in trades.get('total', {}).get('lines', []):
                    if 'peak' in trade and trade['peak'] > highest_value:
                        highest_value = trade['peak']
                max_runup_value = max(0, highest_value - initial_value)
                max_runup_pct = (max_runup_value / initial_value) * 100 if initial_value else 0
            except:
                max_runup_value = 0
                max_runup_pct = 0
        
        # Calculate percentages
        gross_profit_pct = (gross_profit / initial_value) * 100 if initial_value else 0
        gross_loss_pct = (gross_loss / initial_value) * 100 if initial_value else 0
        net_profit_pct = (net_profit / initial_value) * 100 if initial_value else 0
        
        # Try to get max contracts again from the positions if it's still 0
        if max_contracts == 0:
            max_contracts = trades.get('streak', {}).get('won', {}).get('longest', 0)
            
            # Last resort - use the largest size from any executed trade
            if max_contracts == 0:
                for i in range(len(strat._trades)):
                    if strat._trades[i].size > max_contracts:
                        max_contracts = strat._trades[i].size
    except Exception as e:
        print(f"Warning: Error calculating performance metrics: {e}")
        # Default values if analyzer data is unavailable
        gross_profit = 0
        gross_loss = 0
        net_profit = final_value - initial_value
        commission_paid = 0
        max_drawdown_value = 0
        max_runup_value = 0
        max_contracts = 0
        gross_profit_pct = 0
        gross_loss_pct = 0
        net_profit_pct = (net_profit / initial_value) * 100 if initial_value else 0
        max_drawdown_pct = 0
        max_runup_pct = 0
    
    # Get Buy & Hold data
    try:
        data = cerebro.datas[0]
        full_df = data.p.dataname  # Get the original pandas DataFrame
        
        if isinstance(full_df, pd.DataFrame) and not full_df.empty:
            first_close = full_df['Close'].iloc[0]
            last_close = full_df['Close'].iloc[-1]
            
            # Calculate Buy & Hold return
            buy_hold_return = ((last_close / first_close) - 1.0) * 100
            buy_hold_value = cerebro.broker.startingcash * (1.0 + buy_hold_return / 100.0)
            buy_hold_profit = buy_hold_value - cerebro.broker.startingcash
        else:
            buy_hold_return = 0
            buy_hold_profit = 0
    except Exception as e:
        buy_hold_return = 0
        buy_hold_profit = 0
    
    # Print PERFORMANCE METRICS section
    print('\n==== PERFORMANCE METRICS ====')
    
    # Direct key-value format without headers, separators, or extra spacing
    print(f'Open P&L: 0 USD (0.00%)')
    
    if net_profit >= 0:
        print(f'Net profit: +{net_profit:.2f} USD (+{net_profit_pct:.2f}%)')
    else:
        print(f'Net profit: {net_profit:.2f} USD ({net_profit_pct:.2f}%)')
    
    print(f'Gross profit: {gross_profit:.2f} USD ({gross_profit_pct:.2f}%)')
    print(f'Gross loss: {gross_loss:.2f} USD ({gross_loss_pct:.2f}%)')
    print(f'Commission paid: {commission_paid:.2f} USD')
    
    if buy_hold_profit >= 0:
        print(f'Buy & hold return: +{buy_hold_profit:.2f} USD (+{buy_hold_return:.2f}%)')
    else:
        print(f'Buy & hold return: {buy_hold_profit:.2f} USD ({buy_hold_return:.2f}%)')
    
    print(f'Max equity run-up: {max_runup_value:.2f} USD ({max_runup_pct:.2f}%)')
    print(f'Max equity drawdown: {max_drawdown_value:.2f} USD ({max_drawdown_pct:.2f}%)')
    print(f'Max contracts held: {max_contracts}')
    
    # Print DETAILED PERFORMANCE METRICS section
    print('\n==== DETAILED PERFORMANCE METRICS ====')
    
    # Print date range
    if fromdate:
        print(f'Start Date: {fromdate.strftime("%Y-%m-%d")}')
    if todate:
        print(f'End Date: {todate.strftime("%Y-%m-%d")}')
    
    # Final Portfolio Value
    print(f'Final Portfolio Value: ${final_value:.2f}')
    
    # Overall Return (already shown in the summary)
    # print(f'Overall Return: {overall_return:.2f}%')
    
    # Returns from analyzer
    try:
        returns = strat.analyzers.returns.get_analysis()
        total_return = returns.get('rtot', 0) * 100
        if total_return is not None:
            print(f'Strategy Return: {total_return:.2f}%')
        else:
            print('Strategy Return: N/A')
    except Exception as e:
        print(f'Unable to calculate return: {e}')
    
    # Sharpe Ratio
    try:
        sharpe = strat.analyzers.sharperatio.get_analysis()
        sharpe_ratio = sharpe.get('sharperatio', 0)
        if sharpe_ratio is not None and sharpe_ratio != 0.0:
            print(f'Sharpe Ratio: {sharpe_ratio:.4f}')
        else:
            print('Sharpe Ratio: N/A')
    except Exception as e:
        print(f'Unable to calculate Sharpe ratio: {e}')
    
    # Drawdown (already shown in summary metrics)
    # try:
    #     drawdown = strat.analyzers.drawdown.get_analysis()
    #     max_dd = drawdown.get('max', {}).get('drawdown', 0)
    #     if max_dd is not None:
    #         print(f'Max Drawdown: {max_dd:.2f}%')
    #     else:
    #         print('Max Drawdown: N/A')
    # except Exception as e:
    #     print(f'Unable to calculate Max Drawdown: {e}')
    
    # Trade Analysis
    try:
        trades = strat.analyzers.trades.get_analysis()
        
        # Total Trades
        total_trades = trades.get('total', {}).get('total', 0)
        print(f'Total Trades: {total_trades}')
        
        # Open trades (positions still open at the end)
        open_trades = trades.get('total', {}).get('open', 0)
        if open_trades > 0:
            print(f'Open Positions: {open_trades}')
        
        # Handle case where some trades are still open
        closed_trades = total_trades - open_trades
        
        if closed_trades > 0:
            # Won Trades
            won_trades = trades.get('won', {}).get('total', 0)
            print(f'Won Trades: {won_trades}')
            
            # Lost Trades
            lost_trades = trades.get('lost', {}).get('total', 0)
            print(f'Lost Trades: {lost_trades}')
            
            # Win Rate
            win_rate = won_trades / closed_trades * 100 if closed_trades > 0 else 0
            print(f'Win Rate: {win_rate:.2f}%')
            
            # Average Win
            avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
            print(f'Average Win: ${avg_win:.2f}')
            
            # Average Loss
            avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
            print(f'Average Loss: ${avg_loss:.2f}')
            
            # Profit Factor
            if gross_loss != 0:
                profit_factor = gross_profit / gross_loss
            else:
                profit_factor = float('inf') if gross_profit > 0 else 0.0
                
            print(f'Profit Factor: {profit_factor:.2f}')
        elif open_trades > 0:
            print('Note: All trades are still open, no closed trade metrics available')
        else:
            print('No trades executed during the backtest period')
    except Exception as e:
        print(f'Unable to calculate trade statistics: {e}')
    
    # Keep the Buy & Hold comparison detail section
    try:
        # Get the data
        data = cerebro.datas[0]
        
        # Get the full data range from the data feed
        # We need to access the underlying data array which may contain more data than what's in the subset
        full_df = data.p.dataname  # This gets the original pandas DataFrame
        
        if isinstance(full_df, pd.DataFrame) and not full_df.empty:
            # Use the first and last dates from the full dataframe
            first_date = full_df.index[0].strftime('%Y-%m-%d')
            first_close = full_df['Close'].iloc[0]
            
            last_date = full_df.index[-1].strftime('%Y-%m-%d')
            last_close = full_df['Close'].iloc[-1]
            
            # Print date range info for reference
            print(f"\nData range used for Buy & Hold: {first_date} to {last_date}")
            
            # Calculate Buy & Hold return
            buy_hold_return = ((last_close / first_close) - 1.0) * 100
            
            # Calculate the Buy & Hold final value
            buy_hold_value = cerebro.broker.startingcash * (1.0 + buy_hold_return / 100.0)
            
            print(f'\n==== BUY & HOLD COMPARISON ====')
            print(f'Buy Date: {first_date}')
            print(f'Buy Price: ${first_close:.2f}')
            print(f'Sell Date: {last_date}')
            print(f'Sell Price: ${last_close:.2f}')
            print(f'Buy & Hold Return: {buy_hold_return:.2f}%')
            print(f'Buy & Hold Final Value: ${buy_hold_value:.2f}')
            
            # Compare strategy to Buy & Hold
            outperf = overall_return - buy_hold_return
            if outperf > 0:
                print(f'Strategy OUTPERFORMED Buy & Hold by: {outperf:.2f}%')
            else:
                print(f'Strategy UNDERPERFORMED Buy & Hold by: {abs(outperf):.2f}%')
        else:
            print("Unable to access original DataFrame for Buy & Hold comparison")
    except Exception as e:
        print(f'Unable to calculate Buy & Hold comparison: {e}')


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
        SELECT date, open, high, low, close, volume
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
        
        print(f"Successfully fetched data for {symbol}. Retrieved {len(df)} bars.")
        print(f"Data range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
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