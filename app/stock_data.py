import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")              # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")      # Full path to database

TICKERS = ["AQ"]
SHARES_BY_TICKER = {"AQ": 1200002400}

# 🔗 Open one global connection (shared by all functions)
conn = sqlite3.connect(DB_PATH)

# 🔍 Get earnings release events
def get_events(ticker):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_date, period_start, period_end
        FROM company_events
        WHERE ticker = ? AND event_type = 'earnings_release'
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
        start = datetime.strptime(row[0], "%d/%m/%Y").strftime("%Y-%m-%d")
        end = datetime.strptime(row[1], "%d/%m/%Y").strftime("%Y-%m-%d")
        value = float(row[2].replace(",", ""))  # ✅ Clean commas
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
                WHERE ticker = ? AND date >= ? AND date < ?
            """, (eps, ticker, start_date, end_date))
        else:
            print(f"🟩 Updating EPS from {start_date} onward... EPS = {eps}")
            cursor.execute("""
                UPDATE stock_data
                SET eps_ttm = ?
                WHERE ticker = ? AND date >= ?
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
        WHERE ticker = ? AND eps_ttm IS NOT NULL AND eps_ttm != 0
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
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM stock_data", conn)["ticker"]

    for ticker in tickers:
        df = pd.read_sql(f"SELECT date, close_price FROM stock_data WHERE ticker = '{ticker}'", conn)
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
                WHERE ticker = ? AND date = ?
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
    ticker = "AQ"
    shares = SHARES_BY_TICKER[ticker]

    events = get_events(ticker)
    financials = get_financials(ticker)
    eps_timeline = build_eps_timeline(events, financials, shares)

    for eps in eps_timeline:
        print(f"📅 From {eps['from_date']}: EPS_TTM = {round(eps['eps_ttm'], 4)}")

    update_eps_in_stock_data(ticker, eps_timeline)
    update_variations()