"""slippage_impact.py module.

Description of the module functionality."""



class SlippageImpactAnalyzer(bt.Analyzer):
    """Analyzer that measures the impact of slippage on trading performance metrics."""

    def __init__(self):
""""""
"""Args::
    order:"""
""""""
""""""
        return {
            "total_slip_cost": self.total_slip_cost,
            "slip_pct_initial_equity": (
                (self.total_slip_cost / self.initial_equity) * 100
            ),
            "actual_cagr": self.actual_cagr,
            "cagr_wo_slippage": self.hypo_cagr,
            "cagr_impact": self.hypo_cagr - self.actual_cagr,
        }
