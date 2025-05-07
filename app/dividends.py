import pandas as pd
import sqlite3

CSV_PATH = r"C:\Users\irina\Project Element\Data source\AQ\AQ_dividend_history.csv"
DB_PATH = r"C:\Irina\Mosaiq8\app\data\financials.db"

import pandas as pd
import sqlite3
import yfinance as yf
from datetime import datetime

CSV_PATH = r"C:\Users\irina\Project Element\Data source\AQ\AQ_dividend_history.csv"

def get_net_profit(ticker, year):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT f.value FROM financial_data f
    JOIN financial_metrics m ON f.metric_name_ro=m.metric_name_ro
    WHERE f.company_ticker = ?
      AND f.statement_name = 'Profit&Loss'
      AND f.period_type = 'annual'
      AND m.generalized_metric_eng = 'Net profit a.m.'
      AND strftime('%Y', f.period_end) = ?
    LIMIT 1
    """
    try:
        result = cursor.execute(query, (ticker, str(year))).fetchone()
        if result:
            net_profit = float(result[0])
            print(f"✅ Net profit for {ticker} in year {year} was {net_profit:,.0f}")
            return net_profit
        else:
            print(f"⚠️ Net profit not found for {ticker} in year {year}")
            return None
    except Exception as e:
        print(f"❌ Error fetching net profit for {ticker}, {year}: {e}")
        return None
    finally:
        conn.close()

def get_fcfe(ticker, year):
    """
    Fetch FCFE (Free Cash Flow to Equity) from the derived_metrics table,
    using the year corresponding to the net profit (dividend source year).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT value
    FROM derived_metrics
    WHERE company_ticker = ?
      AND metric_name_ro = 'FCFE'
      AND period_type = 'annual'
      AND strftime('%Y', period_end) = ?
    LIMIT 1
    """

    try:
        result = cursor.execute(query, (ticker, str(year))).fetchone()
        if result:
            fcfe = float(result[0])
            print(f"✅ FCFE for {ticker} in year {year} was {fcfe:,.0f}")
            return fcfe
        else:
            print(f"⚠️ FCFE not found for {ticker} in year {year}")
            return None
    except Exception as e:
        print(f"❌ Error fetching FCFE for {ticker}, {year}: {e}")
        return None
    finally:
        conn.close()

def get_average_price_for_dividend(ticker, announcement_date, registration_date, ex_dividend_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert dates to datetime
    try:
        ex_date = datetime.strptime(ex_dividend_date, "%Y-%m-%d").date()
        ann_date = datetime.strptime(announcement_date, "%Y-%m-%d").date()
        reg_date = datetime.strptime(registration_date, "%Y-%m-%d").date()
    except Exception as e:
        print(f"❌ Date parsing error: {e}")
        return None

    today = datetime.today().date()

    if ex_date <= today:
        # Historical dividend — calculate average from announcement to registration date
        query = """
        SELECT AVG(close_price) FROM stock_data
        WHERE company_ticker = ?
          AND date BETWEEN ? AND ?
        """
        cursor.execute(query, (ticker, announcement_date, registration_date))
        result = cursor.fetchone()
        avg_price = result[0] if result else None
        print(f"📊 Avg price for {ticker} from {announcement_date} to {registration_date}: {avg_price}")
    else:
        # Upcoming dividend — use latest available price
        query = """
        SELECT close_price FROM stock_data
        WHERE company_ticker = ?
        ORDER BY date DESC
        LIMIT 1
        """
        cursor.execute(query, (ticker,))
        result = cursor.fetchone()
        avg_price = result[0] if result else None
        print(f"📈 Latest available price for {ticker}: {avg_price}")

    conn.close()
    return avg_price


def enrich_and_insert_dividends():
    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # GROUP AND SUM TOTAL DPS per year per ticker
    totals_by_year = df.groupby(["company_ticker", "DPS_year"])["DPS"].sum().to_dict()

    for _, row in df.iterrows():
        ticker = row["company_ticker"]
        year = int(row["DPS_year"])
        dps = float(row["DPS"])
        shares = int(row["number_of_shares"])
        net_profit_year = int(row["net_profit_year"])
        fcfe = get_fcfe(ticker, net_profit_year)

        # -- CALCULATIONS --
        # -- YEAR-OVER-YEAR CHANGE --
        current_total = totals_by_year.get((ticker, year), 0)
        previous_total = totals_by_year.get((ticker, year - 1), 0)
        dividends_yoy_change = (
            (current_total - previous_total) / previous_total if previous_total else None
        )

        total_dividends = dps * shares
        net_profit = get_net_profit(ticker, net_profit_year)
        payout_ratio = total_dividends / net_profit if net_profit else None
        avg_price = get_average_price_for_dividend(
            ticker,
            row["announcement_date"],
            row["registration_date"],
            row["ex_dividend_date"]
        )
        dividend_yield = dps / avg_price if avg_price else None
        dividends_to_fcfe = total_dividends / float(fcfe) if fcfe else None

        # -- PREPARE ALL VALUES --
        record = (
            ticker,
            year,
            dps,
            dividends_yoy_change,
            shares,
            total_dividends,
            net_profit_year,
            net_profit,
            payout_ratio,
            dividend_yield,
            fcfe,
            dividends_to_fcfe,
            row.get("gsm_approval_date"),
            row.get("registration_date"),
            row.get("ex_dividend_date"),
            row.get("announcement_date"),
            row.get("payment_date"),
            row.get("dividend_type"),
            row.get("dividend_status"),
            
        )

        # -- INSERT or REPLACE --
        cursor.execute("""
        INSERT OR REPLACE INTO dividends (
            company_ticker, DPS_year, DPS_value, dividends_yoy_change, number_of_shares, total_dividends,
            net_profit_year, net_profit, payout_ratio, dividend_yield, fcfe,
            dividends_to_fcfe, gsm_approval_date, registration_date, ex_dividend_date,
            announcement_date, payment_date, dividend_type, dividend_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record)

    conn.commit()
    conn.close()
    print("✅ All dividend records inserted successfully.")

if __name__ == "__main__":
    print("🚀 Starting dividend enrichment and insertion process...")
    enrich_and_insert_dividends()
    print("🏁 Done.")