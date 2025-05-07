"""Deserialize and dispatch messages."""

import dataclasses
import logging
from datetime import datetime, timezone
from typing import Any, cast

from .contract import (
    ComboLeg,
    Contract,
    ContractDescription,
    ContractDetails,
    DeltaNeutralContract,
)
from .objects import (
    BarData,
    CommissionReport,
    DepthMktDataDescription,
    Execution,
    FamilyCode,
    HistogramData,
    HistoricalSession,
    HistoricalTick,
    HistoricalTickBidAsk,
    HistoricalTickLast,
    NewsProvider,
    PriceIncrement,
    SmartComponent,
    SoftDollarTier,
    TagValue,
    TickAttribBidAsk,
    TickAttribLast,
)
from .order import Order, OrderComboLeg, OrderCondition, OrderState
from .util import UNSET_DOUBLE, ZoneInfo, parseIBDatetime
from .wrapper import Wrapper


class Decoder:
    """Decode IB messages and invoke corresponding wrapper methods."""

    def __init__(self, wrapper: Wrapper, serverVersion: int):
"""Args::
    wrapper: 
    serverVersion:"""
    serverVersion:"""
        self.wrapper = wrapper
        self.serverVersion = serverVersion
        self.logger = logging.getLogger("ib_insync.Decoder")
        self.handlers = {
            1: self.priceSizeTick,
            2: self.wrap("tickSize", [int, int, float]),
            3: self.wrap(
                "orderStatus",
                [
                    int,
                    str,
                    float,
                    float,
                    float,
                    int,
                    int,
                    float,
                    int,
                    str,
                    float,
                ],
                skip=1,
            ),
            4: self.errorMsg,
            5: self.openOrder,
            6: self.wrap("updateAccountValue", [str, str, str, str]),
            7: self.updatePortfolio,
            8: self.wrap("updateAccountTime", [str]),
            9: self.wrap("nextValidId", [int]),
            10: self.contractDetails,
            11: self.execDetails,
            12: self.wrap("updateMktDepth", [int, int, int, int, float, float]),
            13: self.wrap(
                "updateMktDepthL2",
                [int, int, str, int, int, float, float, bool],
            ),
            14: self.wrap("updateNewsBulletin", [int, int, str, str]),
            15: self.wrap("managedAccounts", [str]),
            16: self.wrap("receiveFA", [int, str]),
            17: self.historicalData,
            18: self.bondContractDetails,
            19: self.wrap("scannerParameters", [str]),
            20: self.scannerData,
            21: self.tickOptionComputation,
            45: self.wrap("tickGeneric", [int, int, float]),
            46: self.wrap("tickString", [int, int, str]),
            47: self.wrap(
                "tickEFP", [int, int, float, str, float, int, str, float, float]
            ),
            49: self.wrap("currentTime", [int]),
            50: self.wrap(
                "realtimeBar",
                [int, int, float, float, float, float, float, float, int],
            ),
            51: self.wrap("fundamentalData", [int, str]),
            52: self.wrap("contractDetailsEnd", [int]),
            53: self.wrap("openOrderEnd", []),
            54: self.wrap("accountDownloadEnd", [str]),
            55: self.wrap("execDetailsEnd", [int]),
            56: self.deltaNeutralValidation,
            57: self.wrap("tickSnapshotEnd", [int]),
            58: self.wrap("marketDataType", [int, int]),
            59: self.commissionReport,
            61: self.position,
            62: self.wrap("positionEnd", []),
            63: self.wrap("accountSummary", [int, str, str, str, str]),
            64: self.wrap("accountSummaryEnd", [int]),
            65: self.wrap("verifyMessageAPI", [str]),
            66: self.wrap("verifyCompleted", [bool, str]),
            67: self.wrap("displayGroupList", [int, str]),
            68: self.wrap("displayGroupUpdated", [int, str]),
            69: self.wrap("verifyAndAuthMessageAPI", [str, str]),
            70: self.wrap("verifyAndAuthCompleted", [bool, str]),
            71: self.positionMulti,
            72: self.wrap("positionMultiEnd", [int]),
            73: self.wrap("accountUpdateMulti", [int, str, str, str, str, str]),
            74: self.wrap("accountUpdateMultiEnd", [int]),
            75: self.securityDefinitionOptionParameter,
            76: self.wrap("securityDefinitionOptionParameterEnd", [int], skip=1),
            77: self.softDollarTiers,
            78: self.familyCodes,
            79: self.symbolSamples,
            80: self.mktDepthExchanges,
            81: self.wrap("tickReqParams", [int, float, str, int], skip=1),
            82: self.smartComponents,
            83: self.wrap("newsArticle", [int, int, str], skip=1),
            84: self.wrap("tickNews", [int, int, str, str, str, str], skip=1),
            85: self.newsProviders,
            86: self.wrap("historicalNews", [int, str, str, str, str], skip=1),
            87: self.wrap("historicalNewsEnd", [int, bool], skip=1),
            88: self.wrap("headTimestamp", [int, str], skip=1),
            89: self.histogramData,
            90: self.historicalDataUpdate,
            91: self.wrap("rerouteMktDataReq", [int, int, str], skip=1),
            92: self.wrap("rerouteMktDepthReq", [int, int, str], skip=1),
            93: self.marketRule,
            94: self.wrap("pnl", [int, float, float, float], skip=1),
            95: self.wrap(
                "pnlSingle", [int, float, float, float, float, float], skip=1
            ),
            96: self.historicalTicks,
            97: self.historicalTicksBidAsk,
            98: self.historicalTicksLast,
            99: self.tickByTick,
            100: self.wrap("orderBound", [int, int, int], skip=1),
            101: self.completedOrder,
            102: self.wrap("completedOrdersEnd", [], skip=1),
            103: self.wrap("replaceFAEnd", [int, str], skip=1),
            104: self.wrap("wshMetaData", [int, str], skip=1),
            105: self.wrap("wshEventData", [int, str], skip=1),
            106: self.historicalSchedule,
            107: self.wrap("userInfo", [int, str], skip=1),
        }

    def wrap(self, methodName, types, skip=2):
"""Create a message handler that invokes a wrapper method
with the in-order message fields as parameters, skipping over
the first ``skip`` fields, and parsed according to the ``types`` list.

Args::
    methodName: 
    types: 
    skip: (Default value = 2)"""
    skip: (Default value = 2)"""

        def handler(fields):
"""Args::
    fields:"""
"""Decode fields and invoke corresponding wrapper method.

Args::
    fields:"""
    fields:"""
        try:
            msgId = int(fields[0])
            handler = self.handlers[msgId]
            handler(fields)
        except Exception:
            self.logger.exception(f"Error handling fields: {fields}")

    def parse(self, obj):
"""Parse the object's properties according to its default types.

Args::
    obj:"""
    obj:"""
        for field in dataclasses.fields(obj):
            typ = type(field.default)
            if typ is str:
                continue
            v = getattr(obj, field.name)
            if typ is int:
                setattr(obj, field.name, int(v) if v else field.default)
            elif typ is float:
                setattr(obj, field.name, float(v) if v else field.default)
            elif typ is bool:
                setattr(obj, field.name, bool(int(v)) if v else field.default)

    def priceSizeTick(self, fields):
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
"""Args::
    fields:"""
    fields:"""
        (_, reqId, startDateTime, endDateTime, timeZone, count, *fields) = fields
        get = iter(fields).__next__
        sessions = [
            HistoricalSession(startDateTime=get(), endDateTime=get(), refDate=get())
            for _ in range(int(count))
        ]
        self.wrapper.historicalSchedule(
            int(reqId), startDateTime, endDateTime, timeZone, sessions
        )
