"""agent.py module.

Description of the module functionality."""


import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf  # type: ignore
from pydantic_ai import Agent, RunContext

# Define the agent
finance_agent = Agent(
    "openai:gpt-4o",
    deps_type=dict,
    output_type=str,
    system_prompt=(
        "This agent provides tools for financial data analysis, including pulling"
        " historical data and plotting time series."
    ),
)

# Tool 1: Pull historical data from yfinance

# For IB, tools we'd minimally need:
# backtesting tools
# paper trading tools
# long trading strategy:
# - buy to open
# - sell to close
# short selling strategy:
# - sell to open
# - buy to close
# check open positions
# check daily P&L
# check daily data usage
# generate daily report
# - profit/loss
# - open positions
# - daily data usage
# live trading tools - same as paper trading


@finance_agent.tool
def pull_historical_data(
    ctx: RunContext[dict], ticker: str, start: str, end: str
) -> pd.DataFrame:
"""Pull historical data for a given ticker and date range and save as a CSV file.

Args::
        ctx: The run context containing dependencies.
        ticker: The stock ticker symbol (e.g., 'AAPL' for Apple Inc.).
        start: The start date in 'YYYY-MM-DD' format.
        end: The end date in 'YYYY-MM-DD' format.

Returns::
        pd.DataFrame: A DataFrame containing the historical price data."""
    """
    data = yf.download(ticker, start=start, end=end)
    data = cast(pd.DataFrame, data)
    fname = f"{ticker}_{start}_{end}.csv"
    data.to_csv(fname)


# Tool 2: Plot time series from a DataFrame


@finance_agent.tool
def plot_time_series(
    ctx: RunContext[dict],
    csv_file: str,
    column: str,
    title: str = "Time Series Plot",
) -> None:
"""Plot a time series from a CSV file and save it as a PNG image.

Args::
        ctx: The run context containing dependencies.
        csv_file: Path to the CSV file containing the time series data.
        column: The column name in the CSV file to plot.
        title: Title for the plot. Defaults to "Time Series Plot".

Raises::
        ValueError: If the specified column is not found in the CSV file."""
    """
    data = pd.read_csv(csv_file)
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    data[column].plot(title=title)
    plt.xlabel("Date")
    plt.ylabel(column)
    plt.savefig(f"{title}.png")


result = finance_agent.run_sync(
    "Pull historical data for AAPL from 2020-01-01 to 2021-01-01",
    deps={"ticker": "AAPL", "start": "2020-01-01", "end": "2021-01-01"},
)

print(result)


# Base Agent Class
class BaseAgent:
"""Base class for all trading agents.
    
    This class serves as a foundation for specialized trading agents that implement
    different trading strategies. All trading agents should inherit from this class
    and implement the decide method."""
    """

    def __init__(self, name: str):
"""Initialize a new BaseAgent instance.
        
Args::
            name: A descriptive name for the agent."""
        """
        self.name = name

    def decide(self, market_data: dict) -> dict:
"""Make a decision based on market data.
        
Args::
            market_data: A dictionary containing market data such as prices,
                         indicators, and other relevant information.
                         
Returns::
            dict: A dictionary containing the decision details.
            
Raises::
            NotImplementedError: This method must be implemented by subclasses."""
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


# LongAgent
class LongAgent(BaseAgent):
"""Agent implementing a long-only trading strategy.
    
    This agent specializes in long positions, deciding when to buy (open) and
    sell (close) based on price relative to moving average."""
    """

    def decide(self, market_data: dict) -> dict:
"""Decide to buy to open or sell to close based on market data.
        
        Implements a simple strategy where:
        - Buy when price is above moving average
        - Sell when price is below moving average
        
Args::
            market_data: A dictionary containing at least 'price' and 'moving_average' keys.
            
Returns::
            dict: A decision dictionary with 'action' and 'reason' keys."""
        """
        # Example logic for long strategy
        if market_data["price"] > market_data["moving_average"]:
            return {
                "action": "buy_to_open",
                "reason": "Price above moving average",
            }
        return {
            "action": "sell_to_close",
            "reason": "Price below moving average",
        }


# ShortAgent
class ShortAgent(BaseAgent):
"""Agent implementing a short-selling trading strategy.
    
    This agent specializes in short positions, deciding when to sell (open) and
    buy (close) based on price relative to moving average."""
    """

    def decide(self, market_data: dict) -> dict:
"""Decide to sell to open or buy to close based on market data.
        
        Implements a simple strategy where:
        - Sell short when price is below moving average
        - Buy to cover when price is above moving average
        
Args::
            market_data: A dictionary containing at least 'price' and 'moving_average' keys.
            
Returns::
            dict: A decision dictionary with 'action' and 'reason' keys."""
        """
        # Example logic for short strategy
        if market_data["price"] < market_data["moving_average"]:
            return {
                "action": "sell_to_open",
                "reason": "Price below moving average",
            }
        return {
            "action": "buy_to_close",
            "reason": "Price above moving average",
        }


# ReportAgent
class ReportAgent(BaseAgent):
"""Agent responsible for generating trading reports.
    
    This agent specializes in creating formatted reports about trading activity,
    including positions, profit/loss, and data usage metrics."""
    """

    def generate_report(
        self, positions: List[dict], pnl: float, data_usage: int
    ) -> str:
"""Generate a daily trading activity report.
        
Args::
            positions: List of dictionaries, each representing an open position.
                       Each position should have at least 'ticker' and 'quantity' keys.
            pnl: The profit/loss amount for the period.
            data_usage: The amount of data used in MB.
            
Returns::
            str: A formatted report string containing the summary information."""
        """
        report = (
            "Daily Report:\n"
            f"Profit/Loss: {pnl}\n"
            f"Open Positions: {len(positions)}\n"
            f"Daily Data Usage: {data_usage} MB\n"
        )
        return report


# Example usage
if __name__ == "__main__":
    # Initialize agents
    long_agent = LongAgent("Long Strategy Agent")
    short_agent = ShortAgent("Short Strategy Agent")
    report_agent = ReportAgent("Report Generator Agent")

    # Example market data
    market_data = {"price": 150, "moving_average": 145}

    # Decisions
    long_decision = long_agent.decide(market_data)
    short_decision = short_agent.decide(market_data)

    # Example report
    positions = [{"ticker": "AAPL", "quantity": 10}]
    pnl = 500.0
    data_usage = 20
    report = report_agent.generate_report(positions, pnl, data_usage)

    print(long_decision)
    print(short_decision)
    print(report)
