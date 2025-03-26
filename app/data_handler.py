import yfinance as yf
import pandas as pd
import sqlite3
import os
import plotly.graph_objects as go
from datetime import datetime
import json
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
COMPANY_INFO_FILE = os.path.join(DATA_DIR, "company_info.csv")  # Full path to CSV
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

def get_yahoo_stock_price(ticker):
    stock = yf.Ticker(ticker + ".RO")
    info = stock.info  # ✅ Retrieve stock info

    if not info:
        return{"error":f"Stock data not found for {ticker}"}
    
    company_name = info.get("longName") or info.get("shortName") or ticker

    stock_data = {
        "company_name": company_name,
        "last_price": info.get("regularMarketPrice", "N/A"),
        "price_variation": round(info.get("regularMarketChangePercent", 0), 2) if "regularMarketChangePercent" in info else "N/A",
        "market_cap": f"{round(info.get('marketCap', 0) / 1e9, 2)}md RON" if "marketCap" in info else "N/A",
        "industry": info.get("industry", "N/A"),
        "net_income": f"{round(info.get('netIncomeToCommon', 0) / 1e9, 2)}md RON" if "netIncomeToCommon" in info else "N/A",
        "pe_ratio": f"{round(info.get('trailingPE', 0), 2)}x" if "trailingPE" in info else "N/A",
        "next_earnings_date": datetime.utcfromtimestamp(info["earningsTimestamp"]).strftime('%Y-%m-%d') if "earningsTimestamp" in info and isinstance(info["earningsTimestamp"], (int, float)) else "N/A",
        "longBusinessSummary": info.get("longBusinessSummary", "Descrierea companiei nu este disponibilă.")
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
    stock=yf.Ticker(ticker + ".RO")
    # Adjust interval depending on the period
    if period in ["1d", "5d"]:
        interval = "30m"
    elif period in ["1mo", "3mo"]:
        interval = "1d"
    elif period == "1y":
        interval = "1wk"
    elif period in ["5y", "max"]:
        interval = "1mo"
    history=stock.history(period=period, interval=interval)
    if history.empty:
        return None
    
    stock_data={
        "dates":history.index.strftime("%Y-%m-%d").tolist(),
        "prices":history["Close"].tolist()
    }

    return stock_data

DB_PATH = "c:\\Irina\\Mosaiq8\\app\\data\\financials.db"

from collections import OrderedDict
import pandas as pd
import json
import sqlite3

def get_pl_statement(ticker, period_type, aggr_type):
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        m.id AS metric_id, 
        m.metric_name_ro AS metric_name, 
        f.value, 
        f.period_end
    FROM financial_data f
    JOIN financial_metrics m ON f.metric_name = m.metric_name_ro
    WHERE f.company_ticker = ?
    AND f.statement_name = 'Profit&Loss'
    AND f.period_type = ?
    AND f.aggr_type = ?
    ORDER BY m.id ASC, f.period_end ASC
    """
    params = [ticker, period_type, aggr_type]
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        print(f"⚠️ No data found for {ticker} ({period_type}, {aggr_type})")
        return []

    # 1) Convert period_end to datetime for sorting
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")
    df = df.sort_values(by=["metric_id", "period_end"], ascending=[True, True])

    # 2) Pivot: metric_id as rows, period_end as columns
    df_pivot = df.pivot(index="metric_id", columns="period_end", values="value")

    # Convert pivoted columns to string format ("YYYY-MM-DD")
    df_pivot.columns = pd.to_datetime(df_pivot.columns).strftime("%d-%m-%Y")

    # 3) Merge metric_name, keep metric_id for final sorting
    df_pivot = df_pivot.merge(
        df[['metric_id', 'metric_name']].drop_duplicates(),
        on="metric_id"
    ).set_index("metric_id")

    # 4) Convert columns to string for JSON
    df_pivot.columns = [str(col) for col in df_pivot.columns]

    # 5) Build a list of rows to preserve order
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
