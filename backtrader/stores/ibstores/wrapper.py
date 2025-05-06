"""Wrapper to handle incoming messages."""

import asyncio
import logging
from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timezone
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from ib_insync.contract import (
    Contract,
    ContractDescription,
    ContractDetails,
    DeltaNeutralContract,
    ScanData,
)
from ib_insync.objects import (
    AccountValue,
    BarData,
    BarDataList,
    CommissionReport,
    DepthMktDataDescription,
    Dividends,
    DOMLevel,
    Execution,
    FamilyCode,
    Fill,
    FundamentalRatios,
    HistogramData,
    HistoricalNews,
    HistoricalSchedule,
    HistoricalSession,
    HistoricalTick,
    HistoricalTickBidAsk,
    HistoricalTickLast,
    MktDepthData,
    NewsArticle,
    NewsBulletin,
    NewsProvider,
    NewsTick,
    OptionChain,
    OptionComputation,
    PnL,
    PnLSingle,
    PortfolioItem,
    Position,
    PriceIncrement,
    RealTimeBar,
    RealTimeBarList,
    SoftDollarTier,
    TickAttribBidAsk,
    TickAttribLast,
    TickByTickAllLast,
    TickByTickBidAsk,
    TickByTickMidPoint,
    TickData,
    TradeLogEntry,
)
from ib_insync.order import Order, OrderState, OrderStatus, Trade
from ib_insync.ticker import Ticker
from ib_insync.util import (
    UNSET_DOUBLE,
    UNSET_INTEGER,
    dataclassAsDict,
    dataclassUpdate,
    getLoop,
    globalErrorEvent,
    isNan,
    parseIBDatetime,
)

if TYPE_CHECKING:
    from ..ibstore_insync import IBStoreInsync

OrderKeyType = Union[int, Tuple[int, int]]


class RequestError(Exception):
""":raises a: single request"""
    """

    def __init__(self, reqId: int, code: int, message: str):
"""Args::
    reqId: Original request ID.
    code: Original error code.
    message: Original error message."""
    message: Original error message."""
        super().__init__(f"API error: {code}: {message}")
        self.reqId = reqId
        self.code = code
        self.message = message


class Wrapper:
    """Wrapper implementation for use with the IB class."""

    ib: "IBStoreInsync"

    accountValues: Dict[tuple, AccountValue]
    """ (account, tag, currency, modelCode) -> AccountValue """

    acctSummary: Dict[tuple, AccountValue]
    """ (account, tag, currency) -> AccountValue """

    portfolio: Dict[str, Dict[int, PortfolioItem]]
    """ account -> conId -> PortfolioItem """

    positions: Dict[str, Dict[int, Position]]
    """ account -> conId -> Position """

    trades: Dict[OrderKeyType, Trade]
    """ (client, orderId) or permId -> Trade """

    permId2Trade: Dict[int, Trade]
    """ permId -> Trade """

    fills: Dict[str, Fill]
    """ execId -> Fill """

    newsTicks: List[NewsTick]

    msgId2NewsBulletin: Dict[int, NewsBulletin]
    """ msgId -> NewsBulletin """

    tickers: Dict[int, Ticker]
    """ id(Contract) -> Ticker """

    pendingTickers: Set[Ticker]

    reqId2Ticker: Dict[int, Ticker]
    """ reqId -> Ticker """

    ticker2ReqId: Dict[Union[int, str], Dict[Ticker, int]]
    """ tickType -> Ticker -> reqId """

    reqId2Subscriber: Dict[int, Any]
    """ live bars or live scan data """

    reqId2PnL: Dict[int, PnL]
    """ reqId -> PnL """

    reqId2PnlSingle: Dict[int, PnLSingle]
    """ reqId -> PnLSingle """

    pnlKey2ReqId: Dict[tuple, int]
    """ (account, modelCode) -> reqId """

    pnlSingleKey2ReqId: Dict[tuple, int]
    """ (account, modelCode, conId) -> reqId """

    lastTime: datetime
    """ UTC time of last network packet arrival. """

    accounts: List[str]
    clientId: int
    wshMetaReqId: int
    wshEventReqId: int
    _reqId2Contract: Dict[int, Contract]
    _timeout: float

    _futures: Dict[Any, asyncio.Future]
    """ _futures and _results are linked by key. """

    _results: Dict[Any, Any]
    """ _futures and _results are linked by key. """

    _logger: logging.Logger
    _timeoutHandle: Union[asyncio.TimerHandle, None]

    def __init__(self, ib):
"""Args::
    ib:"""
""""""
        """Set all subscription-type events as done."""
        events = [ticker.updateEvent for ticker in self.tickers.values()]
        events += [sub.updateEvent for sub in self.reqId2Subscriber.values()]
        for trade in self.trades.values():
            events += [
                trade.statusEvent,
                trade.modifyEvent,
                trade.fillEvent,
                trade.filledEvent,
                trade.commissionReportEvent,
                trade.cancelEvent,
                trade.cancelledEvent,
            ]
        for event in events:
            event.set_done()

    def connectionClosed(self):
""""""
"""Start a new request and return the future that is associated
with the key and container. The container is a list by default.

Args::
    key: 
    contract: (Default value = None)
    container: (Default value = None)"""
    container: (Default value = None)"""
        future: asyncio.Future = asyncio.Future()
        self._futures[key] = future
        self._results[key] = container if container is not None else []
        if contract:
            self._reqId2Contract[key] = contract
        return future

    def _endReq(self, key, result=None, success=True):
"""Finish the future of corresponding key with the given result.
If no result is given then it will be popped of the general results.

Args::
    key: 
    result: (Default value = None)
    success: (Default value = True)"""
    success: (Default value = True)"""
        future = self._futures.pop(key, None)
        self._reqId2Contract.pop(key, None)
        if future:
            if result is None:
                result = self._results.pop(key, [])
            if not future.done():
                if success:
                    future.set_result(result)
                else:
                    future.set_exception(result)

    def startTicker(self, reqId: int, contract: Contract, tickType: Union[int, str]):
"""Start a tick request that has the reqId associated with the contract.

Args::
    reqId: 
    contract: 
    tickType:"""
    tickType:"""
        ticker = self.tickers.get(id(contract))
        if not ticker:
            ticker = Ticker(
                contract=contract,
                ticks=[],
                tickByTicks=[],
                domBids=[],
                domAsks=[],
                domTicks=[],
            )
            self.tickers[id(contract)] = ticker
        self.reqId2Ticker[reqId] = ticker
        self._reqId2Contract[reqId] = contract
        self.ticker2ReqId[tickType][ticker] = reqId
        return ticker

    def endTicker(self, ticker: Ticker, tickType: Union[int, str]):
"""Args::
    ticker: 
    tickType:"""
    tickType:"""
        reqId = self.ticker2ReqId[tickType].pop(ticker, 0)
        self._reqId2Contract.pop(reqId, None)
        return reqId

    def startSubscription(self, reqId, subscriber, contract=None):
"""Register a live subscription.

Args::
    reqId: 
    subscriber: 
    contract: (Default value = None)"""
    contract: (Default value = None)"""
        self._reqId2Contract[reqId] = contract
        self.reqId2Subscriber[reqId] = subscriber

    def endSubscription(self, subscriber):
"""Unregister a live subscription.

Args::
    subscriber:"""
    subscriber:"""
        self._reqId2Contract.pop(subscriber.reqId, None)
        self.reqId2Subscriber.pop(subscriber.reqId, None)

    def orderKey(self, clientId: int, orderId: int, permId: int) -> OrderKeyType:
"""Args::
    clientId: 
    orderId: 
    permId:"""
    permId:"""
        key: OrderKeyType
        if orderId <= 0:
            # order is placed manually from TWS
            key = permId
        else:
            key = (clientId, orderId)
        return key

    def setTimeout(self, timeout: float):
"""Args::
    timeout:"""
"""Args::
    delay: (Default value = 0)"""
""""""
"""Receives next valid order id.

Args::
    reqId:"""
    reqId:"""
        print(f"nextValidId: {reqId}")
        self.ib.nextValidId(reqId)

    def managedAccounts(self, accountsList: str):
"""Args::
    accountsList:"""
"""Args::
    timestamp:"""
"""Args::
    tag: 
    val: 
    currency: 
    account:"""
    account:"""
        key = (account, tag, currency, "")
        acctVal = AccountValue(account, tag, val, currency, "")
        self.accountValues[key] = acctVal
        self.ib.accountValueEvent.emit(tag, val, currency, account)
        # print("UpdateAccountValue. Key:", key, "acctVal:", acctVal)

    def accountDownloadEnd(self, _account: str):
"""Args::
    _account:"""
"""Args::
    reqId: 
    account: 
    modelCode: 
    tag: 
    val: 
    currency:"""
    currency:"""
        key = (account, tag, currency, modelCode)
        acctVal = AccountValue(account, tag, val, currency, modelCode)
        self.accountValues[key] = acctVal
        self.ib.accountValueEvent.emit(tag, val, currency, account)

    def accountUpdateMultiEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    _reqId: 
    account: 
    tag: 
    value: 
    currency:"""
    currency:"""
        key = (account, tag, currency)
        acctVal = AccountValue(account, tag, value, currency, "")
        self.acctSummary[key] = acctVal
        self.ib.accountSummaryEvent.emit(acctVal)

    def accountSummaryEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    contract: 
    posSize: 
    marketPrice: 
    marketValue: 
    averageCost: 
    unrealizedPNL: 
    realizedPNL: 
    account:"""
    account:"""
        contract = Contract.create(**dataclassAsDict(contract))
        portfItem = PortfolioItem(
            contract,
            posSize,
            marketPrice,
            marketValue,
            averageCost,
            unrealizedPNL,
            realizedPNL,
            account,
        )
        portfolioItems = self.portfolio[account]
        if posSize == 0:
            portfolioItems.pop(contract.conId, None)
        else:
            portfolioItems[contract.conId] = portfItem
        self._logger.info(f"updatePortfolio: {portfItem}")
        self.ib.updatePortfolioEvent.emit(portfItem)
        # self.ib.updatePortfolio(contract, posSize, marketPrice, marketValue,
        #                        averageCost, unrealizedPNL, realizedPNL, account)
        # print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType,
        #      "Exchange:",contract.exchange, "Position:", "AccountName:", account)

    def position(
        self, account: str, contract: Contract, posSize: float, avgCost: float
    ):
"""Args::
    account: 
    contract: 
    posSize: 
    avgCost:"""
    avgCost:"""
        contract = Contract.create(**dataclassAsDict(contract))
        position = Position(account, contract, posSize, avgCost)
        positions = self.positions[account]
        if posSize == 0:
            positions.pop(contract.conId, None)
        else:
            positions[contract.conId] = position
        self._logger.info(f"position: {position}")
        results = self._results.get("positions")
        if results is not None:
            results.append(position)
        self.ib.positionEvent.emit(position)
        print(
            f"Position[{account}], "
            f"Assert:{contract.symbol}, "
            f"Contract:{contract.conId}, "
            f"Position:{position}, "
            f"Avg cost:{avgCost}"
        )

    def positionEnd(self):
""""""
"""Args::
    reqId: 
    account: 
    modelCode: 
    contract: 
    pos: 
    avgCost:"""
    avgCost:"""

    def positionMultiEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    dailyPnL: 
    unrealizedPnL: 
    realizedPnL:"""
    realizedPnL:"""
        pnl = self.reqId2PnL.get(reqId)
        if not pnl:
            return
        pnl.dailyPnL = dailyPnL
        pnl.unrealizedPnL = unrealizedPnL
        pnl.realizedPnL = realizedPnL
        self.ib.pnlEvent.emit(pnl)

    def pnlSingle(
        self,
        reqId: int,
        pos: int,
        dailyPnL: float,
        unrealizedPnL: float,
        realizedPnL: float,
        value: float,
    ):
"""Args::
    reqId: 
    pos: 
    dailyPnL: 
    unrealizedPnL: 
    realizedPnL: 
    value:"""
    value:"""
        pnlSingle = self.reqId2PnlSingle.get(reqId)
        if not pnlSingle:
            return
        pnlSingle.position = pos
        pnlSingle.dailyPnL = dailyPnL
        pnlSingle.unrealizedPnL = unrealizedPnL
        pnlSingle.realizedPnL = realizedPnL
        pnlSingle.value = value
        self.ib.pnlSingleEvent.emit(pnlSingle)

    def openOrder(
        self,
        orderId: int,
        contract: Contract,
        order: Order,
        orderState: OrderState,
    ):
"""This wrapper is called to:
* feed in open orders at startup;
* feed in open orders or order updates from other clients and TWS
if clientId=master id;
* feed in manual orders and order updates from TWS if clientId=0;
* handle openOrders and allOpenOrders responses.

Args::
    orderId: 
    contract: 
    order: 
    orderState:"""
    orderState:"""
        if order.whatIf:
            # response to whatIfOrder
            if orderState.initMarginChange != str(UNSET_DOUBLE):
                self._endReq(order.orderId, orderState)
        else:
            key = self.orderKey(order.clientId, order.orderId, order.permId)
            trade = self.trades.get(key)
            if trade:
                trade.order.permId = order.permId
                trade.order.totalQuantity = order.totalQuantity
                trade.order.lmtPrice = order.lmtPrice
                trade.order.auxPrice = order.auxPrice
                trade.order.orderType = order.orderType
                trade.order.orderRef = order.orderRef
            else:
                # ignore '?' values in the order
                order = Order(
                    **{k: v for k, v in dataclassAsDict(order).items() if v != "?"}
                )
                contract = Contract.create(**dataclassAsDict(contract))
                orderStatus = OrderStatus(orderId=orderId, status=orderState.status)
                trade = Trade(contract, order, orderStatus, [], [])
                self.trades[key] = trade
                self._logger.info(f"openOrder: {trade}")
            self.permId2Trade.setdefault(order.permId, trade)
            results = self._results.get("openOrders")
            if results is None:
                self.ib.openOrderEvent.emit(trade)
            else:
                # response to reqOpenOrders or reqAllOpenOrders
                results.append(trade)

        # make sure that the client issues order ids larger than any
        # order id encountered (even from other clients) to avoid
        # "Duplicate order id" error
        self.ib.client.updateReqId(orderId + 1)

    def openOrderEnd(self):
""""""
"""Args::
    contract: 
    order: 
    orderState:"""
    orderState:"""
        contract = Contract.create(**dataclassAsDict(contract))
        orderStatus = OrderStatus(orderId=order.orderId, status=orderState.status)
        trade = Trade(contract, order, orderStatus, [], [])
        self._results["completedOrders"].append(trade)
        if order.permId not in self.permId2Trade:
            self.trades[order.permId] = trade
            self.permId2Trade[order.permId] = trade
        print("completedOrder orderId", contract, order, orderState)

    def completedOrdersEnd(self):
""""""
"""Args::
    orderId: 
    status: 
    filled: 
    remaining: 
    avgFillPrice: 
    permId: 
    parentId: 
    lastFillPrice: 
    clientId: 
    whyHeld: 
    mktCapPrice: (Default value = 0.0)"""
    mktCapPrice: (Default value = 0.0)"""
        key = self.orderKey(clientId, orderId, permId)
        trade = self.trades.get(key)
        if trade:
            msg: Optional[str]
            oldStatus = trade.orderStatus.status
            new = dict(
                status=status,
                filled=filled,
                remaining=remaining,
                avgFillPrice=avgFillPrice,
                permId=permId,
                parentId=parentId,
                lastFillPrice=lastFillPrice,
                clientId=clientId,
                whyHeld=whyHeld,
                mktCapPrice=mktCapPrice,
            )
            curr = dataclassAsDict(trade.orderStatus)
            isChanged = curr != {**curr, **new}
            if isChanged:
                dataclassUpdate(trade.orderStatus, **new)
                msg = ""
            elif (
                status == "Submitted"
                and trade.log
                and trade.log[-1].message == "Modify"
            ):
                # order modifications are acknowledged
                msg = "Modified"
            else:
                msg = None

            if msg is not None:
                logEntry = TradeLogEntry(self.lastTime, status, msg)
                trade.log.append(logEntry)
                self._logger.info(f"orderStatus: {trade}")
                self.ib.orderStatusEvent.emit(trade)
                trade.statusEvent.emit(trade)
                if status != oldStatus:
                    if status == OrderStatus.Filled:
                        trade.filledEvent.emit(trade)
                    elif status == OrderStatus.Cancelled:
                        trade.cancelledEvent.emit(trade)
        else:
            self._logger.error(
                "orderStatus: No order found for orderId %s and clientId %s",
                orderId,
                clientId,
            )

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
"""This wrapper handles both live fills and responses to
reqExecutions.

Args::
    reqId: 
    contract: 
    execution:"""
    execution:"""
        self._logger.info(f"execDetails {execution}")
        if execution.orderId == UNSET_INTEGER:
            # bug in TWS: executions of manual orders have unset value
            execution.orderId = 0
        trade = self.permId2Trade.get(execution.permId)
        if not trade:
            key = self.orderKey(execution.clientId, execution.orderId, execution.permId)
            trade = self.trades.get(key)
        if trade and contract == trade.contract:
            contract = trade.contract
        else:
            contract = Contract.create(**dataclassAsDict(contract))
        execId = execution.execId
        isLive = reqId not in self._futures
        time = self.lastTime if isLive else execution.time
        fill = Fill(contract, execution, CommissionReport(), time)
        if execId not in self.fills:
            # first time we see this execution so add it
            self.fills[execId] = fill
            if trade:
                trade.fills.append(fill)
                logEntry = TradeLogEntry(
                    time,
                    trade.orderStatus.status,
                    f"Fill {execution.shares}@{execution.price}",
                )
                trade.log.append(logEntry)
                if isLive:
                    self._logger.info(f"execDetails: {fill}")
                    self.ib.execDetailsEvent.emit(trade, fill)
                    trade.fillEvent.emit(trade, fill)
        if not isLive:
            self._results[reqId].append(fill)

    def execDetailsEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    commissionReport:"""
"""Args::
    reqId: 
    apiClientId: 
    apiOrderId:"""
    apiOrderId:"""

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
"""Args::
    reqId: 
    contractDetails:"""
    contractDetails:"""
        self._results[reqId].append(contractDetails)
        # self.ib.contractDetails(reqId, contractDetails)

    bondContractDetails = contractDetails

    def contractDetailsEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    contractDescriptions:"""
    contractDescriptions:"""
        self._endReq(reqId, contractDescriptions)

    def marketRule(self, marketRuleId: int, priceIncrements: List[PriceIncrement]):
"""Args::
    marketRuleId: 
    priceIncrements:"""
    priceIncrements:"""
        self._endReq(f"marketRule-{marketRuleId}", priceIncrements)

    def marketDataType(self, reqId: int, marketDataId: int):
"""Args::
    reqId: 
    marketDataId:"""
    marketDataId:"""
        ticker = self.reqId2Ticker.get(reqId)
        if ticker:
            ticker.marketDataType = marketDataId

    def realtimeBar(
        self,
        reqId: int,
        time: int,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        wap: float,
        count: int,
    ):
"""Args::
    reqId: 
    time: 
    open_: 
    high: 
    low: 
    close: 
    volume: 
    wap: 
    count:"""
    count:"""
        dt = datetime.fromtimestamp(time, timezone.utc)
        bar = RealTimeBar(dt, -1, open_, high, low, close, volume, wap, count)
        bars = self.reqId2Subscriber.get(reqId)
        if bars is not None:
            bars.append(bar)
            self.ib.barUpdateEvent.emit(bars, True)
            bars.updateEvent.emit(bars, True)
        print(
            "RealTimeBar. bars:",
            id(bars),
            " -TickerId:",
            reqId,
            " - Time: ",
            (time),
            ", Open: ",
            (open_),
            ", High: ",
            (high),
            ", Low: ",
            (low),
            ", Close: ",
            (close),
            ", Volume: ",
            (volume),
            ", Count: ",
            (count),
            ", WAP: ",
            (wap),
        )

    def historicalData(self, reqId: int, bar: BarData):
"""Args::
    reqId: 
    bar:"""
    bar:"""
        results = self._results.get(reqId)
        if results is not None:
            bar.date = parseIBDatetime(bar.date)  # type: ignore
            results.append(bar)
        # self.ib.historicalData(reqId, bar)
        # print("HistoricalData. ReqId:", reqId, "BarData.", bar)

    def historicalSchedule(
        self,
        reqId: int,
        startDateTime: str,
        endDateTime: str,
        timeZone: str,
        sessions: List[HistoricalSession],
    ):
"""Args::
    reqId: 
    startDateTime: 
    endDateTime: 
    timeZone: 
    sessions:"""
    sessions:"""
        schedule = HistoricalSchedule(startDateTime, endDateTime, timeZone, sessions)
        self._endReq(reqId, schedule)
        print(
            "HistoricalSchedule. ReqId:",
            reqId,
            "Start:",
            startDateTime,
            "End:",
            endDateTime,
            "TimeZone:",
            timeZone,
        )

    def historicalDataEnd(self, reqId, _start: str, _end: str):
"""Args::
    reqId: 
    _start: 
    _end:"""
    _end:"""
        self._endReq(reqId)
        print("HistoricalDataEnd. ReqId:", reqId, "from", _start, "to", _end)

    def historicalDataUpdate(self, reqId: int, bar: BarData):
"""Args::
    reqId: 
    bar:"""
    bar:"""
        bars = self.reqId2Subscriber.get(reqId)
        bar.date = parseIBDatetime(bar.date)
        hasNewBar = len(bars) == 0
        if hasNewBar:
            bars.append(bar)
        else:
            lastDate = bars[-1].date
            if bar.date < lastDate:
                return
            hasNewBar = bar.date > lastDate
            if hasNewBar:
                bars.append(bar)
            elif bars[-1] != bar:
                bars[-1] = bar
            else:
                return

        self.ib.barUpdateEvent.emit(bars, hasNewBar)
        bars.updateEvent.emit(bars, hasNewBar)
        # print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar.date, "New.", hasNewBar)

    def headTimestamp(self, reqId: int, headTimestamp: str):
"""Args::
    reqId: 
    headTimestamp:"""
    headTimestamp:"""
        try:
            dt = parseIBDatetime(headTimestamp)
            self._endReq(reqId, dt)
        except ValueError as exc:
            self._endReq(reqId, exc, False)

    def historicalTicks(self, reqId: int, ticks: List[HistoricalTick], done: bool):
"""Args::
    reqId: 
    ticks: 
    done:"""
    done:"""
        result = self._results.get(reqId)
        if result is not None:
            result += ticks
        if done:
            self._endReq(reqId)

    def historicalTicksBidAsk(
        self, reqId: int, ticks: List[HistoricalTickBidAsk], done: bool
    ):
"""Args::
    reqId: 
    ticks: 
    done:"""
    done:"""
        result = self._results.get(reqId)
        if result is not None:
            result += ticks
        if done:
            self._endReq(reqId)

    def historicalTicksLast(
        self, reqId: int, ticks: List[HistoricalTickLast], done: bool
    ):
"""Args::
    reqId: 
    ticks: 
    done:"""
    done:"""
        result = self._results.get(reqId)
        if result is not None:
            result += ticks
        if done:
            self._endReq(reqId)

    # additional wrapper method provided by Client
    def priceSizeTick(self, reqId: int, tickType: int, price: float, size: float):
"""Args::
    reqId: 
    tickType: 
    price: 
    size:"""
    size:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            self._logger.error(f"priceSizeTick: Unknown reqId: {reqId}")
            return
        # https://interactivebrokers.github.io/tws-api/tick_types.html
        if tickType in (1, 66):
            if price == ticker.bid and size == ticker.bidSize:
                return
            if price != ticker.bid:
                ticker.prevBid = ticker.bid
                ticker.bid = price
            if size != ticker.bidSize:
                ticker.prevBidSize = ticker.bidSize
                ticker.bidSize = size
        elif tickType in (2, 67):
            if price == ticker.ask and size == ticker.askSize:
                return
            if price != ticker.ask:
                ticker.prevAsk = ticker.ask
                ticker.ask = price
            if size != ticker.askSize:
                ticker.prevAskSize = ticker.askSize
                ticker.askSize = size
        elif tickType in (4, 68):
            if price != ticker.last:
                ticker.prevLast = ticker.last
                ticker.last = price
            if size != ticker.lastSize:
                ticker.prevLastSize = ticker.lastSize
                ticker.lastSize = size
        elif tickType in (6, 72):
            ticker.high = price
        elif tickType in (7, 73):
            ticker.low = price
        elif tickType in (9, 75):
            ticker.close = price
        elif tickType in (14, 76):
            ticker.open = price
        elif tickType == 15:
            ticker.low13week = price
        elif tickType == 16:
            ticker.high13week = price
        elif tickType == 17:
            ticker.low26week = price
        elif tickType == 18:
            ticker.high26week = price
        elif tickType == 19:
            ticker.low52week = price
        elif tickType == 20:
            ticker.high52week = price
        elif tickType == 35:
            ticker.auctionPrice = price
        elif tickType == 37:
            ticker.markPrice = price
        elif tickType in (50, 103):
            ticker.bidYield = price
        elif tickType in (51, 104):
            ticker.askYield = price
        elif tickType == 52:
            ticker.lastYield = price
        if price or size:
            tick = TickData(self.lastTime, tickType, price, size)
            ticker.ticks.append(tick)
        self.pendingTickers.add(ticker)

    def tickPrice(self, tickerId: int, tickType: int, price: float, attribs):
"""Args::
    tickerId: 
    tickType: 
    price: 
    attribs:"""
    attribs:"""
        self.ib.tickPrice(tickerId, tickType, price, attribs)

    def tickSize(self, reqId: int, tickType: int, size: float):
"""Args::
    reqId: 
    tickType: 
    size:"""
    size:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            self._logger.error(f"tickSize: Unknown reqId: {reqId}")
            return
        price = -1.0
        # https://interactivebrokers.github.io/tws-api/tick_types.html
        if tickType in (0, 69):
            if size == ticker.bidSize:
                return
            price = ticker.bid
            ticker.prevBidSize = ticker.bidSize
            ticker.bidSize = size
        elif tickType in (3, 70):
            if size == ticker.askSize:
                return
            price = ticker.ask
            ticker.prevAskSize = ticker.askSize
            ticker.askSize = size
        elif tickType in (5, 71):
            price = ticker.last
            if isNan(price):
                return
            if size != ticker.lastSize:
                ticker.prevLastSize = ticker.lastSize
                ticker.lastSize = size
        elif tickType in (8, 74):
            ticker.volume = size
        elif tickType == 21:
            ticker.avVolume = size
        elif tickType == 27:
            ticker.callOpenInterest = size
        elif tickType == 28:
            ticker.putOpenInterest = size
        elif tickType == 29:
            ticker.callVolume = size
        elif tickType == 30:
            ticker.putVolume = size
        elif tickType == 34:
            ticker.auctionVolume = size
        elif tickType == 36:
            ticker.auctionImbalance = size
        elif tickType == 61:
            ticker.regulatoryImbalance = size
        elif tickType == 86:
            ticker.futuresOpenInterest = size
        elif tickType == 87:
            ticker.avOptionVolume = size
        elif tickType == 89:
            ticker.shortableShares = size
        if price or size:
            tick = TickData(self.lastTime, tickType, price, size)
            ticker.ticks.append(tick)
        self.pendingTickers.add(ticker)

    def tickSnapshotEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    tickType: 
    time: 
    price: 
    size: 
    tickAttribLast: 
    exchange: 
    specialConditions:"""
    specialConditions:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            self._logger.error(f"tickByTickAllLast: Unknown reqId: {reqId}")
            return
        if price != ticker.last:
            ticker.prevLast = ticker.last
            ticker.last = price
        if size != ticker.lastSize:
            ticker.prevLastSize = ticker.lastSize
            ticker.lastSize = size
        tick = TickByTickAllLast(
            tickType,
            self.lastTime,
            price,
            size,
            tickAttribLast,
            exchange,
            specialConditions,
        )
        ticker.tickByTicks.append(tick)
        self.pendingTickers.add(ticker)

    def tickByTickBidAsk(
        self,
        reqId: int,
        time: int,
        bidPrice: float,
        askPrice: float,
        bidSize: float,
        askSize: float,
        tickAttribBidAsk: TickAttribBidAsk,
    ):
"""Args::
    reqId: 
    time: 
    bidPrice: 
    askPrice: 
    bidSize: 
    askSize: 
    tickAttribBidAsk:"""
    tickAttribBidAsk:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            self._logger.error(f"tickByTickBidAsk: Unknown reqId: {reqId}")
            return
        if bidPrice != ticker.bid:
            ticker.prevBid = ticker.bid
            ticker.bid = bidPrice
        if bidSize != ticker.bidSize:
            ticker.prevBidSize = ticker.bidSize
            ticker.bidSize = bidSize
        if askPrice != ticker.ask:
            ticker.prevAsk = ticker.ask
            ticker.ask = askPrice
        if askSize != ticker.askSize:
            ticker.prevAskSize = ticker.askSize
            ticker.askSize = askSize
        tick = TickByTickBidAsk(
            self.lastTime,
            bidPrice,
            askPrice,
            bidSize,
            askSize,
            tickAttribBidAsk,
        )
        ticker.tickByTicks.append(tick)
        self.pendingTickers.add(ticker)

    def tickByTickMidPoint(self, reqId: int, time: int, midPoint: float):
"""Args::
    reqId: 
    time: 
    midPoint:"""
    midPoint:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            self._logger.error(f"tickByTickMidPoint: Unknown reqId: {reqId}")
            return
        tick = TickByTickMidPoint(self.lastTime, midPoint)
        ticker.tickByTicks.append(tick)
        self.pendingTickers.add(ticker)

    def tickString(self, reqId: int, tickType: int, value: str):
"""Args::
    reqId: 
    tickType: 
    value:"""
    value:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            return
        try:
            if tickType == 32:
                ticker.bidExchange = value
            elif tickType == 33:
                ticker.askExchange = value
            elif tickType == 84:
                ticker.lastExchange = value
            elif tickType == 47:
                # https://web.archive.org/web/20200725010343/https://interactivebrokers.github.io/tws-api/fundamental_ratios_tags.html
                d = dict(
                    t.split("=")
                    for t in value.split(";")
                    if t  # type: ignore
                )  # type: ignore
                for k, v in d.items():
                    with suppress(ValueError):
                        if v == "-99999.99":
                            v = "nan"
                        d[k] = float(v)  # type: ignore
                        d[k] = int(v)  # type: ignore
                ticker.fundamentalRatios = FundamentalRatios(**d)
            elif tickType in (48, 77):
                # RT Volume or RT Trade Volume string format:
                # price;size;ms since epoch;total volume;VWAP;single trade
                # example:
                # 701.28;1;1348075471534;67854;701.46918464;true
                priceStr, sizeStr, rtTime, volume, vwap, _ = value.split(";")
                if volume:
                    if tickType == 48:
                        ticker.rtVolume = float(volume)
                    elif tickType == 77:
                        ticker.rtTradeVolume = float(volume)
                if vwap:
                    ticker.vwap = float(vwap)
                if rtTime:
                    ticker.rtTime = datetime.fromtimestamp(
                        int(rtTime) / 1000, timezone.utc
                    )
                if priceStr == "":
                    return
                price = float(priceStr)
                size = float(sizeStr)
                if price and size:
                    if ticker.prevLast != ticker.last:
                        ticker.prevLast = ticker.last
                        ticker.last = price
                    if ticker.prevLastSize != ticker.lastSize:
                        ticker.prevLastSize = ticker.lastSize
                        ticker.lastSize = size
                    tick = TickData(self.lastTime, tickType, price, size)
                    ticker.ticks.append(tick)
            elif tickType == 59:
                # Dividend tick:
                # https://interactivebrokers.github.io/tws-api/tick_types.html#ib_dividends
                # example value: '0.83,0.92,20130219,0.23'
                past12, next12, nextDate, nextAmount = value.split(",")
                ticker.dividends = Dividends(
                    float(past12) if past12 else None,
                    float(next12) if next12 else None,
                    parseIBDatetime(nextDate) if nextDate else None,
                    float(nextAmount) if nextAmount else None,
                )
            self.pendingTickers.add(ticker)
        except ValueError:
            self._logger.error(
                f"tickString with tickType {tickType}: malformed value: {value!r}"
            )

    def tickGeneric(self, reqId: int, tickType: int, value: float):
"""Args::
    reqId: 
    tickType: 
    value:"""
    value:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            return
        try:
            value = float(value)
        except ValueError:
            self._logger.error(f"genericTick: malformed value: {value!r}")
            return
        if tickType == 23:
            ticker.histVolatility = value
        elif tickType == 24:
            ticker.impliedVolatility = value
        elif tickType == 31:
            ticker.indexFuturePremium = value
        elif tickType == 49:
            ticker.halted = value
        elif tickType == 54:
            ticker.tradeCount = value
        elif tickType == 55:
            ticker.tradeRate = value
        elif tickType == 56:
            ticker.volumeRate = value
        elif tickType == 58:
            ticker.rtHistVolatility = value
        tick = TickData(self.lastTime, tickType, value, 0)
        ticker.ticks.append(tick)
        self.pendingTickers.add(ticker)

    def tickReqParams(
        self,
        reqId: int,
        minTick: float,
        bboExchange: str,
        snapshotPermissions: int,
    ):
"""Args::
    reqId: 
    minTick: 
    bboExchange: 
    snapshotPermissions:"""
    snapshotPermissions:"""
        ticker = self.reqId2Ticker.get(reqId)
        if not ticker:
            return
        ticker.minTick = minTick
        ticker.bboExchange = bboExchange
        ticker.snapshotPermissions = snapshotPermissions

    def smartComponents(self, reqId, components):
"""Args::
    reqId: 
    components:"""
    components:"""
        self._endReq(reqId, components)

    def mktDepthExchanges(
        self, depthMktDataDescriptions: List[DepthMktDataDescription]
    ):
"""Args::
    depthMktDataDescriptions:"""
"""Args::
    reqId: 
    position: 
    operation: 
    side: 
    price: 
    size:"""
    size:"""
        self.updateMktDepthL2(reqId, position, "", operation, side, price, size)

    def updateMktDepthL2(
        self,
        reqId: int,
        position: int,
        marketMaker: str,
        operation: int,
        side: int,
        price: float,
        size: float,
        isSmartDepth: bool = False,
    ):
"""Args::
    reqId: 
    position: 
    marketMaker: 
    operation: 
    side: 
    price: 
    size: 
    isSmartDepth: (Default value = False)"""
    isSmartDepth: (Default value = False)"""
        # operation: 0 = insert, 1 = update, 2 = delete
        # side: 0 = ask, 1 = bid
        ticker = self.reqId2Ticker[reqId]

        dom = ticker.domBids if side else ticker.domAsks
        if operation == 0:
            dom.insert(position, DOMLevel(price, size, marketMaker))
        elif operation == 1:
            dom[position] = DOMLevel(price, size, marketMaker)
        elif operation == 2:
            if position < len(dom):
                level = dom.pop(position)
                price = level.price
                size = 0

        tick = MktDepthData(
            self.lastTime, position, marketMaker, operation, side, price, size
        )
        ticker.domTicks.append(tick)
        self.pendingTickers.add(ticker)

    def tickOptionComputation(
        self,
        reqId: int,
        tickType: int,
        tickAttrib: int,
        impliedVol: float,
        delta: float,
        optPrice: float,
        pvDividend: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float,
    ):
"""Args::
    reqId: 
    tickType: 
    tickAttrib: 
    impliedVol: 
    delta: 
    optPrice: 
    pvDividend: 
    gamma: 
    vega: 
    theta: 
    undPrice:"""
    undPrice:"""
        comp = OptionComputation(
            tickAttrib,
            impliedVol if impliedVol != -1 else None,
            delta if delta != -2 else None,
            optPrice if optPrice != -1 else None,
            pvDividend if pvDividend != -1 else None,
            gamma if gamma != -2 else None,
            vega if vega != -2 else vega,
            theta if theta != -2 else theta,
            undPrice if undPrice != -1 else None,
        )
        ticker = self.reqId2Ticker.get(reqId)
        if ticker:
            # reply from reqMktData
            # https://interactivebrokers.github.io/tws-api/tick_types.html
            if tickType in (10, 80):
                ticker.bidGreeks = comp
            elif tickType in (11, 81):
                ticker.askGreeks = comp
            elif tickType in (12, 82):
                ticker.lastGreeks = comp
            elif tickType in (13, 83):
                ticker.modelGreeks = comp
            self.pendingTickers.add(ticker)
        elif reqId in self._futures:
            # reply from calculateImpliedVolatility or calculateOptionPrice
            self._endReq(reqId, comp)
        else:
            self._logger.error(f"tickOptionComputation: Unknown reqId: {reqId}")

    def deltaNeutralValidation(self, reqId: int, dnc: DeltaNeutralContract):
"""Args::
    reqId: 
    dnc:"""
    dnc:"""

    def fundamentalData(self, reqId: int, data: str):
"""Args::
    reqId: 
    data:"""
    data:"""
        self._endReq(reqId, data)

    def scannerParameters(self, xml: str):
"""Args::
    xml:"""
"""Args::
    reqId: 
    rank: 
    contractDetails: 
    distance: 
    benchmark: 
    projection: 
    legsStr:"""
    legsStr:"""
        data = ScanData(rank, contractDetails, distance, benchmark, projection, legsStr)
        dataList = self.reqId2Subscriber.get(reqId)
        if dataList is None:
            dataList = self._results.get(reqId)
        if dataList is not None:
            if rank == 0:
                dataList.clear()
            dataList.append(data)

    def scannerDataEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    items:"""
    items:"""
        result = [HistogramData(item.price, item.count) for item in items]
        self._endReq(reqId, result)

    def securityDefinitionOptionParameter(
        self,
        reqId: int,
        exchange: str,
        underlyingConId: int,
        tradingClass: str,
        multiplier: str,
        expirations: List[str],
        strikes: List[float],
    ):
"""Args::
    reqId: 
    exchange: 
    underlyingConId: 
    tradingClass: 
    multiplier: 
    expirations: 
    strikes:"""
    strikes:"""
        chain = OptionChain(
            exchange,
            underlyingConId,
            tradingClass,
            multiplier,
            expirations,
            strikes,
        )
        self._results[reqId].append(chain)

    def securityDefinitionOptionParameterEnd(self, reqId: int):
"""Args::
    reqId:"""
"""Args::
    newsProviders:"""
"""Args::
    _reqId: 
    timeStamp: 
    providerCode: 
    articleId: 
    headline: 
    extraData:"""
    extraData:"""
        news = NewsTick(timeStamp, providerCode, articleId, headline, extraData)
        self.newsTicks.append(news)
        self.ib.tickNewsEvent.emit(news)

    def newsArticle(self, reqId: int, articleType: int, articleText: str):
"""Args::
    reqId: 
    articleType: 
    articleText:"""
    articleText:"""
        article = NewsArticle(articleType, articleText)
        self._endReq(reqId, article)

    def historicalNews(
        self,
        reqId: int,
        time: str,
        providerCode: str,
        articleId: str,
        headline: str,
    ):
"""Args::
    reqId: 
    time: 
    providerCode: 
    articleId: 
    headline:"""
    headline:"""
        dt = parseIBDatetime(time)
        dt = cast(datetime, dt)
        article = HistoricalNews(dt, providerCode, articleId, headline)
        self._results[reqId].append(article)

    def historicalNewsEnd(self, reqId, _hasMore: bool):
"""Args::
    reqId: 
    _hasMore:"""
    _hasMore:"""
        self._endReq(reqId)

    def updateNewsBulletin(
        self, msgId: int, msgType: int, message: str, origExchange: str
    ):
"""Args::
    msgId: 
    msgType: 
    message: 
    origExchange:"""
    origExchange:"""
        bulletin = NewsBulletin(msgId, msgType, message, origExchange)
        self.msgId2NewsBulletin[msgId] = bulletin
        self.ib.newsBulletinEvent.emit(bulletin)

    def receiveFA(self, _faDataType: int, faXmlData: str):
"""Args::
    _faDataType: 
    faXmlData:"""
    faXmlData:"""
        self._endReq("requestFA", faXmlData)

    def currentTime(self, time: int):
"""Args::
    time:"""
"""Args::
    reqId: 
    tickType: 
    basisPoints: 
    formattedBasisPoints: 
    totalDividends: 
    holdDays: 
    futureLastTradeDate: 
    dividendImpact: 
    dividendsToLastTradeDate:"""
    dividendsToLastTradeDate:"""

    def wshMetaData(self, reqId: int, dataJson: str):
"""Args::
    reqId: 
    dataJson:"""
    dataJson:"""
        self.ib.wshMetaEvent.emit(dataJson)
        self._endReq(reqId, dataJson)

    def wshEventData(self, reqId: int, dataJson: str):
"""Args::
    reqId: 
    dataJson:"""
    dataJson:"""
        self.ib.wshEvent.emit(dataJson)
        self._endReq(reqId, dataJson)

    def userInfo(self, reqId: int, whiteBrandingId: str):
"""Args::
    reqId: 
    whiteBrandingId:"""
    whiteBrandingId:"""
        self._endReq(reqId)

    def softDollarTiers(self, reqId: int, tiers: List[SoftDollarTier]):
"""Args::
    reqId: 
    tiers:"""
    tiers:"""

    def familyCodes(self, familyCodes: List[FamilyCode]):
"""Args::
    familyCodes:"""
"""Args::
    reqId: 
    errorCode: 
    errorString: 
    advancedOrderRejectJson:"""
    advancedOrderRejectJson:"""
        # https://interactivebrokers.github.io/tws-api/message_codes.html
        isRequest = reqId in self._futures
        trade = self.trades.get((self.clientId, reqId))
        warningCodes = {110, 165, 202, 399, 404, 434, 492, 10167}
        isWarning = errorCode in warningCodes or 2100 <= errorCode < 2200
        if errorCode == 110 and isRequest:
            # whatIf request failed
            isWarning = False
        if (
            errorCode == 110
            and trade
            and trade.orderStatus.status == OrderStatus.PendingSubmit
        ):
            # invalid price for a new order must cancel it
            isWarning = False

        msg = (
            f"{'Warning' if isWarning else 'Error'} "
            f"{errorCode}, reqId {reqId}: {errorString}"
        )
        contract = self._reqId2Contract.get(reqId)
        if contract:
            msg += f", contract: {contract}"

        if isWarning:
            self._logger.info(msg)
        else:
            self._logger.error(msg)
            if isRequest:
                # the request failed
                if self.ib.RaiseRequestErrors:
                    error = RequestError(reqId, errorCode, errorString)
                    self._endReq(reqId, error, success=False)
                else:
                    self._endReq(reqId)

            elif trade:
                # something is wrong with the order, cancel it
                if advancedOrderRejectJson:
                    trade.advancedError = advancedOrderRejectJson
                if not trade.isDone():
                    status = trade.orderStatus.status = OrderStatus.Cancelled
                    logEntry = TradeLogEntry(self.lastTime, status, msg, errorCode)
                    trade.log.append(logEntry)
                    self._logger.warning(f"Canceled order: {trade}")
                    self.ib.orderStatusEvent.emit(trade)
                    trade.statusEvent.emit(trade)
                    trade.cancelledEvent.emit(trade)

        if errorCode == 165:
            # for scan data subscription there are no longer matching results
            dataList = self.reqId2Subscriber.get(reqId)
            if dataList:
                dataList.clear()
                dataList.updateEvent.emit(dataList)
        elif errorCode == 317:
            # Market depth data has been RESET
            ticker = self.reqId2Ticker.get(reqId)
            if ticker:
                # clear all DOM levels
                ticker.domTicks += [
                    MktDepthData(self.lastTime, 0, "", 2, 0, level.price, 0)
                    for level in ticker.domAsks
                ]
                ticker.domTicks += [
                    MktDepthData(self.lastTime, 0, "", 2, 1, level.price, 0)
                    for level in ticker.domBids
                ]
                ticker.domAsks.clear()
                ticker.domBids.clear()
                self.pendingTickers.add(ticker)
        elif errorCode == 10225:
            # Bust event occurred, current subscription is deactivated.
            # Please resubscribe real-time bars immediately
            bars = self.reqId2Subscriber.get(reqId)
            if isinstance(bars, RealTimeBarList):
                self.ib.client.cancelRealTimeBars(reqId)
                self.ib.client.reqRealTimeBars(
                    reqId,
                    bars.contract,
                    bars.barSize,
                    bars.whatToShow,
                    bars.useRTH,
                    bars.realTimeBarsOptions,
                )
            elif isinstance(bars, BarDataList):
                self.ib.client.cancelHistoricalData(reqId)
                self.ib.client.reqHistoricalData(
                    reqId,
                    bars.contract,
                    bars.endDateTime,
                    bars.durationStr,
                    bars.barSizeSetting,
                    bars.whatToShow,
                    bars.useRTH,
                    bars.formatDate,
                    bars.keepUpToDate,
                    bars.chartOptions,
                )

        self.ib.errorEvent.emit(reqId, errorCode, errorString, contract)

    def tcpDataArrived(self):
""""""
""""""
        self.ib.updateEvent.emit()
        if self.pendingTickers:
            for ticker in self.pendingTickers:
                ticker.time = self.lastTime
                ticker.updateEvent.emit(ticker)
            self.ib.pendingTickersEvent.emit(self.pendingTickers)
