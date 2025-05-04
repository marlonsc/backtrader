import yfinance as yf  # type: ignore
from typing import cast
import pandas as pd
import matplotlib.pyplot as plt
from pydantic_ai import Agent, RunContext

# Define the agent
finance_agent = Agent(
    'openai:gpt-4o',
    deps_type=dict,
    output_type=str,
    system_prompt=(
        'This agent provides tools for financial data analysis, including pulling historical data and plotting time series.'
    )
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
def pull_historical_data(ctx: RunContext[dict], ticker: str, start: str, end: str) -> pd.DataFrame:
    """Pull historical data for a given ticker and date range and save as a CSV file."""
    data = yf.download(ticker, start=start, end=end)
    data = cast(pd.DataFrame, data)
    fname = f"{ticker}_{start}_{end}.csv"
    data.to_csv(fname)

# Tool 2: Plot time series from a DataFrame


@finance_agent.tool
def plot_time_series(ctx: RunContext[dict], csv_file: str, column: str, title: str = "Time Series Plot") -> None:
    """Plot a time series from a csv file."""
    data = pd.read_csv(csv_file)
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    data[column].plot(title=title)
    plt.xlabel("Date")
    plt.ylabel(column)
    plt.savefig(f"{title}.png")


result = finance_agent.run_sync(
    'Pull historical data for AAPL from 2020-01-01 to 2021-01-01',
    deps={'ticker': 'AAPL', 'start': '2020-01-01', 'end': '2021-01-01'}
)

print(result)



# result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
# print(result.output)
# #> True

# result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
