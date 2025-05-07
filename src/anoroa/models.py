"""models.py module.

Description of the module functionality."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Period = Literal["1m", "5m", "15m", "30m", "1h", "1d", "1w"]


class Candle(BaseModel):
    """Represents a single candlestick in a financial chart."""

    period: Period
    symbol: str
    timestamp: datetime
    open_: float = Field(..., validation_alias="open", serialization_alias="open")
    close_: float = Field(..., validation_alias="close", serialization_alias="close")
    high: float
    low: float
    volume: Optional[float] = None


class TradeDirection(str):
    """Enum-like class for trade directions."""

    LONG = "long"
    SHORT = "short"


class Order(BaseModel):
    """Represents an order to be executed in the market."""

    symbol: str
    kind: Literal["limit", "stop", "market"]
    size: float
    duration: Literal["day", "good_till_cancelled"]
    price: float


class EntryDecision(BaseModel):
    """Represents a decision to enter a trade."""

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
    """Represents a decision to exit a trade."""

    action: Literal["sell_to_close", "buy_to_close"]
    symbol: str
    size: float
    reason: Literal["take_profit_hit", "stop_loss_hit", "manual_exit", "time_expired"]
    timestamp: datetime
    reasoning: Optional[str] = None


class OpenPosition(BaseModel):
    """Represents an open position in the market."""

    symbol: str
    size: float
    direction: Literal["long", "short"]
    entry_price: float
    entry_time: datetime


class TradeLog(BaseModel):
    """Represents a log of a trade, including entry and exit details."""

    symbol: str
    direction: Literal["long", "short"]
    entry_: EntryDecision = Field(validation_alias="entry")
    exit_: Optional[ExitDecision] = Field(None, validation_alias="exit")
    open_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
