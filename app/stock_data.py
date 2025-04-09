import os
import sqlite3
from datetime import datetime
import yfinance as yf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/V
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

TICKERS = ["AQ"]
SHARES_BY_TICKER={"AQ":1200002400}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            ticker TEXT,
            date TEXT,
            close_price REAL,
            volume INTEGER,
            market_cap REAL,
            pe_ratio REAL,
            source TEXT,
            PRIMARY KEY (ticker, date)
        )
    """)
    print("✅ stock_data table initialized.")
    conn.commit()
    conn.close()

def fetch_historical_data(ticker):
    yf_ticker = yf.Ticker(ticker + ".RO")
    hist = yf_ticker.history(period="max")

    if hist.empty:
        raise ValueError(f"No data returned for {ticker}")

    # Custom shares for AQ
    SHARES_BY_TICKER = {
        "AQ": 1200002400
        # Add more tickers later
    }

    shares_outstanding = SHARES_BY_TICKER.get(ticker.upper(), None)

    data_rows = []
    for date, row in hist.iterrows():
        close_price = row["Close"]
        market_cap = close_price * shares_outstanding if shares_outstanding else None

        data_rows.append({
            "ticker": ticker,
            "date": date.strftime('%Y-%m-%d'),
            "close_price": close_price,
            "volume": row["Volume"],
            "market_cap": market_cap,
            "pe_ratio": None,  # Not available historically
            "source": "yfinance"
        })

    return data_rows

def save_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO stock_data 
        (ticker, date, close_price, volume, market_cap, pe_ratio, source)
        VALUES (:ticker, :date, :close_price, :volume, :market_cap, :pe_ratio, :source)
    """, data)

    conn.commit()
    conn.close()

def run_update():
    print("📦 Updating stock_data...")
    init_db()

    for ticker in TICKERS:
        try:
            rows = fetch_historical_data(ticker)
            for data in rows:
                save_to_db(data)
            print(f"✅ Inserted {len(rows)} rows for {ticker}")
        except Exception as e:
            print(f"❌ Failed for {ticker}: {e}")

print(f"Using database at: {DB_PATH}")

if __name__ == "__main__":
    run_update()

