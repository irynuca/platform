import yfinance as yf
import pandas as pd
import sqlite3
import logging
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import re
from collections import OrderedDict
from collections import defaultdict
import time
from babel.dates import format_date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
desc_dir = os.path.join(DATA_DIR, "business_descriptions")
COMPANY_INFO_FILE = os.path.join(DATA_DIR, "company_info.csv")  # Full path to CSV
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

def get_company_details_from_db(ticker):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT company_name, industry FROM companies WHERE company_ticker = ?", (ticker.upper(),))
        result = cursor.fetchone()
        if result:
            return {"company_name": result[0], "industry": result[1]}
        else:
            # Fallback if ticker is not found in the database
                logging.warning(f"Ticker '{ticker}' not found in the database.")
                return {"company_name": ticker, "industry": "N/A"}

    except sqlite3.Error as e:
        logging.error(f"Database error while fetching company details for '{ticker}': {e}")
        return {"company_name": ticker, "industry": "N/A"}

    except Exception as e:
        logging.exception(f"Unexpected error while fetching company details for '{ticker}': {e}")
        return {"company_name": ticker, "industry": "N/A"}

def get_latest_stock_indicators(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT close_price, market_cap, pe_ratio, date
        FROM stock_data
        WHERE company_ticker = ?
        ORDER BY ABS(julianday(date) - julianday('now')) ASC
        LIMIT 1
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker.upper(),))
        result = cursor.fetchone()
        if result:
            return {
                "last_price": result[0],
                "market_cap": result[1],
                "pe_ratio": result[2],
                "ref_date": result[3]  # Optional: for debug or display
            }
        else:
            return {
                "last_price": "N/A",
                "market_cap": "N/A",
                "pe_ratio": "N/A",
                "ref_date": "N/A"
            }
    except Exception as e:
        print(f"Error retrieving stock indicators: {e}")
        return {
            "last_price": "N/A",
            "market_cap": "N/A",
            "pe_ratio": "N/A",
            "ref_date": "N/A"
        }
    finally:
        conn.close()

def get_latest_net_income(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT f.value
        FROM financial_data f
        JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
        WHERE f.company_ticker = ?
        AND m.generalized_metric_eng = 'Net profit a.m.'
        ORDER BY ABS(julianday(f.period_end) - julianday('now')) ASC
        LIMIT 1
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker.upper(),))
        result = cursor.fetchone()
        return float(str(result[0]).replace(",", "")) if result else "N/A"
    except Exception as e:
        print(f"Error retrieving net income: {e}")
        return "N/A"
    finally:
        conn.close()

def format_date_ro(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return format_date(date_obj, format="d MMMM y", locale="ro_RO")
    except:
        return date_str
    
def get_next_earnings_date(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT event_date 
        FROM financial_events 
        WHERE company_ticker = ? AND event_type = 'earnings_release' AND event_date >= date('now')
        ORDER BY event_date ASC 
        LIMIT 1
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker.upper(),))
        result = cursor.fetchone()
        return result[0] if result else "N/A"
    except Exception as e:
        print(f"Error retrieving earnings date: {e}")
        return "N/A"
    finally:
        conn.close()

def get_latest_price_variation(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT change_day
        FROM stock_data
        WHERE company_ticker = ?
          AND change_day IS NOT NULL
        ORDER BY ABS(julianday(date) - julianday('now')) ASC
        LIMIT 1
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker.upper(),))
        result = cursor.fetchone()
        return round(result[0], 2) if result else "N/A"
    except Exception as e:
        print(f"Error retrieving daily price variation: {e}")
        return "N/A"
    finally:
        conn.close()

def get_latest_variation_changes(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT change_yoy, change_ytd
        FROM stock_data
        WHERE company_ticker = ?
          AND change_yoy IS NOT NULL
          AND change_ytd IS NOT NULL
        ORDER BY ABS(julianday(date) - julianday('now')) ASC
        LIMIT 1
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker.upper(),))
        result = cursor.fetchone()
        if result:
            return {
                "yoy_change": round(result[0], 2),
                "ytd_change": round(result[1], 2)
            }
        else:
            return {
                "yoy_change": "N/A",
                "ytd_change": "N/A"
            }
    except Exception as e:
        print(f"Error retrieving YoY/YTD changes: {e}")
        return {
            "yoy_change": "N/A",
            "ytd_change": "N/A"
        }
    finally:
        conn.close()

def get_stock_overview(ticker):
    """
    Combines company details, market indicators, income, and events into a single dictionary used for frontend display.
    """
    # Fetch basic company info
    company_details = get_company_details_from_db(ticker)
    indicators = get_latest_stock_indicators(ticker)
    net_income = get_latest_net_income(ticker)
    earnings_date = get_next_earnings_date(ticker)
    variation_changes = get_latest_variation_changes(ticker)

    # Get business description from local file
    txt_filename = f"{ticker.upper()}_about_ro.txt"
    txt_path = os.path.join(desc_dir, txt_filename)
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            business_description = f.read().strip()
    except FileNotFoundError:
        business_description = "Descrierea companiei nu este disponibilă."

    # Helper to clean numeric values
    def clean_numeric(value, default="N/A"):
        try:
            return float(str(value).replace(",", "").replace(" ", ""))
        except (ValueError, TypeError):
            return default

    # Build the stock data dictionary
    stock_data = {
        "company_name": company_details.get("company_name", ticker),
        "industry": company_details.get("industry", "N/A"),
        "last_price": clean_numeric(indicators.get("last_price", "N/A")),
        "price_variation": clean_numeric(get_latest_price_variation(ticker)),
        "market_cap": clean_numeric(indicators.get("market_cap", "N/A")),
        "pe_ratio": clean_numeric(indicators.get("pe_ratio", "N/A")),
        "net_income": clean_numeric(net_income),
        "next_earnings_date": format_date_ro(earnings_date),
        "longBusinessSummary": business_description,
        "yoy_change": clean_numeric(variation_changes.get("yoy_change", "N/A")),
        "ytd_change": clean_numeric(variation_changes.get("ytd_change", "N/A")),
    }

    return stock_data


def get_historical_stock_data(ticker, period="1mo", interval="1d"):
    conn=sqlite3.connect(DB_PATH)
        # Map period to number of days
    period_map = {
        "1d": 1,
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "1y": 365,
        "5y": 1825,
        "max": None  # Special case: no filter
    }

    try:
        days = period_map.get(period, 30)
        query = "SELECT date, close_price FROM stock_data WHERE company_ticker = ?"
        params = [ticker.upper()]

        if days is not None:
            cutoff = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
            query += " AND date >= ?"
            params.append(cutoff)

        query += " ORDER BY date ASC"

        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return None

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        stock_data = {
            "dates": df["date"].dt.strftime("%Y-%m-%d").tolist(),
            "prices": df["close_price"].tolist()
        }

        return stock_data

    except Exception as e:
        print(f"❌ Error retrieving historical data: {e}")
        return None

    finally:
        conn.close()

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
        sorted_periods = sorted(row_data.index, key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
        period_values = OrderedDict()
        for period_col in sorted_periods:
            period_values[period_col] = float(row_data[period_col]) if pd.notnull(row_data[period_col]) else None

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
    print(periods)
    if not periods:
        conn.close()
        return {"period":"N/A", "data": []}

    # Step 2: Parse to datetime and find the latest
    try:
        latest_period = max(
            (datetime.strptime(p[0], "%Y-%m-%d") for p in periods),
            default=None
        ).strftime("%Y-%m-%d")
    except Exception as e:
        print(f"❌ Date parsing error: {e}")
        conn.close()
        return {"period": "N/A", "data": []}


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

def get_revenue_qtl_and_change_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_qtl v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Revenue'
        ORDER BY v.period_end ASC
    """, (ticker,))
    revenue_data = cursor.fetchall()
    print("Revenue data:", revenue_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_qtl
        WHERE company_ticker = ? AND ratio_name_eng = 'Revenue growth y/y'
        ORDER BY period_end ASC
    """, (ticker,))
    change_data = cursor.fetchall()
    print("Revenue change data:", change_data)

    conn.close()

    # --- Normalize and match periods
    revenue_dict = {row[0]: (row[1], row[2]) for row in revenue_data}  # period_end: (display_period, value)
    change_dict = {row[0]: row[2] for row in change_data}  # ✅ value, not display_period

    common_periods = sorted(
    p for p in (set(revenue_dict.keys()) & set(change_dict.keys()))
    if change_dict[p] is not None and revenue_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [revenue_dict[p][0] for p in common_periods]
    revenues = [float(str(revenue_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    change_rate = [float(str(change_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "revenues": revenues,
        "change_rate": change_rate
    }

def get_operating_profit_qtl_and_margin_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_qtl v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Operating profit'
        ORDER BY v.period_end ASC
    """, (ticker,))

    operating_profit_data = cursor.fetchall()
    print("Operating profit data:", operating_profit_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_qtl
        WHERE company_ticker = ? AND ratio_name_eng = 'Operating profit margin'
        ORDER BY period_end ASC
    """, (ticker,))
    operating_margin_data = cursor.fetchall()
    print("Operating margin data:", operating_margin_data)

    conn.close()

    # --- Normalize and match periods
    operating_profit_dict = {row[0]: (row[1], row[2]) for row in operating_profit_data}
    margin_dict = {row[0]: row[2] for row in operating_margin_data}  

    common_periods = sorted(
    p for p in (set(operating_profit_dict.keys()) & set(margin_dict.keys()))
    if margin_dict[p] is not None and operating_profit_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [operating_profit_dict[p][0] for p in common_periods]
    operating_profit = [float(str(operating_profit_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    operating_margin = [float(str(margin_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "operating_profit": operating_profit,
        "operating_margin": operating_margin
    }

def get_net_profit_qtl_and_margin_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_qtl v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Net profit a.m.'
        ORDER BY v.period_end ASC
    """, (ticker,))

    net_profit_data = cursor.fetchall()
    print("Net profit data:", net_profit_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_qtl
        WHERE company_ticker = ? AND ratio_name_eng = 'Net profit margin'
        ORDER BY period_end ASC
    """, (ticker,))
    net_margin_data = cursor.fetchall()
    print("Operating margin data:", net_margin_data)

    conn.close()

    # --- Normalize and match periods
    net_profit_dict = {row[0]: (row[1], row[2]) for row in net_profit_data}
    margin_dict = {row[0]: row[2] for row in net_margin_data}  

    common_periods = sorted(
    p for p in (set(net_profit_dict.keys()) & set(margin_dict.keys()))
    if margin_dict[p] is not None and net_profit_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [net_profit_dict[p][0] for p in common_periods]
    net_profit = [float(str(net_profit_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    net_margin = [float(str(margin_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "net_profit": net_profit,
        "net_margin": net_margin
    }

def get_chart_comment(ticker, chart_type, period_display):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT comment FROM chart_comments
        WHERE company_ticker = ? AND chart_type = ? AND period_display = ?
    """, (ticker, chart_type, period_display))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_revenue_annual_and_change_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_annual v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Revenue'
        ORDER BY v.period_end ASC
    """, (ticker,))
    revenue_data = cursor.fetchall()
    print("Revenue data:", revenue_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_annual
        WHERE company_ticker = ? AND ratio_name_eng = 'Revenue growth y/y'
        ORDER BY period_end ASC
    """, (ticker,))
    change_data = cursor.fetchall()
    print("Revenue change data:", change_data)

    conn.close()

    # --- Normalize and match periods
    revenue_dict = {row[0]: (row[1], row[2]) for row in revenue_data}  # period_end: (display_period, value)
    change_dict = {row[0]: row[2] for row in change_data}  # ✅ value, not display_period

    common_periods = sorted(
    p for p in (set(revenue_dict.keys()) & set(change_dict.keys()))
    if change_dict[p] is not None and revenue_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [revenue_dict[p][0] for p in common_periods]
    revenues = [float(str(revenue_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    change_rate = [float(str(change_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "revenues": revenues,
        "change_rate": change_rate
    }

def get_operating_profit_annual_and_margin_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_annual v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Operating profit'
        ORDER BY v.period_end ASC
    """, (ticker,))
    operating_profit_data = cursor.fetchall()
    print("Operating profit data:", operating_profit_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_annual
        WHERE company_ticker = ? AND ratio_name_eng = 'Operating profit margin'
        ORDER BY period_end ASC
    """, (ticker,))
    operating_margin_data = cursor.fetchall()
    print("Operating margin data:", operating_margin_data)

    conn.close()

    # --- Normalize and match periods
    operating_profit_dict = {row[0]: (row[1], row[2]) for row in operating_profit_data}  # period_end: (display_period, value)
    operating_margin_dict = {row[0]: row[2] for row in operating_margin_data}  # ✅ value, not display_period

    common_periods = sorted(
    p for p in (set(operating_profit_dict.keys()) & set(operating_margin_dict.keys()))
    if operating_margin_dict[p] is not None and operating_profit_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [operating_profit_dict[p][0] for p in common_periods]
    operating_profit = [float(str(operating_profit_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    operating_margin = [float(str(operating_margin_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "operating_profit": operating_profit,
        "operating_margin": operating_margin
    }

def get_net_profit_annual_and_margin_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Fetch Revenue from view_financial_qtl ---
    cursor.execute("""
        SELECT v.period_end, v.display_period, v.value
        FROM view_financial_annual v
        JOIN financial_metrics m 
        ON v.metric_name_ro = m.metric_name_ro
        AND v.company_ticker = m.company_ticker
        WHERE v.company_ticker = ?
        AND m.generalized_metric_eng = 'Net profit a.m.'
        ORDER BY v.period_end ASC
    """, (ticker,))
    net_profit_data = cursor.fetchall()
    print("Net profit data:", net_profit_data)

    cursor.execute("""
        SELECT period_end, display_period, value
        FROM view_financial_ratios_annual
        WHERE company_ticker = ? AND ratio_name_eng = 'Net profit margin'
        ORDER BY period_end ASC
    """, (ticker,))
    net_margin_data = cursor.fetchall()
    print("Net profit margin data:", net_margin_data)

    conn.close()

    # --- Normalize and match periods
    net_profit_dict = {row[0]: (row[1], row[2]) for row in net_profit_data}  # period_end: (display_period, value)
    net_margin_dict = {row[0]: row[2] for row in net_margin_data}  # ✅ value, not display_period

    common_periods = sorted(
    p for p in (set(net_profit_dict.keys()) & set(net_margin_dict.keys()))
    if net_margin_dict[p] is not None and net_profit_dict[p][1] is not None)[-8:]

    if not common_periods:
        return None

    periods = [net_profit_dict[p][0] for p in common_periods]
    net_profit = [float(str(net_profit_dict[p][1]).replace(",", "").replace(" ", "")) for p in common_periods]
    net_margin = [float(str(net_margin_dict[p]).replace(",", "").replace(" ", "")) for p in common_periods]

    return {
        "periods": periods,
        "net_profit": net_profit,
        "net_margin": net_margin
    }
def get_dividends(ticker):
    """
    Fetch dividend data for a given ticker as a list of dicts.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables column name access
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            DPS_year,
            DPS_value,
            dividends_yoy_change,      
            net_profit,
            total_dividends,
            payout_ratio,
            dividend_yield,
            fcfe,
            dividends_to_fcfe,
            ex_dividend_date,
            payment_date,
            dividend_type,
            dividend_status
        FROM dividends
        WHERE company_ticker = ?
        ORDER BY ex_dividend_date DESC
    """, (ticker,))

    rows = cursor.fetchall()
    conn.close()

    # Convert rows to list of dicts
    return [dict(row) for row in rows]

def get_dividends_dps_and_growth(ticker):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DPS_year, DPS_value, dividends_yoy_change
        FROM dividends
        WHERE company_ticker = ?
    """, (ticker,))
    
    rows = cursor.fetchall()
    conn.close()

    grouped = defaultdict(lambda: {"DPS_value": 0, "dividends_yoy_change": None})
    for row in rows:
        year = row["DPS_year"]
        grouped[year]["DPS_value"] += row["DPS_value"] or 0
        if row["dividends_yoy_change"] is not None:
            grouped[year]["dividends_yoy_change"] = row["dividends_yoy_change"]

    return [
        {"year": year, "DPS_value": data["DPS_value"], "dividends_yoy_change": data["dividends_yoy_change"]}
        for year, data in sorted(grouped.items())
    ]

def get_dividend_yield_history(ticker):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DPS_year, dividend_yield
        FROM dividends
        WHERE company_ticker = ?
    """, (ticker,))
    
    rows = cursor.fetchall()
    conn.close()

    grouped = defaultdict(float)
    for row in rows:
        grouped[row["DPS_year"]] += row["dividend_yield"] or 0

    return [{"year": year, "dividend_yield": val} for year, val in sorted(grouped.items())]

def get_payout_ratio_history(ticker):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DPS_year, payout_ratio
        FROM dividends
        WHERE company_ticker = ?
    """, (ticker,))
    
    rows = cursor.fetchall()
    conn.close()

    grouped = defaultdict(float)
    for row in rows:
        grouped[row["DPS_year"]] += row["payout_ratio"] or 0

    return [{"year": year, "payout_ratio": val} for year, val in sorted(grouped.items())]

def get_dividends_to_fcfe_history(ticker):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DPS_year, dividends_to_fcfe
        FROM dividends
        WHERE company_ticker = ?
    """, (ticker,))
    
    rows = cursor.fetchall()
    conn.close()

    grouped = defaultdict(float)
    for row in rows:
        grouped[row["DPS_year"]] += row["dividends_to_fcfe"] or 0

    return [{"year": year, "dividends_to_fcfe": val} for year, val in sorted(grouped.items())]

def get_calendar_events():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            fe.id,
            fe.event_date,
            fe.title AS raw_title,
            fe.period_reference,
            fe.event_type,
            fe.category,
            fe.company_ticker,
            c.company_name
        FROM financial_events fe
        LEFT JOIN companies c
          ON UPPER(TRIM(fe.company_ticker)) = UPPER(TRIM(c.company_ticker))
        ORDER BY fe.event_date
    """)
    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        ticker = (r["company_ticker"] or "").strip().upper()
        company = r["company_name"]
        raw_title = (r["raw_title"] or "").strip()
        raw_title = re.sub(r"[–\-\s]+$", "", raw_title)
        period = (r["period_reference"] or "").strip()

        # Handle title formatting based on category
        if r["category"] == "company":
            # Format: Company (TICKER) – Event Title – Period
            if ticker and period:
                title = f"{company} ({ticker}) – {raw_title} – {period}"
            elif ticker:
                title = f"{company} ({ticker}) – {raw_title}"
            else:
                title = f"{raw_title} – {period}" if period else raw_title
        elif r["category"] == "macro":
            # Format: Event Title – Period
            title = f"{raw_title} – {period}" if period else raw_title

        events.append({
            "id": r["id"],
            "title": title,
            "start": r["event_date"],
            "extendedProps": {
                "ticker": ticker,
                "company": company,
                "period": period,
                "eventType": r["event_type"],
                "category": r["category"]
            }
        })

    return events