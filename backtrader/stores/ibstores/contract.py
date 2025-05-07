"""Financial instrument types used by Interactive Brokers."""

import datetime as dt
from dataclasses import dataclass, field
from typing import List, NamedTuple, Optional

import ib_insync.util as util


@dataclass
class Contract:
    """``Contract(**kwargs)`` can create any contract using keyword
arguments. To simplify working with contracts, there are also more
specialized contracts that take optional positional arguments.
Some examples::
Contract(conId=270639)
Stock('AMD', 'SMART', 'USD')
Stock('INTC', 'SMART', 'USD', primaryExchange='NASDAQ')
Forex('EURUSD')
CFD('IBUS30')
Future('ES', '20180921', 'GLOBEX')
Option('SPY', '20170721', 240, 'C', 'SMART')
Bond(secIdType='ISIN', secId='US03076KAA60')
Crypto('BTC', 'PAXOS', 'USD')"""

    secType: str = ""
    conId: int = 0
    symbol: str = ""
    lastTradeDateOrContractMonth: str = ""
    strike: float = 0.0
    right: str = ""
    multiplier: str = ""
    exchange: str = ""
    primaryExchange: str = ""
    currency: str = ""
    localSymbol: str = ""
    tradingClass: str = ""
    includeExpired: bool = False
    secIdType: str = ""
    secId: str = ""
    description: str = ""
    issuerId: str = ""
    comboLegsDescrip: str = ""
    comboLegs: List["ComboLeg"] = field(default_factory=list)
    deltaNeutralContract: Optional["DeltaNeutralContract"] = None

    @staticmethod
    def create(**kwargs) -> "Contract":
        """Create and a return a specialized contract based on the given secType,
or a general Contract if secType is not given."""
        secType = kwargs.get("secType", "")
        cls = {
            "": Contract,
            "STK": Stock,
            "OPT": Option,
            "FUT": Future,
            "CONTFUT": ContFuture,
            "CASH": Forex,
            "IND": Index,
            "CFD": CFD,
            "BOND": Bond,
            "CMDTY": Commodity,
            "FOP": FuturesOption,
            "FUND": MutualFund,
            "WAR": Warrant,
            "IOPT": Warrant,
            "BAG": Bag,
            "CRYPTO": Crypto,
            "NEWS": Contract,
            "EVENT": Contract,
        }.get(secType, Contract)
        if cls is not Contract:
            kwargs.pop("secType", "")
        return cls(**kwargs)

    def isHashable(self) -> bool:
        """See if this contract can be hashed by conId.
Note: Bag contracts always get conId=28812380, so they're not hashable.
:rtype: bool"""
        return bool(self.conId and self.conId != 28812380 and self.secType != "BAG")

    def __eq__(self, other):
        """Args:
    other:"""
        return isinstance(other, Contract) and (
            self.conId
            and self.conId == other.conId
            or util.dataclassAsDict(self) == util.dataclassAsDict(other)
        )

    def __hash__(self):
        """ """
        if not self.isHashable():
            raise ValueError(f"Contract {self} can't be hashed")
        if self.secType == "CONTFUT":
            # CONTFUT gets the same conId as the front contract, invert it here
            h = -self.conId
        else:
            h = self.conId
        return h

    def __repr__(self):
        """ """
        attrs = util.dataclassNonDefaults(self)
        if self.__class__ is not Contract:
            attrs.pop("secType", "")
        clsName = self.__class__.__qualname__
        kwargs = ", ".join(f"{k}={v!r}" for k, v in attrs.items())
        return f"{clsName}({kwargs})"

    __str__ = __repr__


class Stock(Contract):
    """ """

    def __init__(
        self, symbol: str = "", exchange: str = "", currency: str = "", **kwargs
    ):
        """Stock contract.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            secType="STK",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )


class Option(Contract):
    """ """

    def __init__(
        self,
        symbol: str = "",
        lastTradeDateOrContractMonth: str = "",
        strike: float = 0.0,
        right: str = "",
        exchange: str = "",
        multiplier: str = "",
        currency: str = "",
        **kwargs,
    ):
        """Option contract.

Args:
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    strike: The option's strike price. (Default value = 0.0)
    right: Put or call option.
    exchange: Destination exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "OPT",
            symbol=symbol,
            lastTradeDateOrContractMonth=lastTradeDateOrContractMonth,
            strike=strike,
            right=right,
            exchange=exchange,
            multiplier=multiplier,
            currency=currency,
            **kwargs,
        )


class Future(Contract):
    """ """

    def __init__(
        self,
        symbol: str = "",
        lastTradeDateOrContractMonth: str = "",
        exchange: str = "",
        localSymbol: str = "",
        multiplier: str = "",
        currency: str = "",
        **kwargs,
    ):
        """Future contract.

Args:
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    exchange: Destination exchange. (Default value = "")
    localSymbol: The contract's symbol within its primary exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "FUT",
            symbol=symbol,
            lastTradeDateOrContractMonth=lastTradeDateOrContractMonth,
            exchange=exchange,
            localSymbol=localSymbol,
            multiplier=multiplier,
            currency=currency,
            **kwargs,
        )


class ContFuture(Contract):
    """ """

    def __init__(
        self,
        symbol: str = "",
        exchange: str = "",
        localSymbol: str = "",
        multiplier: str = "",
        currency: str = "",
        **kwargs,
    ):
        """Continuous future contract.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    localSymbol: The contract's symbol within its primary exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "CONTFUT",
            symbol=symbol,
            exchange=exchange,
            localSymbol=localSymbol,
            multiplier=multiplier,
            currency=currency,
            **kwargs,
        )


class Forex(Contract):
    """ """

    def __init__(
        self,
        pair: str = "",
        exchange: str = "IDEALPRO",
        symbol: str = "",
        currency: str = "",
        **kwargs,
    ):
        """Foreign exchange currency pair.

Args:
    pair: Shortcut for specifying symbol and currency, like 'EURUSD'. (Default value = "")
    exchange: Destination exchange. (Default value = "IDEALPRO")
    symbol: Base currency. (Default value = "")
    currency: Quote currency. (Default value = "")"""
        if pair:
            assert len(pair) == 6
            symbol = symbol or pair[:3]
            currency = currency or pair[3:]
        Contract.__init__(
            self,
            "CASH",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )

    def __repr__(self):
        """ """
        attrs = util.dataclassNonDefaults(self)
        attrs.pop("secType")
        s = "Forex("
        if "symbol" in attrs and "currency" in attrs:
            pair = attrs.pop("symbol")
            pair += attrs.pop("currency")
            s += "'" + pair + "'" + (", " if attrs else "")
        s += ", ".join(f"{k}={v!r}" for k, v in attrs.items())
        s += ")"
        return s

    __str__ = __repr__

    def pair(self) -> str:
        """Short name of pair.
:rtype: str"""
        return self.symbol + self.currency


class Index(Contract):
    """ """

    def __init__(
        self, symbol: str = "", exchange: str = "", currency: str = "", **kwargs
    ):
        """Index.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "IND",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )


class CFD(Contract):
    """ """

    def __init__(
        self, symbol: str = "", exchange: str = "", currency: str = "", **kwargs
    ):
        """Contract For Difference.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "CFD",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )


class Commodity(Contract):
    """ """

    def __init__(
        self, symbol: str = "", exchange: str = "", currency: str = "", **kwargs
    ):
        """Commodity.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "CMDTY",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )


class Bond(Contract):
    """ """

    def __init__(self, **kwargs):
        """Bond."""
        Contract.__init__(self, "BOND", **kwargs)


class FuturesOption(Contract):
    """ """

    def __init__(
        self,
        symbol: str = "",
        lastTradeDateOrContractMonth: str = "",
        strike: float = 0.0,
        right: str = "",
        exchange: str = "",
        multiplier: str = "",
        currency: str = "",
        **kwargs,
    ):
        """Option on a futures contract.

Args:
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    strike: The option's strike price. (Default value = 0.0)
    right: Put or call option.
    exchange: Destination exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            "FOP",
            symbol=symbol,
            lastTradeDateOrContractMonth=lastTradeDateOrContractMonth,
            strike=strike,
            right=right,
            exchange=exchange,
            multiplier=multiplier,
            currency=currency,
            **kwargs,
        )


class MutualFund(Contract):
    """ """

    def __init__(self, **kwargs):
        """Mutual fund."""
        Contract.__init__(self, "FUND", **kwargs)


class Warrant(Contract):
    """ """

    def __init__(self, **kwargs):
        """Warrant option."""
        Contract.__init__(self, "WAR", **kwargs)


class Bag(Contract):
    """ """

    def __init__(self, **kwargs):
        """Bag contract."""
        Contract.__init__(self, "BAG", **kwargs)


class Crypto(Contract):
    """ """

    def __init__(
        self, symbol: str = "", exchange: str = "", currency: str = "", **kwargs
    ):
        """Crypto currency contract.

Args:
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
        Contract.__init__(
            self,
            secType="CRYPTO",
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            **kwargs,
        )


class TagValue(NamedTuple):
    """ """

    tag: str
    value: str


@dataclass
class ComboLeg:
    """ """

    conId: int = 0
    ratio: int = 0
    action: str = ""
    exchange: str = ""
    openClose: int = 0
    shortSaleSlot: int = 0
    designatedLocation: str = ""
    exemptCode: int = -1


@dataclass
class DeltaNeutralContract:
    """ """

    conId: int = 0
    delta: float = 0.0
    price: float = 0.0


class TradingSession(NamedTuple):
    """ """

    start: dt.datetime
    end: dt.datetime


@dataclass
class ContractDetails:
    """ """

    contract: Optional[Contract] = None
    marketName: str = ""
    minTick: float = 0.0
    orderTypes: str = ""
    validExchanges: str = ""
    priceMagnifier: int = 0
    underConId: int = 0
    longName: str = ""
    contractMonth: str = ""
    industry: str = ""
    category: str = ""
    subcategory: str = ""
    timeZoneId: str = ""
    tradingHours: str = ""
    liquidHours: str = ""
    evRule: str = ""
    evMultiplier: int = 0
    mdSizeMultiplier: int = 1  # obsolete
    aggGroup: int = 0
    underSymbol: str = ""
    underSecType: str = ""
    marketRuleIds: str = ""
    secIdList: List[TagValue] = field(default_factory=list)
    realExpirationDate: str = ""
    lastTradeTime: str = ""
    stockType: str = ""
    minSize: float = 0.0
    sizeIncrement: float = 0.0
    suggestedSizeIncrement: float = 0.0
    # minCashQtySize: float = 0.0
    cusip: str = ""
    ratings: str = ""
    descAppend: str = ""
    bondType: str = ""
    couponType: str = ""
    callable: bool = False
    putable: bool = False
    coupon: float = 0
    convertible: bool = False
    maturity: str = ""
    issueDate: str = ""
    nextOptionDate: str = ""
    nextOptionType: str = ""
    nextOptionPartial: bool = False
    notes: str = ""

    def tradingSessions(self) -> List[TradingSession]:
        """


        :rtype: List[TradingSession]

        """
        return self._parseSessions(self.tradingHours)

    def liquidSessions(self) -> List[TradingSession]:
        """


        :rtype: List[TradingSession]

        """
        return self._parseSessions(self.liquidHours)

    def _parseSessions(self, s: str) -> List[TradingSession]:
        """Args:
    s:"""
        tz = util.ZoneInfo(self.timeZoneId)
        sessions = []
        for sess in s.split(";"):
            if not sess or "CLOSED" in sess:
                continue
            sessions.append(
                TradingSession(
                    *[
                        dt.datetime.strptime(t, "%Y%m%d:%H%M").replace(tzinfo=tz)
                        for t in sess.split("-")
                    ]
                )
            )
        return sessions


@dataclass
class ContractDescription:
    """ """

    contract: Optional[Contract] = None
    derivativeSecTypes: List[str] = field(default_factory=list)


@dataclass
class ScanData:
    """ """

    rank: int
    contractDetails: ContractDetails
    distance: str
    benchmark: str
    projection: str
    legsStr: str
