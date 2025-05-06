"""Socket client for communicating with Interactive Brokers."""

import asyncio
import io
import logging
import math
import struct
import time
from collections import deque
from typing import Deque, List, Optional

from eventkit import Event

from .connection import Connection
from .contract import Contract
from .decoder import Decoder
from .objects import ConnectionStats, WshEventData
from .util import UNSET_DOUBLE, UNSET_INTEGER, dataclassAsTuple, getLoop, run


class Client:
    """Replacement for ``ibapi.client.EClient`` that uses asyncio.
The client is fully asynchronous and has its own
event-driven networking code that replaces the
networking code of the standard EClient.
It also replaces the infinite loop of ``EClient.run()``
with the asyncio event loop. It can be used as a drop-in
replacement for the standard EClient as provided by IBAPI.
Compared to the standard EClient this client has the following
additional features:
* ``client.connect()`` will block until the client is ready to
serve requests; It is not necessary to wait for ``nextValidId``
to start requests as the client has already done that.
The reqId is directly available with :py:meth:`.getReqId()`.
* ``client.connectAsync()`` is a coroutine for connecting asynchronously.
* When blocking, ``client.connect()`` can be made to time out with
the timeout parameter (default 2 seconds).
* Optional ``wrapper.priceSizeTick(reqId, tickType, price, size)`` that
combines price and size instead of the two wrapper methods
priceTick and sizeTick.
* Automatic request throttling.
* Optional ``wrapper.tcpDataArrived()`` method;
If the wrapper has this method it is invoked directly after
a network packet has arrived.
A possible use is to timestamp all data in the packet with
the exact same time.
* Optional ``wrapper.tcpDataProcessed()`` method;
If the wrapper has this method it is invoked after the
network packet's data has been handled.
A possible use is to write or evaluate the newly arrived data in
one batch instead of item by item."""

    events = ("apiStart", "apiEnd", "apiError", "throttleStart", "throttleEnd")

    MaxRequests = 45
    RequestsInterval = 1

    MinClientVersion = 157
    MaxClientVersion = 178

    (DISCONNECTED, CONNECTING, CONNECTED) = range(3)

    def __init__(self, wrapper):
"""Args::
    wrapper:"""
""""""
""":rtype: int"""
        """
        return self._serverVersion

    def run(self):
""""""
""""""
        """Is the API connection up and running?
:rtype: bool"""
        return self._apiReady

    def connectionStats(self) -> ConnectionStats:
        """Get statistics about the connection.
:rtype: ConnectionStats"""
        if not self.isReady():
            raise ConnectionError("Not connected")
        return ConnectionStats(
            self._startTime,
            time.time() - self._startTime,
            self._numBytesRecv,
            self.conn.numBytesSent,
            self._numMsgRecv,
            self.conn.numMsgSent,
        )

    def getReqId(self) -> int:
        """Get new request ID.
:rtype: int"""
        if not self.isReady():
            raise ConnectionError("Not connected")
        newId = self._reqIdSeq
        self._reqIdSeq += 1
        return newId

    def updateReqId(self, minReqId):
"""Update the next reqId to be at least ``minReqId``.

Args::
    minReqId:"""
    minReqId:"""
        self._reqIdSeq = max(self._reqIdSeq, minReqId)

    def getAccounts(self) -> List[str]:
        """Get the list of account names that are under management.
:rtype: List[str]"""
        if not self.isReady():
            raise ConnectionError("Not connected")
        return self._accounts

    def setConnectOptions(self, connectOptions: str):
"""Set additional connect options.

Args::
    connectOptions: Use "+PACEAPI" to use request-pacing built"""
    connectOptions: Use "+PACEAPI" to use request-pacing built"""
        self.connectOptions = connectOptions.encode()

    def connect(
        self,
        host: str,
        port: int,
        clientId: int,
        timeout: Optional[float] = 2.0,
    ):
"""Connect to a running TWS or IB gateway application.

Args::
    host: Host name or IP address.
    port: Port number.
    clientId: ID number to use for this client; must be unique per
    timeout: If establishing the connection takes longer than"""
    timeout: If establishing the connection takes longer than"""
        run(self.connectAsync(host, port, clientId, timeout))

    async def connectAsync(self, host, port, clientId, timeout=2.0):
        """

        :param host:
        :param port:
        :param clientId:
        :param timeout:  (Default value = 2.0)

        """
        try:
            self._logger.info(
                f"Connecting to {host}:{port} with clientId {clientId}..."
            )
            self.host = host
            self.port = int(port)
            self.clientId = int(clientId)
            self.connState = Client.CONNECTING
            timeout = timeout or None
            await asyncio.wait_for(self.conn.connectAsync(host, port), timeout)
            self._logger.info("Connected")
            msg = b"API\0" + self._prefix(
                b"v%d..%d%s"
                % (
                    self.MinClientVersion,
                    self.MaxClientVersion,
                    b" " + self.connectOptions if self.connectOptions else b"",
                )
            )
            self.conn.sendMsg(msg)
            await asyncio.wait_for(self.apiStart, timeout)
            self._logger.info("API connection ready")
        except BaseException as e:
            self.disconnect()
            msg = f"API connection failed: {e!r}"
            self._logger.error(msg)
            self.apiError.emit(msg)
            if isinstance(e, ConnectionRefusedError):
                self._logger.error("Make sure API port on TWS/IBG is open")
            raise

    def disconnect(self):
        """Disconnect from IB connection."""
        self._logger.info("Disconnecting")
        self.connState = Client.DISCONNECTED
        self.conn.disconnect()
        self.reset()

    def send(self, *fields, makeEmpty=True):
"""Serialize and send the given fields using the IB socket protocol.

Args::
    makeEmpty: (Default value = True)"""
    makeEmpty: (Default value = True)"""
        if not self.isConnected():
            raise ConnectionError("Not connected")

        msg = io.StringIO()
        empty = (None, UNSET_INTEGER, UNSET_DOUBLE) if makeEmpty else (None,)
        for field in fields:
            typ = type(field)
            if field in empty:
                s = ""
            elif typ is str:
                s = field
            elif type is int:
                s = str(field)
            elif typ is float:
                s = "Infinite" if field == math.inf else str(field)
            elif typ is bool:
                s = "1" if field else "0"
            elif typ is list:
                # list of TagValue
                s = "".join(f"{v.tag}={v.value};" for v in field)
            elif isinstance(field, Contract):
                c = field
                s = "\0".join(
                    str(f)
                    for f in (
                        c.conId,
                        c.symbol,
                        c.secType,
                        c.lastTradeDateOrContractMonth,
                        c.strike,
                        c.right,
                        c.multiplier,
                        c.exchange,
                        c.primaryExchange,
                        c.currency,
                        c.localSymbol,
                        c.tradingClass,
                    )
                )
            else:
                s = str(field)
            msg.write(s)
            msg.write("\0")
        self.sendMsg(msg.getvalue())

    def sendMsg(self, msg: str):
"""Args::
    msg:"""
"""Args::
    msg:"""
"""Args::
    data:"""
"""Args::
    msg:"""
"""Args::
    reqId: 
    contract: 
    genericTickList: 
    snapshot: 
    regulatorySnapshot: 
    mktDataOptions:"""
    mktDataOptions:"""
        fields = [1, 11, reqId, contract]

        if contract.secType == "BAG":
            legs = contract.comboLegs or []
            fields += [len(legs)]
            for leg in legs:
                fields += [leg.conId, leg.ratio, leg.action, leg.exchange]

        dnc = contract.deltaNeutralContract
        if dnc:
            fields += [True, dnc.conId, dnc.delta, dnc.price]
        else:
            fields += [False]

        fields += [
            genericTickList,
            snapshot,
            regulatorySnapshot,
            mktDataOptions,
        ]
        self.send(*fields)

    def cancelMktData(self, reqId):
"""Args::
    reqId:"""
"""Args::
    orderId: 
    contract: 
    order:"""
    order:"""
        version = self.serverVersion()
        fields = [
            3,
            orderId,
            contract,
            contract.secIdType,
            contract.secId,
            order.action,
            order.totalQuantity,
            order.orderType,
            order.lmtPrice,
            order.auxPrice,
            order.tif,
            order.ocaGroup,
            order.account,
            order.openClose,
            order.origin,
            order.orderRef,
            order.transmit,
            order.parentId,
            order.blockOrder,
            order.sweepToFill,
            order.displaySize,
            order.triggerMethod,
            order.outsideRth,
            order.hidden,
        ]

        if contract.secType == "BAG":
            legs = contract.comboLegs or []
            fields += [len(legs)]
            for leg in legs:
                fields += [
                    leg.conId,
                    leg.ratio,
                    leg.action,
                    leg.exchange,
                    leg.openClose,
                    leg.shortSaleSlot,
                    leg.designatedLocation,
                    leg.exemptCode,
                ]

            legs = order.orderComboLegs or []
            fields += [len(legs)]
            for leg in legs:
                fields += [leg.price]

            params = order.smartComboRoutingParams or []
            fields += [len(params)]
            for param in params:
                fields += [param.tag, param.value]

        fields += [
            "",
            order.discretionaryAmt,
            order.goodAfterTime,
            order.goodTillDate,
            order.faGroup,
            order.faMethod,
            order.faPercentage,
        ]
        if version < 177:
            fields += [order.faProfile]
        fields += [
            order.modelCode,
            order.shortSaleSlot,
            order.designatedLocation,
            order.exemptCode,
            order.ocaType,
            order.rule80A,
            order.settlingFirm,
            order.allOrNone,
            order.minQty,
            order.percentOffset,
            order.eTradeOnly,
            order.firmQuoteOnly,
            order.nbboPriceCap,
            order.auctionStrategy,
            order.startingPrice,
            order.stockRefPrice,
            order.delta,
            order.stockRangeLower,
            order.stockRangeUpper,
            order.overridePercentageConstraints,
            order.volatility,
            order.volatilityType,
            order.deltaNeutralOrderType,
            order.deltaNeutralAuxPrice,
        ]

        if order.deltaNeutralOrderType:
            fields += [
                order.deltaNeutralConId,
                order.deltaNeutralSettlingFirm,
                order.deltaNeutralClearingAccount,
                order.deltaNeutralClearingIntent,
                order.deltaNeutralOpenClose,
                order.deltaNeutralShortSale,
                order.deltaNeutralShortSaleSlot,
                order.deltaNeutralDesignatedLocation,
            ]

        fields += [
            order.continuousUpdate,
            order.referencePriceType,
            order.trailStopPrice,
            order.trailingPercent,
            order.scaleInitLevelSize,
            order.scaleSubsLevelSize,
            order.scalePriceIncrement,
        ]

        if 0 < order.scalePriceIncrement < UNSET_DOUBLE:
            fields += [
                order.scalePriceAdjustValue,
                order.scalePriceAdjustInterval,
                order.scaleProfitOffset,
                order.scaleAutoReset,
                order.scaleInitPosition,
                order.scaleInitFillQty,
                order.scaleRandomPercent,
            ]

        fields += [
            order.scaleTable,
            order.activeStartTime,
            order.activeStopTime,
            order.hedgeType,
        ]

        if order.hedgeType:
            fields += [order.hedgeParam]

        fields += [
            order.optOutSmartRouting,
            order.clearingAccount,
            order.clearingIntent,
            order.notHeld,
        ]

        dnc = contract.deltaNeutralContract
        if dnc:
            fields += [True, dnc.conId, dnc.delta, dnc.price]
        else:
            fields += [False]

        fields += [order.algoStrategy]
        if order.algoStrategy:
            params = order.algoParams or []
            fields += [len(params)]
            for param in params:
                fields += [param.tag, param.value]

        fields += [
            order.algoId,
            order.whatIf,
            order.orderMiscOptions,
            order.solicited,
            order.randomizeSize,
            order.randomizePrice,
        ]

        if order.orderType in ("PEG BENCH", "PEGBENCH"):
            fields += [
                order.referenceContractId,
                order.isPeggedChangeAmountDecrease,
                order.peggedChangeAmount,
                order.referenceChangeAmount,
                order.referenceExchangeId,
            ]

        fields += [len(order.conditions)]
        if order.conditions:
            for cond in order.conditions:
                fields += dataclassAsTuple(cond)
            fields += [order.conditionsIgnoreRth, order.conditionsCancelOrder]

        fields += [
            order.adjustedOrderType,
            order.triggerPrice,
            order.lmtPriceOffset,
            order.adjustedStopPrice,
            order.adjustedStopLimitPrice,
            order.adjustedTrailingAmount,
            order.adjustableTrailingUnit,
            order.extOperator,
            order.softDollarTier.name,
            order.softDollarTier.val,
            order.cashQty,
            order.mifid2DecisionMaker,
            order.mifid2DecisionAlgo,
            order.mifid2ExecutionTrader,
            order.mifid2ExecutionAlgo,
            order.dontUseAutoPriceForHedge,
            order.isOmsContainer,
            order.discretionaryUpToLimitPrice,
            order.usePriceMgmtAlgo,
        ]

        if version >= 158:
            fields += [order.duration]
        if version >= 160:
            fields += [order.postToAts]
        if version >= 162:
            fields += [order.autoCancelParent]
        if version >= 166:
            fields += [order.advancedErrorOverride]
        if version >= 169:
            fields += [order.manualOrderTime]
        if version >= 170:
            if contract.exchange == "IBKRATS":
                fields += [order.minTradeQty]
            if order.orderType in ("PEG BEST", "PEGBEST"):
                fields += [order.minCompeteSize, order.competeAgainstBestOffset]
                if order.competeAgainstBestOffset == math.inf:
                    fields += [order.midOffsetAtWhole, order.midOffsetAtHalf]
            elif order.orderType in ("PEG MID", "PEGMID"):
                fields += [order.midOffsetAtWhole, order.midOffsetAtHalf]

        self.send(*fields)

    def cancelOrder(self, orderId, manualCancelOrderTime=""):
"""Args::
    orderId: 
    manualCancelOrderTime: (Default value = "")"""
    manualCancelOrderTime: (Default value = "")"""
        fields = [4, 1, orderId]
        if self.serverVersion() >= 169:
            fields += [manualCancelOrderTime]
        self.send(*fields)

    def reqOpenOrders(self):
""""""
"""Args::
    subscribe: 
    acctCode:"""
    acctCode:"""
        self.send(6, 2, subscribe, acctCode)

    def reqExecutions(self, reqId, execFilter):
"""Args::
    reqId: 
    execFilter:"""
    execFilter:"""
        self.send(
            7,
            3,
            reqId,
            execFilter.clientId,
            execFilter.acctCode,
            execFilter.time,
            execFilter.symbol,
            execFilter.secType,
            execFilter.exchange,
            execFilter.side,
        )

    def reqIds(self, numIds):
"""Args::
    numIds:"""
"""Args::
    reqId: 
    contract:"""
    contract:"""
        fields = [
            9,
            8,
            reqId,
            contract,
            contract.includeExpired,
            contract.secIdType,
            contract.secId,
        ]
        if self.serverVersion() >= 176:
            fields += [contract.issuerId]
        self.send(*fields)

    def reqMktDepth(self, reqId, contract, numRows, isSmartDepth, mktDepthOptions):
"""Args::
    reqId: 
    contract: 
    numRows: 
    isSmartDepth: 
    mktDepthOptions:"""
    mktDepthOptions:"""
        self.send(
            10,
            5,
            reqId,
            contract.conId,
            contract.symbol,
            contract.secType,
            contract.lastTradeDateOrContractMonth,
            contract.strike,
            contract.right,
            contract.multiplier,
            contract.exchange,
            contract.primaryExchange,
            contract.currency,
            contract.localSymbol,
            contract.tradingClass,
            numRows,
            isSmartDepth,
            mktDepthOptions,
        )

    def cancelMktDepth(self, reqId, isSmartDepth):
"""Args::
    reqId: 
    isSmartDepth:"""
    isSmartDepth:"""
        self.send(11, 1, reqId, isSmartDepth)

    def reqNewsBulletins(self, allMsgs):
"""Args::
    allMsgs:"""
""""""
"""Args::
    logLevel:"""
"""Args::
    bAutoBind:"""
""""""
""""""
"""Args::
    faData:"""
"""Args::
    reqId: 
    faData: 
    cxml:"""
    cxml:"""
        self.send(19, 1, faData, cxml, reqId)

    def reqHistoricalData(
        self,
        reqId,
        contract,
        endDateTime,
        durationStr,
        barSizeSetting,
        whatToShow,
        useRTH,
        formatDate,
        keepUpToDate,
        chartOptions,
    ):
"""Args::
    reqId: 
    contract: 
    endDateTime: 
    durationStr: 
    barSizeSetting: 
    whatToShow: 
    useRTH: 
    formatDate: 
    keepUpToDate: 
    chartOptions:"""
    chartOptions:"""
        fields = [
            20,
            reqId,
            contract,
            contract.includeExpired,
            endDateTime,
            barSizeSetting,
            durationStr,
            useRTH,
            whatToShow,
            formatDate,
        ]

        if contract.secType == "BAG":
            legs = contract.comboLegs or []
            fields += [len(legs)]
            for leg in legs:
                fields += [leg.conId, leg.ratio, leg.action, leg.exchange]

        fields += [keepUpToDate, chartOptions]
        self.send(*fields)

    def exerciseOptions(
        self,
        reqId,
        contract,
        exerciseAction,
        exerciseQuantity,
        account,
        override,
    ):
"""Args::
    reqId: 
    contract: 
    exerciseAction: 
    exerciseQuantity: 
    account: 
    override:"""
    override:"""
        self.send(
            21,
            2,
            reqId,
            contract.conId,
            contract.symbol,
            contract.secType,
            contract.lastTradeDateOrContractMonth,
            contract.strike,
            contract.right,
            contract.multiplier,
            contract.exchange,
            contract.currency,
            contract.localSymbol,
            contract.tradingClass,
            exerciseAction,
            exerciseQuantity,
            account,
            override,
        )

    def reqScannerSubscription(
        self,
        reqId,
        subscription,
        scannerSubscriptionOptions,
        scannerSubscriptionFilterOptions,
    ):
"""Args::
    reqId: 
    subscription: 
    scannerSubscriptionOptions: 
    scannerSubscriptionFilterOptions:"""
    scannerSubscriptionFilterOptions:"""
        sub = subscription
        self.send(
            22,
            reqId,
            sub.numberOfRows,
            sub.instrument,
            sub.locationCode,
            sub.scanCode,
            sub.abovePrice,
            sub.belowPrice,
            sub.aboveVolume,
            sub.marketCapAbove,
            sub.marketCapBelow,
            sub.moodyRatingAbove,
            sub.moodyRatingBelow,
            sub.spRatingAbove,
            sub.spRatingBelow,
            sub.maturityDateAbove,
            sub.maturityDateBelow,
            sub.couponRateAbove,
            sub.couponRateBelow,
            sub.excludeConvertible,
            sub.averageOptionVolumeAbove,
            sub.scannerSettingPairs,
            sub.stockTypeFilter,
            scannerSubscriptionFilterOptions,
            scannerSubscriptionOptions,
        )

    def cancelScannerSubscription(self, reqId):
"""Args::
    reqId:"""
""""""
"""Args::
    reqId:"""
""""""
"""Args::
    reqId: 
    contract: 
    barSize: 
    whatToShow: 
    useRTH: 
    realTimeBarsOptions:"""
    realTimeBarsOptions:"""
        self.send(
            50,
            3,
            reqId,
            contract,
            barSize,
            whatToShow,
            useRTH,
            realTimeBarsOptions,
        )

    def cancelRealTimeBars(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    contract: 
    reportType: 
    fundamentalDataOptions:"""
    fundamentalDataOptions:"""
        options = fundamentalDataOptions or []
        self.send(
            52,
            2,
            reqId,
            contract.conId,
            contract.symbol,
            contract.secType,
            contract.exchange,
            contract.primaryExchange,
            contract.currency,
            contract.localSymbol,
            reportType,
            len(options),
            options,
        )

    def cancelFundamentalData(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    contract: 
    optionPrice: 
    underPrice: 
    implVolOptions:"""
    implVolOptions:"""
        self.send(
            54,
            3,
            reqId,
            contract,
            optionPrice,
            underPrice,
            len(implVolOptions),
            implVolOptions,
        )

    def calculateOptionPrice(
        self, reqId, contract, volatility, underPrice, optPrcOptions
    ):
"""Args::
    reqId: 
    contract: 
    volatility: 
    underPrice: 
    optPrcOptions:"""
    optPrcOptions:"""
        self.send(
            55,
            3,
            reqId,
            contract,
            volatility,
            underPrice,
            len(optPrcOptions),
            optPrcOptions,
        )

    def cancelCalculateImpliedVolatility(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId:"""
""""""
"""Args::
    marketDataType:"""
""""""
"""Args::
    reqId: 
    groupName: 
    tags:"""
    tags:"""
        self.send(62, 1, reqId, groupName, tags)

    def cancelAccountSummary(self, reqId):
"""Args::
    reqId:"""
""""""
"""Args::
    apiName: 
    apiVersion:"""
    apiVersion:"""
        self.send(65, 1, apiName, apiVersion)

    def verifyMessage(self, apiData):
"""Args::
    apiData:"""
"""Args::
    reqId:"""
"""Args::
    reqId: 
    groupId:"""
    groupId:"""
        self.send(68, 1, reqId, groupId)

    def updateDisplayGroup(self, reqId, contractInfo):
"""Args::
    reqId: 
    contractInfo:"""
    contractInfo:"""
        self.send(69, 1, reqId, contractInfo)

    def unsubscribeFromGroupEvents(self, reqId):
"""Args::
    reqId:"""
""""""
"""Args::
    apiName: 
    apiVersion: 
    opaqueIsvKey:"""
    opaqueIsvKey:"""
        self.send(72, 1, apiName, apiVersion, opaqueIsvKey)

    def verifyAndAuthMessage(self, apiData, xyzResponse):
"""Args::
    apiData: 
    xyzResponse:"""
    xyzResponse:"""
        self.send(73, 1, apiData, xyzResponse)

    def reqPositionsMulti(self, reqId, account, modelCode):
"""Args::
    reqId: 
    account: 
    modelCode:"""
    modelCode:"""
        self.send(74, 1, reqId, account, modelCode)

    def cancelPositionsMulti(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    account: 
    modelCode: 
    ledgerAndNLV:"""
    ledgerAndNLV:"""
        self.send(76, 1, reqId, account, modelCode, ledgerAndNLV)

    def cancelAccountUpdatesMulti(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    underlyingSymbol: 
    futFopExchange: 
    underlyingSecType: 
    underlyingConId:"""
    underlyingConId:"""
        self.send(
            78,
            reqId,
            underlyingSymbol,
            futFopExchange,
            underlyingSecType,
            underlyingConId,
        )

    def reqSoftDollarTiers(self, reqId):
"""Args::
    reqId:"""
""""""
"""Args::
    reqId: 
    pattern:"""
    pattern:"""
        self.send(81, reqId, pattern)

    def reqMktDepthExchanges(self):
""""""
"""Args::
    reqId: 
    bboExchange:"""
    bboExchange:"""
        self.send(83, reqId, bboExchange)

    def reqNewsArticle(self, reqId, providerCode, articleId, newsArticleOptions):
"""Args::
    reqId: 
    providerCode: 
    articleId: 
    newsArticleOptions:"""
    newsArticleOptions:"""
        self.send(84, reqId, providerCode, articleId, newsArticleOptions)

    def reqNewsProviders(self):
""""""
"""Args::
    reqId: 
    conId: 
    providerCodes: 
    startDateTime: 
    endDateTime: 
    totalResults: 
    historicalNewsOptions:"""
    historicalNewsOptions:"""
        self.send(
            86,
            reqId,
            conId,
            providerCodes,
            startDateTime,
            endDateTime,
            totalResults,
            historicalNewsOptions,
        )

    def reqHeadTimeStamp(self, reqId, contract, whatToShow, useRTH, formatDate):
"""Args::
    reqId: 
    contract: 
    whatToShow: 
    useRTH: 
    formatDate:"""
    formatDate:"""
        self.send(
            87,
            reqId,
            contract,
            contract.includeExpired,
            useRTH,
            whatToShow,
            formatDate,
        )

    def reqHistogramData(self, tickerId, contract, useRTH, timePeriod):
"""Args::
    tickerId: 
    contract: 
    useRTH: 
    timePeriod:"""
    timePeriod:"""
        self.send(88, tickerId, contract, contract.includeExpired, useRTH, timePeriod)

    def cancelHistogramData(self, tickerId):
"""Args::
    tickerId:"""
"""Args::
    reqId:"""
"""Args::
    marketRuleId:"""
"""Args::
    reqId: 
    account: 
    modelCode:"""
    modelCode:"""
        self.send(92, reqId, account, modelCode)

    def cancelPnL(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    account: 
    modelCode: 
    conid:"""
    conid:"""
        self.send(94, reqId, account, modelCode, conid)

    def cancelPnLSingle(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId: 
    contract: 
    startDateTime: 
    endDateTime: 
    numberOfTicks: 
    whatToShow: 
    useRth: 
    ignoreSize: 
    miscOptions:"""
    miscOptions:"""
        self.send(
            96,
            reqId,
            contract,
            contract.includeExpired,
            startDateTime,
            endDateTime,
            numberOfTicks,
            whatToShow,
            useRth,
            ignoreSize,
            miscOptions,
        )

    def reqTickByTickData(self, reqId, contract, tickType, numberOfTicks, ignoreSize):
"""Args::
    reqId: 
    contract: 
    tickType: 
    numberOfTicks: 
    ignoreSize:"""
    ignoreSize:"""
        self.send(97, reqId, contract, tickType, numberOfTicks, ignoreSize)

    def cancelTickByTickData(self, reqId):
"""Args::
    reqId:"""
"""Args::
    apiOnly:"""
"""Args::
    reqId:"""
"""Args::
    reqId:"""
"""Args::
    reqId: 
    data:"""
    data:"""
        fields = [102, reqId, data.conId]
        if self.serverVersion() >= 171:
            fields += [
                data.filter,
                data.fillWatchlist,
                data.fillPortfolio,
                data.fillCompetitors,
            ]
        if self.serverVersion() >= 173:
            fields += [data.startDate, data.endDate, data.totalLimit]
        self.send(*fields, makeEmpty=False)

    def cancelWshEventData(self, reqId):
"""Args::
    reqId:"""
"""Args::
    reqId:"""
    reqId:"""
        self.send(104, reqId)
