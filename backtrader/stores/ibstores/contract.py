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
"""Args::
    other:"""
""""""
""""""
""""""
"""Stock contract.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Option contract.

Args::
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    strike: The option's strike price. (Default value = 0.0)
    right: Put or call option.
    exchange: Destination exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Future contract.

Args::
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    exchange: Destination exchange. (Default value = "")
    localSymbol: The contract's symbol within its primary exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Continuous future contract.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    localSymbol: The contract's symbol within its primary exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Foreign exchange currency pair.

Args::
    pair: Shortcut for specifying symbol and currency, like 'EURUSD'. (Default value = "")
    exchange: Destination exchange. (Default value = "IDEALPRO")
    symbol: Base currency. (Default value = "")
    currency: Quote currency. (Default value = "")"""
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
""""""
        """Short name of pair.
:rtype: str"""
        return self.symbol + self.currency


class Index(Contract):
""""""
"""Index.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Contract For Difference.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
"""Commodity.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
        """Bond."""
        Contract.__init__(self, "BOND", **kwargs)


class FuturesOption(Contract):
""""""
"""Option on a futures contract.

Args::
    symbol: Symbol name. (Default value = "")
    lastTradeDateOrContractMonth: The option's last trading day
    strike: The option's strike price. (Default value = 0.0)
    right: Put or call option.
    exchange: Destination exchange. (Default value = "")
    multiplier: The contract multiplier. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
        """Mutual fund."""
        Contract.__init__(self, "FUND", **kwargs)


class Warrant(Contract):
""""""
        """Warrant option."""
        Contract.__init__(self, "WAR", **kwargs)


class Bag(Contract):
""""""
        """Bag contract."""
        Contract.__init__(self, "BAG", **kwargs)


class Crypto(Contract):
""""""
"""Crypto currency contract.

Args::
    symbol: Symbol name. (Default value = "")
    exchange: Destination exchange. (Default value = "")
    currency: Underlying currency. (Default value = "")"""
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
""""""
""""""
""""""
""""""
""""""
""":rtype: List[TradingSession]"""
        """
        return self._parseSessions(self.tradingHours)

    def liquidSessions(self) -> List[TradingSession]:
""":rtype: List[TradingSession]"""
        """
        return self._parseSessions(self.liquidHours)

    def _parseSessions(self, s: str) -> List[TradingSession]:
"""Args::
    s:"""
""""""
""""""

    rank: int
    contractDetails: ContractDetails
    distance: str
    benchmark: str
    projection: str
    legsStr: str
