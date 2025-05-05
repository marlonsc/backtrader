import argparse
import os

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor


def main(symbol, fromdate, todate, output_dir=None):
    """

    :param symbol:
    :param fromdate:
    :param todate:
    :param output_dir: (Default value = None)

    """
    # Database connection parameters
    db_params = {
        "dbname": "market_data",
        "user": "jason",
        "password": "fsck",
        "host": "localhost",
    }

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**db_params)

        # Use RealDictCursor to get column names
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Create parameterized query to prevent SQL injection
        query = """
        SELECT * FROM stock_price_data
        WHERE symbol = %s
        AND date >= %s
        AND date <= %s
        ORDER BY date ASC;
        """

        # Execute query with parameters
        cursor.execute(query, (symbol, fromdate, todate))

        # Fetch all results
        results = cursor.fetchall()

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        if df.empty:
            print(f"No data found for {symbol} between {fromdate} and {todate}")
            return

        # Determine output directory
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs",
            )

        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Output file path
        output_file = os.path.join(output_dir, f"{symbol}.csv")

        # Dump the DataFrame to a CSV file
        df.to_csv(output_file, index=False)
        print(f"Data exported to {output_file}")
        print(f"Retrieved {len(df)} records for {symbol}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close cursor and connection
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Dump stock price data to CSV.")
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Stock symbol to dump data for (e.g., TSLA)",
    )
    parser.add_argument(
        "--fromdate",
        type=str,
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--todate",
        type=str,
        required=True,
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (defaults to logs directory)",
    )

    args = parser.parse_args()

    # Call the main function with the provided parameters
    main(args.data, args.fromdate, args.todate, args.output)
