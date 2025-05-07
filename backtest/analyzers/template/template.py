"""template.py module.

Description of the module functionality."""



# Community custom analyzer example: https://community.backtrader.com/topic/1274/closed-trade-list-including-mfe-mae-analyzer
# Create analyzer
class MyAnalyzer(bt.Analyzer):
""""""
        """Initialize attributes, calculate indicators, etc."""

    # Analyzer, like strategy, starts running from bar 0
    # Both face the min_period issue
    # So both use prenext and nextstart to wait for min_period to be satisfied
    def start(self):
""""""
""""""
""""""
""""""
""""""
"""Notify order information

Args::
    order:"""
    order:"""

    def notify_trade(self, trade):
"""Notify trade information

Args::
    trade:"""
    trade:"""

    def notify_cashvalue(self, cash, value):
"""Notify current cash and total asset value

Args::
    cash: 
    value:"""
    value:"""

    def notify_fund(self, cash, value, fundvalue, shares):
"""Args::
    cash: 
    value: 
    fundvalue: 
    shares:"""
    shares:"""

    def get_analysis(self):
""""""
