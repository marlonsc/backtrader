import backtrader as bt

class SlippageImpactAnalyzer(bt.Analyzer):
    """
    Analyzer that measures the impact of slippage on trading performance metrics.
    """

    def __init__(self):
        self.orders = []
        # Get slippage percentage from broker
        self.slip_perc = self.strategy.broker.p.slip_perc

    def notify_order(self, order):
        if order.status == order.Completed:
            # Calculate slippage cost for this specific order
            # For buys, slippage increases cost; for sells, slippage decreases proceeds
            if order.isbuy():
                # Price without slippage would be lower
                price_wo_slip = order.executed.price / (1 + self.slip_perc)
                slip_cost = (order.executed.price - price_wo_slip) * abs(order.executed.size)
            else:  # sell
                # Price without slippage would be higher
                price_wo_slip = order.executed.price / (1 - self.slip_perc)
                slip_cost = (price_wo_slip - order.executed.price) * abs(order.executed.size)

            # Store executed order data
            self.orders.append({
                'dt': bt.num2date(order.executed.dt),
                'size': order.executed.size,
                'price': order.executed.price,
                'value': order.executed.value,
                'slip_cost': slip_cost,
                'data': order.data._name,
            })

    def stop(self):
        # Calculate total trading volume for reference
        self.total_traded_value = sum(abs(o['value']) for o in self.orders)

        # Calculate total slippage cost from individual orders
        self.total_slip_cost = sum(o['slip_cost'] for o in self.orders)

        # Get initial equity
        self.initial_equity = self.strategy.broker.startingcash

        # Get final value
        self.final_value = self.strategy.broker.getvalue()

        # Calculate actual return (with slippage)
        self.actual_return = (self.final_value / self.initial_equity) - 1

        # Calculate hypothetical return without slippage
        self.hypo_final = self.final_value + self.total_slip_cost
        self.hypo_return = (self.hypo_final / self.initial_equity) - 1

        # Calculate CAGR with and without slippage
        days = len(self.strategy)
        years = days / 252.0  # Assuming 252 trading days per year

        if years > 0:
            self.actual_cagr = (1 + self.actual_return) ** (1 / years) - 1
            self.hypo_cagr = (1 + self.hypo_return) ** (1 / years) - 1
        else:
            self.actual_cagr = self.actual_return
            self.hypo_cagr = self.hypo_return

    def get_analysis(self):
        return {
            'total_slip_cost': self.total_slip_cost,
            'slip_pct_initial_equity': (self.total_slip_cost / self.initial_equity) * 100,
            'actual_cagr': self.actual_cagr,
            'cagr_wo_slippage': self.hypo_cagr,
            'cagr_impact': self.hypo_cagr - self.actual_cagr
        }