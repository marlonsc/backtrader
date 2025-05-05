#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2024 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from backtrader import Analyzer
from backtrader.utils import AutoDict, AutoOrderedDict
from backtrader.utils.py3 import MAXINT


class TradeAnalyzer(Analyzer):
    """Provides statistics on closed trades (keeps also the count of open ones)

      - Total Open/Closed Trades

      - Streak Won/Lost Current/Longest

      - ProfitAndLoss Total/Average

      - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Long/Short Count/ Total PNL / Average PNL / Max PNL

          - Won/Lost Count/ Total PNL/ Average PNL / Max PNL

      - Length (bars in the market)

        - Total/Average/Max/Min

        - Won/Lost Total/Average/Max/Min

        - Long/Short Total/Average/Max/Min

          - Won/Lost Total/Average/Max/Min

    Note:

      The analyzer uses an "auto"dict for the fields, which means that if no
      trades are executed, no statistics will be generated.

      In that case there will be a single field/subfield in the dictionary


    :returns: - dictname['total']['total'] which will have a value of 0 (the field is
          also reachable with dot notation dictname.total.total

    """

    def create_analysis(self):
        """ """
        self.rets = AutoOrderedDict(
            {
                "total": AutoOrderedDict({"total": 0, "open": 0, "closed": 0}),
                "streak": AutoOrderedDict(
                    {
                        "won": AutoOrderedDict({"current": 0, "longest": 0}),
                        "lost": AutoOrderedDict({"current": 0, "longest": 0}),
                    }
                ),
                "pnl": AutoOrderedDict(
                    {
                        "gross": AutoOrderedDict({"total": 0, "average": 0}),
                        "net": AutoOrderedDict({"total": 0, "average": 0}),
                    }
                ),
                "won": AutoOrderedDict(
                    {
                        "total": 0,
                        "pnl": AutoOrderedDict({"total": 0, "average": 0, "max": 0}),
                    }
                ),
                "lost": AutoOrderedDict(
                    {
                        "total": 0,
                        "pnl": AutoOrderedDict({"total": 0, "average": 0, "max": 0}),
                    }
                ),
                "long": AutoOrderedDict(
                    {
                        "total": 0,
                        "pnl": AutoOrderedDict(
                            {
                                "total": 0,
                                "average": 0,
                                "won": AutoOrderedDict(
                                    {"total": 0, "average": 0, "max": 0}
                                ),
                                "lost": AutoOrderedDict(
                                    {"total": 0, "average": 0, "max": 0}
                                ),
                            }
                        ),
                        "won": 0,
                        "lost": 0,
                    }
                ),
                "short": AutoOrderedDict(
                    {
                        "total": 0,
                        "pnl": AutoOrderedDict(
                            {
                                "total": 0,
                                "average": 0,
                                "won": AutoOrderedDict(
                                    {"total": 0, "average": 0, "max": 0}
                                ),
                                "lost": AutoOrderedDict(
                                    {"total": 0, "average": 0, "max": 0}
                                ),
                            }
                        ),
                        "won": 0,
                        "lost": 0,
                    }
                ),
                "len": AutoOrderedDict(
                    {
                        "total": 0,
                        "average": 0,
                        "max": 0,
                        "min": 0,
                        "won": AutoOrderedDict({"total": 0, "average": 0, "max": 0}),
                        "lost": AutoOrderedDict(
                            {"total": 0, "average": 0, "max": 0, "min": 0}
                        ),
                        "long": AutoOrderedDict(
                            {
                                "total": 0,
                                "average": 0,
                                "max": 0,
                                "min": 0,
                                "won": AutoOrderedDict(
                                    {
                                        "total": 0,
                                        "average": 0,
                                        "max": 0,
                                        "min": 0,
                                    }
                                ),
                                "lost": AutoOrderedDict(
                                    {
                                        "total": 0,
                                        "average": 0,
                                        "max": 0,
                                        "min": 0,
                                    }
                                ),
                            }
                        ),
                        "short": AutoOrderedDict(
                            {
                                "total": 0,
                                "average": 0.0,
                                "max": 0,
                                "min": 0,
                                "won": AutoOrderedDict(
                                    {
                                        "total": 0,
                                        "average": 0.0,
                                        "max": 0,
                                        "min": 0,
                                    }
                                ),
                                "lost": AutoOrderedDict(
                                    {
                                        "total": 0,
                                        "average": 0.0,
                                        "max": 0,
                                        "min": 0,
                                    }
                                ),
                            }
                        ),
                    }
                ),
            }
        )
        self.rets.total.total = 0

    def stop(self):
        """ """
        super(TradeAnalyzer, self).stop()
        self.rets._close()

    def notify_trade(self, trade):
        """

        :param trade:

        """
        if trade.justopened:
            # Trade just opened
            self.rets.total.total += 1
            self.rets.total.open += 1

        elif trade.status == trade.Closed:
            trades = self.rets

            res = AutoDict()
            # Trade just closed

            won = res.won = int(trade.pnlcomm >= 0.0)
            lost = res.lost = int(not won)
            tlong = res.tlong = trade.long
            tshort = res.tshort = not trade.long

            trades.total.open -= 1
            trades.total.closed += 1

            # Streak
            for wlname in ["won", "lost"]:
                wl = res[wlname]

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.total = round(trpnl.gross.total, 2)
            trpnl.gross.average = round(trades.pnl.gross.total / trades.total.closed, 2)
            trpnl.net.total += trade.pnlcomm
            trpnl.net.total = round(trpnl.net.total, 2)
            trpnl.net.average = round(trades.pnl.net.total / trades.total.closed, 2)

            # Won/Lost statistics
            for wlname in ["won", "lost"]:
                wl = res[wlname]
                trwl = trades[wlname]

                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.total = round(trwlpnl.total, 2)
                trwlpnl.average = round(trwlpnl.total / (trwl.total or 1.0), 2)

                wm = trwlpnl.max or 0.0
                func = max if wlname == "won" else min
                trwlpnl.max = round(func(wm, pnlcomm), 2)

            # Long/Short statistics
            for tname in ["long", "short"]:
                trls = trades[tname]
                ls = res["t" + tname]

                trls.total += ls  # long.total / short.total
                trls.total = round(trls.total, 2)
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.total = round(trls.pnl.total, 2)
                trls.pnl.average = round(trls.pnl.total / (trls.total or 1.0), 2)

                for wlname in ["won", "lost"]:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].total = round(trls.pnl[wlname].total, 2)
                    trls.pnl[wlname].average = round(
                        trls.pnl[wlname].total / (trls[wlname] or 1.0), 2
                    )

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == "won" else min
                    trls.pnl[wlname].max = round(func(wm, pnlcomm), 2)

            # Length
            trades.len.total += trade.barlen
            trades.len.average = round(trades.len.total / trades.total.closed, 6)
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or MAXINT
            trades.len.min = min(ml, trade.barlen)

            # Length Won/Lost
            for wlname in ["won", "lost"]:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen
                trwl.total = round(trwl.total, 6)
                trwl.average = round(trwl.total / (trades[wlname].total or 1.0), 6)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or MAXINT
                    trwl.min = round(min(m, trade.barlen * wl), 6)

            # Length Long/Short
            for lsname in ["long", "short"]:
                trls = trades.len[lsname]  # trades.len.long
                ls = res["t" + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                trls.total = round(trls.total, 6)
                total_ls = trades[lsname].total  # trades.long.total
                trls.average = round(trls.total / (total_ls or 1.0), 6)

                # max/min
                m = trls.max or 0
                trls.max = round(max(m, barlen), 6)
                m = trls.min or MAXINT
                trls.min = round(min(m, barlen or m), 6)

                for wlname in ["won", "lost"]:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total
                    trls_wl.total = round(trls_wl.total, 6)

                    trls_wl.average = round(
                        trls_wl.total / (trades[lsname][wlname] or 1.0), 6
                    )

                    # max/min
                    m = trls_wl.max or 0
                    trls_wl.max = round(max(m, barlen2), 6)
                    m = trls_wl.min or MAXINT
                    trls_wl.min = round(min(m, barlen2 or m), 6)
