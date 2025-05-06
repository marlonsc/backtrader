# -*- coding: UTF-8 -*-

# import
import pandas as pd

# globals

# functions/classes

if __name__ == "__main__":
    # Example data: Create a DataFrame with OHLC data
    data = {
        "High": [1.2, 1.3, 1.4, 1.5, 1.3],
        "Low": [1.1, 1.2, 1.3, 1.4, 1.2],
        "Close": [1.15, 1.25, 1.35, 1.45, 1.25],
    }
    df = pd.DataFrame(data)

    # Calculation of True Range (TR)
    df["Prev Close"] = df["Close"].shift(1)  #
    df["High-Low"] = df["High"] - df["Low"]  # High - Low
    df["High-Prev Close"] = abs(df["High"] - df["Prev Close"])
    df["Low-Prev Close"] = abs(df["Low"] - df["Prev Close"])

    # True Range is the maximum of the above values
    df["True Range"] = df[["High-Low", "High-Prev Close", "Low-Prev Close"]].max(
        axis=1
    )  # Maximum of the three values per day

    # Calculation of Average True Range (ATR)
    period = 3  # Example period
    df["ATR"] = df["True Range"].rolling(window=period).mean()

    # Output of the DataFrame
    print(
        df[
            [
                "High",
                "Low",
                "Close",
                "Prev Close",
                "High-Low",
                "High-Prev Close",
                "Low-Prev Close",
                "True Range",
                "ATR",
            ]
        ]
    )
