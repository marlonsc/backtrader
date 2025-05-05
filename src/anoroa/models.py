from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

Period = Literal["1m", "5m", "15m", "30m", "1h", "1d", "1w"]


class Candle(BaseModel):
    """
    Represents a single candlestick in a financial chart.

    Attributes:
        period (Period): The time period of the candlestick (e.g., 1m, 5m).
        symbol (str): The financial instrument symbol (e.g., AAPL, BTCUSD).
        timestamp (datetime): The timestamp of the candlestick.
        open_ (float): The opening price of the candlestick.
        close_ (float): The closing price of the candlestick.
        high (float): The highest price during the candlestick period.
        low (float): The lowest price during the candlestick period.
        volume (Optional[float]): The trading volume during the candlestick period.
    """

    period: Period
    symbol: str
    timestamp: datetime
    open_: float = Field(..., validation_alias="open", serialization_alias="open")
    close_: float = Field(..., validation_alias="close", serialization_alias="close")
    high: float
    low: float
    volume: Optional[float] = None


class TradeDirection(str):
    """
    Enum-like class for trade directions.

    Attributes:
        LONG (str): Represents a long trade direction.
        SHORT (str): Represents a short trade direction.
    """

    LONG = "long"
    SHORT = "short"


class Order(BaseModel):
    """
    Represents an order to be executed in the market.

    Attributes:
        symbol (str): The financial instrument symbol.
        kind (Literal): The type of order (e.g., limit, stop, market).
        size (float): The number of shares/contracts to trade.
        duration (Literal): The duration of the order (e.g., day, good_till_cancelled).
        price (float): The price at which the order is to be executed.
    """

    symbol: str
    kind: Literal["limit", "stop", "market"]
    size: float
    duration: Literal["day", "good_till_cancelled"]
    price: float


class EntryDecision(BaseModel):
    """
    Represents a decision to enter a trade.

    Attributes:
        action (Literal): The action to take (e.g., buy_to_open, sell_to_open).
        symbol (str): The financial instrument symbol.
        size (float): The number of shares/contracts to trade.
        stop_loss (float): The stop loss price.
        take_profit (float): The take profit price.
        timestamp (datetime): The timestamp of the decision.
        reasoning (Optional[str]): The reasoning behind the decision.
    """

    action: Literal["buy_to_open", "sell_to_open"]
    symbol: str
    size: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    reasoning: Optional[str] = Field(
        description="Why did the agent make this decision?"
    )


class ExitDecision(BaseModel):
    """
    Represents a decision to exit a trade.

    Attributes:
        action (Literal): The action to take (e.g., sell_to_close, buy_to_close).
        symbol (str): The financial instrument symbol.
        size (float): The number of shares/contracts to trade.
        reason (Literal): The reason for exiting the trade.
        timestamp (datetime): The timestamp of the decision.
        reasoning (Optional[str]): Additional reasoning for the exit decision.
    """

    action: Literal["sell_to_close", "buy_to_close"]
    symbol: str
    size: float
    reason: Literal["take_profit_hit", "stop_loss_hit", "manual_exit", "time_expired"]
    timestamp: datetime
    reasoning: Optional[str] = None


class OpenPosition(BaseModel):
    """
    Represents an open position in the market.

    Attributes:
        symbol (str): The financial instrument symbol.
        size (float): The number of shares/contracts in the position.
        direction (Literal): The direction of the position (long or short).
        entry_price (float): The price at which the position was entered.
        entry_time (datetime): The timestamp of when the position was opened.
    """

    symbol: str
    size: float
    direction: Literal["long", "short"]
    entry_price: float
    entry_time: datetime


class TradeLog(BaseModel):
    """
    Represents a log of a trade, including entry and exit details.

    Attributes:
        symbol (str): The financial instrument symbol.
        direction (Literal): The direction of the trade (long or short).
        entry_ (EntryDecision): The entry decision details.
        exit_ (Optional[ExitDecision]): The exit decision details, if any.
        open_pnl (Optional[float]): The unrealized profit and loss.
        realized_pnl (Optional[float]): The realized profit and loss.
    """

    symbol: str
    direction: Literal["long", "short"]
    entry_: EntryDecision = Field(validation_alias="entry")
    exit_: Optional[ExitDecision] = Field(None, validation_alias="exit")
    open_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
