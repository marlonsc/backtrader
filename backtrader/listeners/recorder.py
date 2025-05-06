"""recorder.py module.

Description of the module functionality."""

import logging
from typing import Optional

import backtrader as bt
from backtrader.listener import ListenerBase

_logger = logging.getLogger(__name__)


class RecorderListener(ListenerBase):
""""""
""""""
"""Args::
    cerebro:"""
"""Args::
    name: 
    snapshot:"""
    snapshot:"""
        line = snapshot["array"]
        if name == "datetime":
            line = [bt.num2date(x) for x in line]
        _logger.debug(
            f"Line '{name:20}' idx: {snapshot['idx']} - lencount:"
            f" {snapshot['lencount']} - {list(reversed(line))}"
        )

    @staticmethod
    def print_next(idx, next):
"""Args::
    idx: 
    next:"""
    next:"""
        _logger.debug(f"--- Next: {next['prenext']} - #{idx}")
        RecorderListener.print_line_snapshot("datetime", next["strategy"]["datetime"])

        for di, data in enumerate(next["datas"]):
            _logger.debug(f"\t--- Data {di}")
            for k, v in data[1].items():
                RecorderListener.print_line_snapshot(k, v)

        for oi, obs in enumerate(next["observers"]):
            _logger.debug(f"\t--- Obvserver {oi}")
            for k, v in obs[1].items():
                RecorderListener.print_line_snapshot(k, v)

        for ii, ind in enumerate(next["indicators"]):
            _logger.debug(f"\t--- Indicators {ii}")
            for k, v in ind[1].items():
                RecorderListener.print_line_snapshot(k, v)

    @staticmethod
    def print_nexts(nexts):
"""Args::
    nexts:"""
"""Args::
    data:"""
"""Args::
    strat: 
    is_prenext: (Default value = False)"""
    is_prenext: (Default value = False)"""
        curbars = []
        for i, d in enumerate(strat.datas):
            curbars.append((d._name, self._copy_lines(d)))

        oblines = []
        for obs in strat.getobservers():
            oblines.append((obs.__class__, self._copy_lines(obs)))

        indlines = []
        for ind in strat.getindicators():
            indlines.append((ind.__class__, self._copy_lines(ind)))

        self.nexts.append(
            {
                "prenext": is_prenext,
                "strategy": self._copy_lines(strat),
                "datas": curbars,
                "observers": oblines,
                "indicators": indlines,
            }
        )

        _logger.info("------------------- next")
        self.print_next(len(strat), self.nexts[-1])
        _logger.info("------------------- next-end")

    def next(self):
""""""
        for s in self._cerebro.runningstrats:
            # minper = s._getminperstatus()
            # if minper > 0:
            #    continue
            self._record_data(s)
