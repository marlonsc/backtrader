"""spread.py module.

Description of the module functionality."""

# -*- coding: utf-8; py-indent-offset:4 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from . import Indicator


class SpreadWithSignals(Indicator):
"""Calculate the price difference between two data sources and mark buy/sell signal points.
    
    Parameters:
    - data2: Second data source (used to calculate the price difference)
    - buy_signal: Buy signal array
    - sell_signal: Sell signal array"""
    """

    lines = ("spread",)  # Define a spread line
    alias = ("Spread",)
    plotinfo = dict(
        plot=True,
        subplot=True,  # Display in a separate subplot
        plotname="Spread",
        plotlabels=True,
        plotlinelabels=True,
        plotymargin=0.05,
    )

    plotlines = dict(spread=dict(_name="Spread", color="blue", ls="-", _plotskip=False))

    def __init__(self):
        """Initialize the SpreadWithSignals indicator."""
        super(SpreadWithSignals, self).__init__()

        # Calculate the price difference
        self.lines.spread = self.data - self.data1

        # Add buy/sell signal plotting
        self.plotinfo.plotmarkers = [
            dict(
                name="buy",
                marker="^",  # Up triangle
                color="g",  # Green
                markersize=8,
                fillstyle="full",
                text="buy %(price).2f",  # Label format
                textsize=8,
                textcolor="g",
                ls="",  # No line
                _plotskip=False,
            ),
            dict(
                name="sell",
                marker="v",  # Down triangle
                color="r",  # Red
                markersize=8,
                fillstyle="full",
                text="sell %(price).2f",  # Label format
                textsize=8,
                textcolor="r",
                ls="",  # No line
                _plotskip=False,
            ),
        ]
