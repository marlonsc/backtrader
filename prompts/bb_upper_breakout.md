You are a professional PineScript v6 developer and an expert Python developer with experience with Backtrader framework.
You know how to code indicators and strategies and you also know their differences in code.
I need your help to turn a TradingView strategy into a Backtrader strategy please.

When to buy and when to sell:
- Go long when price closes above the upper Bollinger Band.
- Close long when price closed below the lower Bollinger Band.

Respect these instructions:
- Convert all TradeView code into Backtrader code. Don't use any code that a Backtrader Strategy won't support.  Use native Backtrader functions and calculations where possible.
- Do not hardcode any values into the script, the script will need to work for different stock symbols and different date ranges, the implementation should function based on dynamic data from the parameters that are passed to the script. 
- Preserve the timeframe logic if there is one. Fill gaps.
- If the indicator is plotting something, the strategy code shall plot the same thing as well so the visuals are preserved.
- Don't trigger a short. Simply go Long and Flat.
- Always use 100% of capital.
- Set commission to 0.1%.
- Set slippage to 0.
- Only update the trading logic of this script to exactly match the PineScript code provided.  Keep utility functions that include performance reporting, database connection, and anything that is unrelated to the logic or the performance of the strategy.
- Leave all other strategy settings to default values (aka. don't set them at all).
- Never use lookahead_on because that’s cheating. 
- The settings represented in the PineScript code should be the default parameters, but we should be able to set this similar to the existing script.
- Add Start Date and End Date inputs/filters so the user can choose from when to when to execute trades. Start with 1st January 2024 and go to 31st December 2024.
- When you are finished, the Python Backtrader script should perform exactly the same as the PineScript script does in Backtrader.
- Ensure everything has verbose documentation and the help parameter option.

Here is the PineScript that you should translate to the Python Backtrader code:

//@version=5
strategy(title="Demo GPT - Bollinger Bands Strategy", overlay=true, process_orders_on_close=true, default_qty_type=strategy.percent_of_equity, default_qty_value=100, commission_type=strategy.commission.percent, commission_value=0.1)

// Inputs
length = input.int(20, minval=1)
maType = input.string("SMA", "Basis MA Type", options = ["SMA", "EMA", "SMMA (RMA)", "WMA", "VWMA"])
src = input(close, title="Source")
mult = input.float(2.0, minval=0.001, maxval=50, title="StdDev")
offset = input.int(0, "Offset", minval = -500, maxval = 500, display = display.data_window)

// Moving Average Function
ma(source, length, _type) =>
    switch _type
        "SMA" => ta.sma(source, length)
        "EMA" => ta.ema(source, length)
        "SMMA (RMA)" => ta.rma(source, length)
        "WMA" => ta.wma(source, length)
        "VWMA" => ta.vwma(source, length)

// Calculate Bollinger Bands
basis = ma(src, length, maType)
dev = mult * ta.stdev(src, length)
upper = basis + dev
lower = basis - dev

// Plotting
plot(basis, "Basis", color=#2962FF, offset = offset)
p1 = plot(upper, "Upper", color=#F23645, offset = offset)
p2 = plot(lower, "Lower", color=#089981, offset = offset)
fill(p1, p2, title = "Background", color=color.rgb(33, 150, 243, 95))

// Date Range Inputs
start_year = input.int(2018, "Start Year")
start_month = input.int(1, "Start Month")
start_day = input.int(1, "Start Day")
end_year = input.int(2069, "End Year")
end_month = input.int(12, "End Month")
end_day = input.int(31, "End Day")

// Calculate Timestamps
start_timestamp = timestamp(start_year, start_month, start_day, 0, 0)
end_timestamp = timestamp(end_year, end_month, end_day, 23, 59)

// Check if current bar is within the date range
in_date_range = time >= start_timestamp and time <= end_timestamp

// Trading Logic
if in_date_range and src > upper
    strategy.entry("Long", strategy.long)

if in_date_range and src < lower
    strategy.close("Long")


