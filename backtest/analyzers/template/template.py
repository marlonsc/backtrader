import backtrader as bt


# Community custom analyzer example: https://community.backtrader.com/topic/1274/closed-trade-list-including-mfe-mae-analyzer
# Create analyzer
class MyAnalyzer(bt.Analyzer):
    # Initialize parameters: such as those supported by built-in analyzers
    params = ((..., ...),)  # It is best not to delete the last comma!
    # Initialization function

    def __init__(self):
        """Initialize attributes, calculate indicators, etc."""
        pass

    # Analyzer, like strategy, starts running from bar 0
    # Both face the min_period issue
    # So both use prenext and nextstart to wait for min_period to be satisfied
    def start(self):
        pass

    def prenext(self):
        pass

    def nextstart(self):
        pass

    def next(self):
        pass

    def stop(self):
        # Generally, overall evaluation metrics for the strategy are calculated after it ends
        pass

    # Support information printing functions like strategy
    def notify_order(self, order):
        """Notify order information"""
        pass

    def notify_trade(self, trade):
        """Notify trade information"""
        pass

    def notify_cashvalue(self, cash, value):
        """Notify current cash and total asset value"""
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        """Return current cash, total asset value, fund value, and fund shares"""
        pass

    def get_analysis(self):
        pass
