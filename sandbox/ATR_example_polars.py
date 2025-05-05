import polars as pl
from polars import Series as plSeries
from icecream import ic


def calculate_true_range(high: plSeries, low: plSeries, close: plSeries) -> plSeries:
    """
    The calculate_true_range function calculates the True Range (TR) for a given
    set of high, low, and close prices.
    The True Range is a measure of market volatility and is used in the
    calculation of the Average True Range (ATR).
    The True Range is the maximum of the following three values:
    1. The difference between the current high and low prices.
    2. The absolute value of the difference between the current high and the
    previous close.
    3. The absolute value of the difference between the current low and the
    previous close.
    """
    # Maximum difference between high and low prices
    tr1 = high - low
    # Absolute difference between high and the previous close
    tr2 = (high - close.shift(1)).abs()
    # Absolute difference between low and the previous close
    tr3 = (low - close.shift(1)).abs()

    # The True Range is the maximum of the three values for each day
    # First create a DataFrame with the three true range values as columns
    true_range_base = pl.DataFrame(
        {"high-low": tr1, "high-close": tr2, "low-close": tr3}
    )
    ic(true_range_base)
    # Select the maximum value for each row over the three columns
    # This will give us the True Range for each day
    tr_max = true_range_base.select(
        pl.max_horizontal(["high-low", "high-close", "low-close"]).alias("true_range")
    )
    ic(tr_max)
    return tr_max


def calculate_atr(
    high: plSeries, low: plSeries, close: plSeries, period: int = 5
) -> plSeries:
    """
    Calculate the Average True Range (ATR) for a given set of high, low, and
    close prices over a specified period.
    """
    true_range: plSeries = calculate_true_range(high, low, close)
    atr = true_range.select(
        pl.col("true_range").rolling_mean(window_size=period).alias("ATR")
    )
    return atr


# Example usage with a DataFrame containing 'High', 'Low', and 'Close' columns
data = pl.DataFrame({
    "High": [127.01, 127.62, 126.59, 127.35, 128.17],
    "Low": [125.36, 126.56, 125.07, 126.32, 126.80],
    "Close": [126.00, 127.29, 126.00, 127.04, 127.88],
})

atr = calculate_atr(data["High"], data["Low"], data["Close"], period=3)
print(atr)
