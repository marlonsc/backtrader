from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

Period = Literal["1m", "5m", "15m", "30m", "1h", "1d", "1w"]


class Candle(BaseModel):
    """Core data structure for anoroa"""
    period: Period
    symbol: str
    timestamp: datetime
    # use validation alias to avoid conflict with built-in open()
    open_: float = Field(..., validation_alias="open",
                         serialization_alias="open")
    # use validation alias to avoid conflict with built-in close()
    close_: float = Field(..., validation_alias="close",
                          serialization_alias="close")
    high: float
    low: float
    volume: Optional[float] = None  # e.g. shares traded, contracts traded


class TradeDirection(str):
    LONG = "long"
    SHORT = "short"


class Order(BaseModel):
    """Order to be executed in the market"""
    symbol: str
    kind: Literal["limit", "stop", "market"]
    size: float  # number of shares/contracts
    duration: Literal["day", "good_till_cancelled"]
    price: float  # absolute price


"""
based on what the Entry Decision spits out,
the agent will place an order
"""
class EntryDecision(BaseModel):
    """Decision to enter a trade"""

    # literals map to tools
    action: Literal["buy_to_open", "sell_to_open"]
    symbol: str
    size: float  # number of shares/contracts

    # These are dynamic. These are open limit orders
    # that will be filled when the market price reaches the limit price
    stop_loss: float  # absolute price
    take_profit: float  # absolute price
    timestamp: datetime
    reasoning: Optional[str] = Field(
        description="Why did the agent make this decision?"
    )


class ExitDecision(BaseModel):
    """Decision to exit a trade"""
    action: Literal["sell_to_close", "buy_to_close"]
    symbol: str
    size: float  # number of shares/contracts
    reason: Literal["take_profit_hit",
                    "stop_loss_hit", "manual_exit", "time_expired"]
    timestamp: datetime
    reasoning: Optional[str] = None


class Position(BaseModel):
    symbol: str
    size: float
    direction: Literal["long", "short"]
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    active: bool = True


class TradeLog(BaseModel):
    symbol: str
    direction: Literal["long", "short"]
    entry: EntryDecision
    exit: Optional[ExitDecision] = None
    pnl: Optional[float] = None  # populated after exit
