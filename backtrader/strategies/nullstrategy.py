import logging

import backtrader as bt

_logger = logging.getLogger(__name__)


class NullStrategy(bt.Strategy):
    """Dummy strategy that does nothing. Really nothing."""
    pass
