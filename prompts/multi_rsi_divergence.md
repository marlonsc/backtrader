TODO


//@version=5
indicator(title="Multiple RSI Divergence", overlay=false)

// RSI Inputs
short_rsi_length = input.int(7, title="Short RSI Length")
medium_rsi_length = input.int(14, title="Medium RSI Length")
long_rsi_length = input.int(21, title="Long RSI Length")

// RSI Calculations
short_rsi = ta.rsi(close, short_rsi_length)
medium_rsi = ta.rsi(close, medium_rsi_length)
long_rsi = ta.rsi(close, long_rsi_length)

// RSI Moving Averages (Smoothing)
short_rsi_ma = ta.ema(short_rsi, 5)
medium_rsi_ma = ta.ema(medium_rsi, 5)
long_rsi_ma = ta.sma(long_rsi, 5)

// Detect Divergences
bullish_divergence = ta.lowest(close, 10) < ta.lowest(close, 20) and short_rsi > short_rsi[1]
bearish_divergence = ta.highest(close, 10) > ta.highest(close, 20) and short_rsi < short_rsi[1]

// Plot RSIs
plot(short_rsi, title="Short RSI", color=color.blue)
plot(medium_rsi, title="Medium RSI", color=color.green)
plot(long_rsi, title="Long RSI", color=color.red)

// Plot Moving Averages for RSI
plot(short_rsi_ma, title="Short RSI MA", color=color.blue, style=plot.style_stepline)
plot(medium_rsi_ma, title="Medium RSI MA", color=color.green, style=plot.style_stepline)
plot(long_rsi_ma, title="Long RSI MA", color=color.red, style=plot.style_stepline)

// Highlight Divergences
plotshape(bullish_divergence, location=location.bottom, color=color.green, style=shape.labelup, title="Bullish Divergence")
plotshape(bearish_divergence, location=location.top, color=color.red, style=shape.labeldown, title="Bearish Divergence")

