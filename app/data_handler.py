import yfinance as yf
import pandas as pd
import sqlite3
import os
import plotly.graph_objects as go
from datetime import datetime
import json
import re
from collections import OrderedDict
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
COMPANY_INFO_FILE = os.path.join(DATA_DIR, "company_info.csv")  # Full path to CSV
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

import time

def fetch_with_retry(ticker, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return yf.Ticker(ticker)
        except Exception as e:
            print(f"Retry {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception("Yahoo Finance API failed after multiple retries.")


def get_yahoo_stock_price(ticker):
    stock = fetch_with_retry(ticker + ".RO")
    info = stock.info

    if not info:
        return{"error":f"Stock data not found for {ticker}"}
    
    company_name = info.get("longName") or info.get("shortName") or ticker

    # Get business description from local file
    txt_filename = f"{ticker.upper()}_about_ro.txt"
    txt_path = os.path.join("C:/Users/irina/Project Element/Data source", ticker.upper(), txt_filename)
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            business_description = f.read().strip()
    except FileNotFoundError:
        business_description = "Descrierea companiei nu este disponibilă (fișierul local lipsește)."

    stock_data = {
        "company_name": company_name,
        "last_price": info.get("regularMarketPrice", "N/A"),
        "price_variation": round(info.get("regularMarketChangePercent", 0), 2) if "regularMarketChangePercent" in info else "N/A",
        "market_cap": f"{round(info.get('marketCap', 0) / 1e9, 2)}md RON" if "marketCap" in info else "N/A",
        "industry": info.get("industry", "N/A"),
        "net_income": f"{round(info.get('netIncomeToCommon', 0) / 1e9, 2)}md RON" if "netIncomeToCommon" in info else "N/A",
        "pe_ratio": f"{round(info.get('trailingPE', 0), 2)}x" if "trailingPE" in info else "N/A",
        "next_earnings_date": datetime.utcfromtimestamp(info["earningsTimestamp"]).strftime('%Y-%m-%d') if "earningsTimestamp" in info and isinstance(info["earningsTimestamp"], (int, float)) else "N/A",
        "longBusinessSummary": business_description
    }

    return stock_data

def get_company_info(ticker):
    """
    Fetch company details (Name, Sector, Market Cap, etc.) from company_info.csv.
    """
    if not os.path.exists(COMPANY_INFO_FILE):
        print(f"❌ ERROR: CSV file not found at {COMPANY_INFO_FILE}")  # Show exact path
        return None

    df = pd.read_csv(COMPANY_INFO_FILE)

    # Convert tickers to uppercase to avoid case-sensitivity issues
    df["ticker"] = df["ticker"].str.upper()

    # Find the stock in the dataframe
    company_data = df[df["ticker"] == ticker.upper()].to_dict(orient="records")

    return company_data[0] if company_data else None  # Return first match or None

def get_stock_data(ticker):
    """
    Combine Yahoo price data with company fundamentals.
    """
    company_info = get_company_info(ticker)
    yahoo_data = get_yahoo_stock_price(ticker)

    if not company_info:
        print(f"Error: Ticker {ticker} not found in CSV")
        return None  # Return None if company is not found

    return {**company_info, **yahoo_data}  # Merge company info & price data

def get_historical_stock_data(ticker, period="1mo", interval="1d"):
    stock=fetch_with_retry(ticker + ".RO")
    # Adjust interval depending on the period
    if period in ["1d", "5d"]:
        interval = "30m"
    elif period in ["1mo", "3mo"]:
        interval = "1d"
    elif period == "1y":
        interval = "1wk"
    elif period in ["5y", "max"]:
        interval = "1mo"
    history=stock.history(period=period, interval=interval, prepost=False, actions=False)
    if history.empty:
        return None
    
    stock_data={
        "dates":history.index.strftime("%Y-%m-%d").tolist(),
        "prices":history["Close"].tolist()
    }

    return stock_data

DB_PATH = "c:\\Irina\\Mosaiq8\\app\\data\\financials.db"

def get_financial_statement(ticker, statement_name, period_type, aggr_type):
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        m.id AS metric_id, 
        m.metric_name_ro AS metric_name, 
        f.value, 
        f.period_end
    FROM financial_data f
    JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
    WHERE f.company_ticker = ?
    AND f.statement_name = ?
    AND f.period_type = ?
    AND f.aggr_type = ?
    ORDER BY m.id ASC, f.period_end ASC
    """
    params = [ticker, statement_name, period_type, aggr_type]
    
    print("👉 Query Parameters:", params)
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        print(f"⚠️ No data found for {ticker} ({statement_name}, {period_type}, {aggr_type})")
        return []

    # Convert period_end to datetime for sorting
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce", dayfirst=True)
    df = df.sort_values(by=["metric_id", "period_end"], ascending=[True, True])

    # Pivot: metric_id as rows, period_end as columns
    df_pivot = df.pivot(index="metric_id", columns="period_end", values="value")

    # Convert pivoted columns to string format ("YYYY-MM-DD")
    df_pivot.columns = pd.to_datetime(df_pivot.columns).strftime("%d-%m-%Y")

    # Merge metric_name, keep metric_id for final sorting
    df_pivot = df_pivot.merge(
        df[['metric_id', 'metric_name']].drop_duplicates(),
        on="metric_id"
    ).set_index("metric_id")

    # Convert columns to string for JSON
    df_pivot.columns = [str(col) for col in df_pivot.columns]

    # Build a list of rows to preserve order
    final_list = []
    for metric_id in df_pivot.index:
        row = df_pivot.loc[metric_id]

        # metric_name is a single value, the rest are actual periods
        metric_name = row["metric_name"]
        
        # Remove "metric_name" so we only have date columns left
        row_data = row.drop(labels=["metric_name"]).dropna()

        # Build an ordered dictionary of period → value
        sorted_periods = sorted(row_data.index, key=lambda x: datetime.strptime(x,"%d-%m-%Y"))
        period_values = OrderedDict()
        for period_col in sorted_periods:
            period_values[period_col] = str(row_data[period_col])  # Convert to string if needed

        final_list.append({
            "metric_id": metric_id,
            "metric_name": metric_name,
            "values": period_values
        })

    # Debugging
    print("\n✅ Final List Output:")
    print(json.dumps(final_list, indent=4, ensure_ascii=False))

    return final_list


def get_financial_statement(ticker, statement_name, period_type, aggr_type):
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        m.id AS metric_id, 
        m.metric_name_ro AS metric_name, 
        f.value, 
        f.period_end
    FROM financial_data f
    JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
    WHERE f.company_ticker = ?
    AND f.statement_name = ?
    AND f.period_type = ?
    AND f.aggr_type = ?
    ORDER BY m.id ASC, f.period_end ASC
    """
    params = [ticker, statement_name, period_type, aggr_type]
    
    print("👉 Query Parameters:", params)
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        print(f"⚠️ No data found for {ticker} ({statement_name}, {period_type}, {aggr_type})")
        return []

    # Convert period_end to datetime for sorting
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce", dayfirst=True)
    df = df.sort_values(by=["metric_id", "period_end"], ascending=[True, True])

    # Pivot: metric_id as rows, period_end as columns
    df_pivot = df.pivot(index="metric_id", columns="period_end", values="value")

    # Convert pivoted columns to string format ("YYYY-MM-DD")
    df_pivot.columns = pd.to_datetime(df_pivot.columns).strftime("%d-%m-%Y")

    # Merge metric_name, keep metric_id for final sorting
    df_pivot = df_pivot.merge(
        df[['metric_id', 'metric_name']].drop_duplicates(),
        on="metric_id"
    ).set_index("metric_id")

    # Convert columns to string for JSON
    df_pivot.columns = [str(col) for col in df_pivot.columns]

    # Build a list of rows to preserve order
    final_list = []
    for metric_id in df_pivot.index:
        row = df_pivot.loc[metric_id]

        # metric_name is a single value, the rest are actual periods
        metric_name = row["metric_name"]
        
        # Remove "metric_name" so we only have date columns left
        row_data = row.drop(labels=["metric_name"]).dropna()

        # Build an ordered dictionary of period → value
        sorted_periods = sorted(row_data.index, key=lambda x: datetime.strptime(x,"%d-%m-%Y"))
        period_values = OrderedDict()
        for period_col in sorted_periods:
            period_values[period_col] = str(row_data[period_col])  # Convert to string if needed

        final_list.append({
            "metric_id": metric_id,
            "metric_name": metric_name,
            "values": period_values
        })

    # Debugging
    print("\n✅ Final List Output:")
    print(json.dumps(final_list, indent=4, ensure_ascii=False))

    return final_list


def get_grouped_financial_ratios(ticker, period_type, aggr_type):
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT 
        ratio_name_ro AS ratio_name,
        value,
        category, 
        period_end
    FROM financial_ratios
    WHERE company_ticker = ?
    AND period_type = ?
    AND aggr_type = ?
    AND category IN ("Profitabilitate", "Indatorare")
    ORDER BY category ASC, ratio_name ASC, period_end ASC
    """
    params = [ticker, period_type, aggr_type]

    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"❌ Database Error (ratios): {e}")
        return {}
    finally:
        conn.close()

    if df.empty:
        return {}

    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")
    df = df.sort_values(by=["category", "ratio_name", "period_end"])

    df_pivot = df.pivot(index=["category", "ratio_name"], columns="period_end", values="value")
    df_pivot.columns = pd.to_datetime(df_pivot.columns).strftime("%d-%m-%Y")

    from collections import OrderedDict

    grouped = defaultdict(list)
    for (category, ratio_name), row in df_pivot.iterrows():
        row_data = row.dropna()
        sorted_periods = sorted(row_data.index, key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
        values = OrderedDict((p, str(row_data[p])) for p in sorted_periods)

        grouped[category].append({
            "metric_name": ratio_name,
            "values": values
        })

    return grouped

def get_revenue_data(ticker, period_type="annual", aggr_type="cml"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.period_end, f.value
        FROM financial_data f
        JOIN financial_metrics m ON f.metric_name_ro = m.generalized_metric_ro
        WHERE f.company_ticker = ?
          AND f.period_type = ?
          AND f.aggr_type = ?
          AND m.generalized_metric_ro = 'Venituri'
        ORDER BY f.period_end ASC
    """, (ticker, period_type, aggr_type))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    # Format results
    # Clean and format values
    revenue_data = {
        "periods": [pd.to_datetime(row[0], dayfirst=True).strftime("%d/%m/%Y") for row in rows],
        "values": [float(str(row[1]).replace(",", "").replace(" ", "")) for row in rows if row[1] is not None]
    }

    return revenue_data

def get_segment_revenue_notes(ticker):
    """
    Fetch revenue note elements for the most recent period using Python-side date parsing.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Get all periods for this ticker with revenue notes
    all_periods_query = """
        SELECT DISTINCT period_end
        FROM notes
        WHERE company_ticker = ?
        AND note_type = 'revenue'
    """
    cursor.execute(all_periods_query, (ticker,))
    periods = cursor.fetchall()

    if not periods:
        conn.close()
        return []

    # Step 2: Parse to datetime and find the latest
    try:
        latest_period = max(
            (datetime.strptime(p[0], "%d/%m/%Y") for p in periods),
            default=None
        ).strftime("%d/%m/%Y")
    except Exception as e:
        print(f"❌ Date parsing error: {e}")
        conn.close()
        return []

    # Step 3: Now fetch note elements for that latest period
    notes_query = """
        SELECT note_element, value
        FROM notes
        WHERE company_ticker = ?
        AND note_type = 'revenue'
        AND period_end = ?
        ORDER BY line_order ASC
    """
    cursor.execute(notes_query, (ticker, latest_period))
    rows = cursor.fetchall()
    conn.close()

    segment_data = [{"label": note_element, "value": value} for note_element, value in rows]

    return {
    "period": latest_period,
    "data": segment_data}


def get_profit_and_margin_data(ticker, period_type="annual", aggr_type="cml"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- 1. Fetch Profit net a.m. using JOIN on generalized_metric_ro ---
    cursor.execute("""
        SELECT f.period_end, f.value
        FROM financial_data f
        JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro AND f.company_ticker = m.company_ticker 
        WHERE f.company_ticker = ?
          AND f.period_type = ?
          AND f.aggr_type = ?
          AND m.generalized_metric_ro = 'Profit net a.m.'
        ORDER BY f.period_end ASC
    """, (ticker, period_type, aggr_type))

    profit_data = cursor.fetchall()

    print("date despre profit:", profit_data)
    # --- 2. Fetch Net Profit Margin from financial_ratios ---
    cursor.execute("""
        SELECT period_end, value
        FROM financial_ratios
        WHERE company_ticker = ?
          AND period_type = ?
          AND aggr_type = ?
          AND ratio_name_ro = 'Marja neta a profitului'
        ORDER BY period_end ASC
    """, (ticker, period_type, aggr_type))

    margin_data = cursor.fetchall()
    print("marja net:", margin_data)
    conn.close()

    # Normalize and align by period_end
    profit_dict = {row[0]: row[1] for row in profit_data}
    margin_dict = {row[0]: row[1] for row in margin_data}

    # Use intersection of periods
    common_periods = sorted(set(profit_dict.keys()) & set(margin_dict.keys()))

    if not common_periods:
        return None

    labels = [pd.strftime("%d/%m/%Y") if hasattr(pd, 'strftime') else pd for pd in common_periods]
    profit_values = [float(str(profit_dict[per]).replace(",", "").replace(" ", "")) for per in common_periods]
    margin_values = [float(str(margin_dict[per]).replace(",", "").replace(" ", "")) for per in common_periods]

    return {
        "periods": labels,
        "profit": profit_values,
        "margin": margin_values
    }

