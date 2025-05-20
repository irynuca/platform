import os
import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")              # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")      # Full path to database

TICKERS = ["AQ", "WINE"]
SHARES_BY_TICKER = {"AQ": 1200002400, "WINE":40426674}

# Create/ensure table exists (run once)
def initialize_stock_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS stock_data (
            company_ticker TEXT,
            date TEXT,
            close_price REAL,
            volume INTEGER,
            market_cap REAL,
            pe_ratio REAL,
            eps_ttm REAL,
            change_day REAL,
            change_yoy REAL,
            change_ytd REAL,
            source TEXT,
            PRIMARY KEY (company_ticker, date)
        )
        """)

# Fetch & store price history
# Uses yf.download to avoid hanging, with threads=False and progress=False
# Adds a timeout via yfinance internal session settings

def fetch_and_store_stock_data(ticker):
    shares_outstanding = SHARES_BY_TICKER.get(ticker)
    if not shares_outstanding:
        print(f"❌ Number of shares not defined for {ticker}")
        return

    print(f"📥 Fetching full history for {ticker}...")
    try:
        # Module-level download with no threading & no progress bar
        df = yf.download(
            tickers=f"{ticker}.RO", 
            period="max", 
            interval="1d", 
            progress=False, 
            threads=False,
            auto_adjust=True 
        )
    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")
        return

    if df.empty:
        print(f"❌ No price history available for {ticker}")
        return

    # Prepare DataFrame
    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns=df.columns.droplevel(0)
    df["date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df["close_price"] = df["Close"].astype(float).round(4)
    df["volume"] = df["Volume"].astype(int)
    df["market_cap"] = (df["close_price"] * shares_outstanding).astype(float)
    df["company_ticker"] = ticker
    df["source"] = "yfinance"

    # Select & add nullable columns
    cols = ["company_ticker", "date", "close_price", "volume", "market_cap", "source"]
    data = df[cols].copy()
    for col in ["pe_ratio", "eps_ttm", "change_day", "change_yoy", "change_ytd"]:
        data[col] = None

    # Insert into DB
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Bulk insert using executemany
        records = [tuple(row) for row in data.to_records(index=False)]
        placeholders = ",".join(["?" for _ in range(len(data.columns))])
        sql = f"""
            INSERT OR REPLACE INTO stock_data ({','.join(data.columns)})
            VALUES ({placeholders})
        """
        cursor.executemany(sql, records)
        conn.commit()

    print(f"✅ Stored {len(data)} rows for {ticker} into stock_data.")

# 🔍 Get earnings release events
def get_events(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_date, period_start, period_end
        FROM company_events
        WHERE company_ticker = ? AND event_type = 'earnings_release'
        ORDER BY event_date
    """, (ticker,))

    rows = cursor.fetchall()
    if not rows:
        print(f"⚠️ No matching events found for ticker '{ticker}'.")
        return []

    print(f"📊 Retrieved {len(rows)} events for {ticker}:")  
    for row in rows:
        print(f"   ▶ Earnings release: {row[0]} for period {row[1]} to {row[2]}")

    return [{"event_date": row[0], "period_start": row[1], "period_end": row[2]} for row in rows]

# 🔍 Get net profit values
def get_financials(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT period_start, period_end, value
        FROM financial_data
        WHERE company_ticker = ? AND metric_name_ro = 'Profitul atribuibil actionarilor Grupului'
          AND aggr_type = 'cml'
    """, (ticker,))
    
    rows = cursor.fetchall()
    if not rows:
        print(f"⚠️ No matching financial data found for ticker '{ticker}'.")
        return {}

    print(f"📈 Retrieved {len(rows)} financial entries for {ticker}:")
    financials = {}
    for row in rows:
        start = pd.to_datetime(row[0]).strftime("%Y-%m-%d")
        end = pd.to_datetime(row[1]).strftime("%Y-%m-%d")
        value = float(row[2])
        financials[(start, end)] = value
        print(f"   ▶ ({start}, {end}) = {value}")


    return financials

# 🔧 Build EPS timeline from earnings events and net profits
def build_eps_timeline(events, financials, shares):
    eps_timeline = []

    for event in events:
        per_end = event["period_end"]
        per_end_date = datetime.strptime(event["period_end"], "%Y-%m-%d")  # ✅ ISO parsing
        per_year = per_end_date.year
        per_end_iso = per_end_date.strftime("%Y-%m-%d")  # '2024-09-30'

        lookup_key = (f"{per_year}-01-01", per_end_iso)
        print(f"🔍 Looking for key: {lookup_key}")
        print("🔑 Available keys in financials:")
        for key in financials.keys():
            print("   ", key)

        nine_m_curr = financials.get(lookup_key)
        print("➡️ nine_m_curr:", nine_m_curr)

        nine_m_prev = financials.get((f"{per_year-1}-01-01", f"{per_year-1}-09-30"))
        fy_prev = financials.get((f"{per_year-1}-01-01", f"{per_year-1}-12-31"))

        if None in (nine_m_curr, nine_m_prev, fy_prev):
            print(f"⚠️ Missing financial data for event on {event['event_date']} — skipping.")
            continue

        q4_prev = fy_prev - nine_m_prev
        net_profit_ttm = nine_m_curr + q4_prev
        eps_ttm = net_profit_ttm / shares

        eps_timeline.append({
            "from_date": event["event_date"],
            "eps_ttm": eps_ttm
        })
    print(eps_timeline)
    print(f"✅ Built EPS timeline with {len(eps_timeline)} entries.")
    return eps_timeline


def update_eps_in_stock_data(ticker, eps_timeline):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for i in range(len(eps_timeline)):
        start_date = eps_timeline[i]["from_date"]
        end_date = eps_timeline[i + 1]["from_date"] if i + 1 < len(eps_timeline) else None
        eps = eps_timeline[i]["eps_ttm"]

        if end_date:
            print(f"🟦 Updating EPS from {start_date} to {end_date} (excluding)... EPS = {eps}")
            cursor.execute("""
                UPDATE stock_data
                SET eps_ttm = ?
                WHERE company_ticker = ? AND date >= ? AND date < ?
            """, (eps, ticker, start_date, end_date))
        else:
            print(f"🟩 Updating EPS from {start_date} onward... EPS = {eps}")
            cursor.execute("""
                UPDATE stock_data
                SET eps_ttm = ?
                WHERE company_ticker = ? AND date >= ?
            """, (eps, ticker, start_date))

    conn.commit()
    conn.close()
    print("✅ EPS values updated in stock_data.")

def update_pe_ratio(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🔄 Updating P/E ratio for {ticker}...")

    # Only update where eps_ttm is valid (non-null and non-zero)
    cursor.execute("""
        UPDATE stock_data
        SET pe_ratio = close_price / eps_ttm
        WHERE company_ticker = ? AND eps_ttm IS NOT NULL AND eps_ttm != 0
    """, (ticker,))

    conn.commit()
    conn.close()

    print("✅ P/E ratio updated in stock_data.")

def compute_yoy(df, current_date, current_price, threshold_days=5):
    one_year_ago = current_date - timedelta(days=365)
    df["delta"] = (df["date"] - one_year_ago).abs()
    closest_row = df.loc[df["delta"].idxmin()]
    
    if closest_row["delta"].days > threshold_days:
        return None  # Too far, don't compute

    prev_price = closest_row["close_price"]
    return ((current_price - prev_price) / prev_price) * 100 if prev_price else None


def compute_ytd(df, current_date, current_price, threshold_days=5):
    jan_first = datetime(current_date.year, 1, 1)
    df["delta"] = (df["date"] - jan_first).abs()
    closest_row = df.loc[df["delta"].idxmin()]
    
    if closest_row["delta"].days > threshold_days:
        return None  # Too far from Jan 1

    base_price = closest_row["close_price"]
    return ((current_price - base_price) / base_price) * 100 if base_price else None


def update_variations():
    conn = sqlite3.connect(DB_PATH)
    tickers = pd.read_sql("SELECT DISTINCT company_ticker FROM stock_data", conn)["company_ticker"]

    for ticker in tickers:
        df = pd.read_sql(f"SELECT date, close_price FROM stock_data WHERE company_ticker = '{ticker}'", conn)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        df["change_day"] = df["close_price"].pct_change() * 100

        df["change_yoy"] = df.apply(lambda row: compute_yoy(df, row["date"], row["close_price"]), axis=1)
        df["change_ytd"] = df.apply(lambda row: compute_ytd(df, row["date"], row["close_price"]), axis=1)

        # Update the table row-by-row
        for _, row in df.iterrows():
            update_query = """
                UPDATE stock_data 
                SET change_day = ?, change_yoy = ?, change_ytd = ?
                WHERE company_ticker = ? AND date = ?
            """
            conn.execute(update_query, (
                round(row["change_day"], 2) if not pd.isna(row["change_day"]) else None,
                round(row["change_yoy"], 2) if not pd.isna(row["change_yoy"]) else None,
                round(row["change_ytd"], 2) if not pd.isna(row["change_ytd"]) else None,
                ticker,
                row["date"].strftime("%Y-%m-%d")
            ))

        conn.commit()
        print(f"✅ Updated {ticker}")

    conn.close()


if __name__ == "__main__":
    
    initialize_stock_table()
    # Fetch historical price & volume data and populate stock_data table
    for ticker in TICKERS:
        fetch_and_store_stock_data(ticker)

        # Get earnings events and financial results
        events = get_events(ticker)
        financials = get_financials(ticker)

        shares = SHARES_BY_TICKER[ticker]
        # Compute EPS timeline
        eps_timeline = build_eps_timeline(events, financials, shares)

        for eps in eps_timeline:
            print(f"📅 From {eps['from_date']}: EPS_TTM = {round(eps['eps_ttm'], 4)}")

        # Update stock_data with EPS values and then compute ratios
        update_eps_in_stock_data(ticker, eps_timeline)
        update_pe_ratio(ticker)
        update_variations()