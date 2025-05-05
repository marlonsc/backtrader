import pandas as pd
from pandas import Series


def calculate_true_range(high: Series, low: Series, close: Series) -> pd.DataFrame:
    """The calculate_true_range function calculates the True Range (TR) for a given
    set of high, low, and close prices.
    The True Range is a measure of market volatility and is used in the
    calculation of the Average True Range (ATR).
    The True Range is the maximum of the following three values:
    1. The difference between the current high and low prices.
    2. The absolute value of the difference between the current high and the
    previous close.
    3. The absolute value of the difference between the current low and the
    previous close.

    :param high:
    :type high: Series
    :param low:
    :type low: Series
    :param close:
    :type close: Series
    :rtype: pd.DataFrame

    """
    # Maximum difference between high and low prices
    tr1 = high - low
    # Absolute difference between high and the previous close
    tr2 = abs(high - close.shift(1))
    # Absolute difference between low and the previous close
    tr3 = abs(low - close.shift(1))

    # The True Range is the maximum of the three values for each day
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range


def calculate_atr(
    high: Series, low: Series, close: Series, period: int = 5
) -> pd.DataFrame:
    """Calculate the Average True Range (ATR) for a given set of high, low, and
    close prices over a specified period.

    :param high:
    :type high: Series
    :param low:
    :type low: Series
    :param close:
    :type close: Series
    :param period:  (Default value = 5)
    :type period: int
    :rtype: pd.DataFrame

    """
    true_range: pd.DataFrame = calculate_true_range(high, low, close)
    atr: pd.DataFrame = true_range.rolling(window=period).mean()
    return atr


# Example usage with a DataFrame containing 'High', 'Low', and 'Close' columns
data = pd.DataFrame(
    {
        "High": [127.01, 127.62, 126.59, 127.35, 128.17],
        "Low": [125.36, 126.56, 125.07, 126.32, 126.80],
        "Close": [126.00, 127.29, 126.00, 127.04, 127.88],
    }
)

atr = calculate_atr(data["High"], data["Low"], data["Close"], period=3)
print(atr)
