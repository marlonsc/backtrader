"""Order types used by Interactive Brokers."""

from dataclasses import dataclass, field
from typing import ClassVar, FrozenSet, List, NamedTuple

from eventkit import Event

from .contract import Contract, TagValue
from .objects import Fill, SoftDollarTier, TradeLogEntry
from .util import UNSET_DOUBLE, UNSET_INTEGER, dataclassNonDefaults


@dataclass
class Order:
    """Order for trading contracts.
https://interactivebrokers.github.io/tws-api/available_orders.html"""

    orderId: int = 0
    clientId: int = 0
    permId: int = 0
    action: str = ""
    totalQuantity: float = 0.0
    orderType: str = ""
    lmtPrice: float = UNSET_DOUBLE
    auxPrice: float = UNSET_DOUBLE
    tif: str = ""
    activeStartTime: str = ""
    activeStopTime: str = ""
    ocaGroup: str = ""
    ocaType: int = 0
    orderRef: str = ""
    transmit: bool = True
    parentId: int = 0
    blockOrder: bool = False
    sweepToFill: bool = False
    displaySize: int = 0
    triggerMethod: int = 0
    outsideRth: bool = False
    hidden: bool = False
    goodAfterTime: str = ""
    goodTillDate: str = ""
    rule80A: str = ""
    allOrNone: bool = False
    minQty: int = UNSET_INTEGER
    percentOffset: float = UNSET_DOUBLE
    overridePercentageConstraints: bool = False
    trailStopPrice: float = UNSET_DOUBLE
    trailingPercent: float = UNSET_DOUBLE
    faGroup: str = ""
    faProfile: str = ""
    faMethod: str = ""
    faPercentage: str = ""
    designatedLocation: str = ""
    openClose: str = "O"
    origin: int = 0
    shortSaleSlot: int = 0
    exemptCode: int = -1
    discretionaryAmt: float = 0.0
    eTradeOnly: bool = False
    firmQuoteOnly: bool = False
    nbboPriceCap: float = UNSET_DOUBLE
    optOutSmartRouting: bool = False
    auctionStrategy: int = 0
    startingPrice: float = UNSET_DOUBLE
    stockRefPrice: float = UNSET_DOUBLE
    delta: float = UNSET_DOUBLE
    stockRangeLower: float = UNSET_DOUBLE
    stockRangeUpper: float = UNSET_DOUBLE
    randomizePrice: bool = False
    randomizeSize: bool = False
    volatility: float = UNSET_DOUBLE
    volatilityType: int = UNSET_INTEGER
    deltaNeutralOrderType: str = ""
    deltaNeutralAuxPrice: float = UNSET_DOUBLE
    deltaNeutralConId: int = 0
    deltaNeutralSettlingFirm: str = ""
    deltaNeutralClearingAccount: str = ""
    deltaNeutralClearingIntent: str = ""
    deltaNeutralOpenClose: str = ""
    deltaNeutralShortSale: bool = False
    deltaNeutralShortSaleSlot: int = 0
    deltaNeutralDesignatedLocation: str = ""
    continuousUpdate: bool = False
    referencePriceType: int = UNSET_INTEGER
    basisPoints: float = UNSET_DOUBLE
    basisPointsType: int = UNSET_INTEGER
    scaleInitLevelSize: int = UNSET_INTEGER
    scaleSubsLevelSize: int = UNSET_INTEGER
    scalePriceIncrement: float = UNSET_DOUBLE
    scalePriceAdjustValue: float = UNSET_DOUBLE
    scalePriceAdjustInterval: int = UNSET_INTEGER
    scaleProfitOffset: float = UNSET_DOUBLE
    scaleAutoReset: bool = False
    scaleInitPosition: int = UNSET_INTEGER
    scaleInitFillQty: int = UNSET_INTEGER
    scaleRandomPercent: bool = False
    scaleTable: str = ""
    hedgeType: str = ""
    hedgeParam: str = ""
    account: str = ""
    settlingFirm: str = ""
    clearingAccount: str = ""
    clearingIntent: str = ""
    algoStrategy: str = ""
    algoParams: List[TagValue] = field(default_factory=list)
    smartComboRoutingParams: List[TagValue] = field(default_factory=list)
    algoId: str = ""
    whatIf: bool = False
    notHeld: bool = False
    solicited: bool = False
    modelCode: str = ""
    orderComboLegs: List["OrderComboLeg"] = field(default_factory=list)
    orderMiscOptions: List[TagValue] = field(default_factory=list)
    referenceContractId: int = 0
    peggedChangeAmount: float = 0.0
    isPeggedChangeAmountDecrease: bool = False
    referenceChangeAmount: float = 0.0
    referenceExchangeId: str = ""
    adjustedOrderType: str = ""
    triggerPrice: float = UNSET_DOUBLE
    adjustedStopPrice: float = UNSET_DOUBLE
    adjustedStopLimitPrice: float = UNSET_DOUBLE
    adjustedTrailingAmount: float = UNSET_DOUBLE
    adjustableTrailingUnit: int = 0
    lmtPriceOffset: float = UNSET_DOUBLE
    conditions: List["OrderCondition"] = field(default_factory=list)
    conditionsCancelOrder: bool = False
    conditionsIgnoreRth: bool = False
    extOperator: str = ""
    softDollarTier: SoftDollarTier = field(default_factory=SoftDollarTier)
    cashQty: float = UNSET_DOUBLE
    mifid2DecisionMaker: str = ""
    mifid2DecisionAlgo: str = ""
    mifid2ExecutionTrader: str = ""
    mifid2ExecutionAlgo: str = ""
    dontUseAutoPriceForHedge: bool = False
    isOmsContainer: bool = False
    discretionaryUpToLimitPrice: bool = False
    autoCancelDate: str = ""
    filledQuantity: float = UNSET_DOUBLE
    refFuturesConId: int = 0
    autoCancelParent: bool = False
    shareholder: str = ""
    imbalanceOnly: bool = False
    routeMarketableToBbo: bool = False
    parentPermId: int = 0
    usePriceMgmtAlgo: bool = False
    duration: int = UNSET_INTEGER
    postToAts: int = UNSET_INTEGER
    advancedErrorOverride: str = ""
    manualOrderTime: str = ""
    minTradeQty: int = UNSET_INTEGER
    minCompeteSize: int = UNSET_INTEGER
    competeAgainstBestOffset: float = UNSET_DOUBLE
    midOffsetAtWhole: float = UNSET_DOUBLE
    midOffsetAtHalf: float = UNSET_DOUBLE

    def __repr__(self):
""""""
"""Args::
    other:"""
""""""
""""""
"""Args::
    action: 
    totalQuantity: 
    lmtPrice:"""
    lmtPrice:"""
        Order.__init__(
            self,
            orderType="LMT",
            action=action,
            totalQuantity=totalQuantity,
            lmtPrice=lmtPrice,
            **kwargs,
        )


class MarketOrder(Order):
""""""
"""Args::
    action: 
    totalQuantity:"""
    totalQuantity:"""
        Order.__init__(
            self,
            orderType="MKT",
            action=action,
            totalQuantity=totalQuantity,
            **kwargs,
        )


class StopOrder(Order):
""""""
"""Args::
    action: 
    totalQuantity: 
    stopPrice:"""
    stopPrice:"""
        Order.__init__(
            self,
            orderType="STP",
            action=action,
            totalQuantity=totalQuantity,
            auxPrice=stopPrice,
            **kwargs,
        )


class StopLimitOrder(Order):
""""""
"""Args::
    action: 
    totalQuantity: 
    lmtPrice: 
    stopPrice:"""
    stopPrice:"""
        Order.__init__(
            self,
            orderType="STP LMT",
            action=action,
            totalQuantity=totalQuantity,
            lmtPrice=lmtPrice,
            auxPrice=stopPrice,
            **kwargs,
        )


@dataclass
class OrderStatus:
""""""
""""""
""""""
    """Trade keeps track of an order, its status and all its fills.
Events:
* ``statusEvent`` (trade: :class:`.Trade`)
* ``modifyEvent`` (trade: :class:`.Trade`)
* ``fillEvent`` (trade: :class:`.Trade`, fill: :class:`.Fill`)
* ``commissionReportEvent`` (trade: :class:`.Trade`,
fill: :class:`.Fill`, commissionReport: :class:`.CommissionReport`)
* ``filledEvent`` (trade: :class:`.Trade`)
* ``cancelEvent`` (trade: :class:`.Trade`)
* ``cancelledEvent`` (trade: :class:`.Trade`)"""

    contract: Contract = field(default_factory=Contract)
    order: Order = field(default_factory=Order)
    orderStatus: "OrderStatus" = field(default_factory=OrderStatus)
    fills: List[Fill] = field(default_factory=list)
    log: List[TradeLogEntry] = field(default_factory=list)
    advancedError: str = ""

    events: ClassVar = (
        "statusEvent",
        "modifyEvent",
        "fillEvent",
        "commissionReportEvent",
        "filledEvent",
        "cancelEvent",
        "cancelledEvent",
    )

    def __post_init__(self):
""""""
        """True if eligible for execution, false otherwise.
:rtype: bool"""
        return self.orderStatus.status in OrderStatus.ActiveStates

    def isDone(self) -> bool:
        """True if completely filled or cancelled, false otherwise.
:rtype: bool"""
        return self.orderStatus.status in OrderStatus.DoneStates

    def filled(self) -> float:
        """Number of shares filled.
:rtype: float"""
        fills = self.fills
        if self.contract.secType == "BAG":
            # don't count fills for the leg contracts
            fills = [f for f in fills if f.contract.secType == "BAG"]
        return sum(f.execution.shares for f in fills)

    def remaining(self) -> float:
        """Number of shares remaining to be filled.
:rtype: float"""
        return self.order.totalQuantity - self.filled()


class BracketOrder(NamedTuple):
""""""
""""""
"""Args::
    condType:"""
""""""
""""""
""""""
""""""
""""""
""""""
""""""
""""""

    condType: int = 7
    conjunction: str = "a"
    isMore: bool = True
    changePercent: float = 0.0
    conId: int = 0
    exch: str = ""
