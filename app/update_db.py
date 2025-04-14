import os
import pandas as pd
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
COMPANY_INFO_FILE = os.path.join(DATA_DIR, "company_info.csv")  # Full path to CSV
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

# ========================== CONVERSION UTILITIES =================================================================
def convert_excel_to_csv(ticker, statement_type, base_dir):
    excel_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_type}_history.xlsx")
    csv_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_type}_history.csv")
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return None
    
    print(f"📥 Converting Excel to CSV: {excel_file} → {csv_file}")
    df = pd.read_excel(excel_file, header=None)
    df.to_csv(csv_file, index=False, header=False)  # Match your CSV format (no header)
    print("✅ Excel converted to CSV.")
    return csv_file

def convert_csv_to_long_format(input_file, output_file, metadata_rows=10):
    print("📥 Reading wide-format CSV...")
    df = pd.read_csv(input_file, header=None)
    metadata = df.iloc[:metadata_rows]
    # Extract financial data and clean
    df_metrics = df.iloc[metadata_rows:]
    df_metrics[0] = df_metrics[0].astype(str).str.strip()
    df_metrics_transposed = df_metrics.set_index(0).T
    print("transposed metrics \n", df_metrics_transposed)

    # Add metadata rows as new columns
    for i in range(metadata_rows):
        df_metrics_transposed[metadata.iloc[i, 0]] = metadata.iloc[i, 1:].values

    metadata_columns = list(metadata.iloc[:, 0])
    valid_metric_columns = df_metrics_transposed.columns.difference(metadata_columns, sort=False).tolist()
    df_final = df_metrics_transposed[metadata_columns + valid_metric_columns]
 

    df_long = df_final.melt(
        id_vars=metadata_columns,
        var_name="metric_name_ro",
        value_name="value"
    )
    print("df_long: \n", df_long)
    # Optional: Remove rows with missing metric names or values
    df_long = df_long.dropna(subset=["metric_name_ro", "value"], how="all")

    df_long.to_csv(output_file, index=False)
    print("✅ CSV successfully transformed to long format!")
    return df_long

# ============================== DATABASE UPDATE ==================================================================
def update_financials_db_from_csv(output_file, DB_PATH, ticker, statement_name):
    print("🗃️ Updating SQLite database...")

    df = pd.read_csv(output_file)
    print(df)
    print("📎 BEFORE enforcing statement_name:", df["statement_name"].unique() if "statement_name" in df.columns else "Column not found")

    ticker = ticker.strip().upper()
    statement_name = statement_name.strip()
    df["company_ticker"] = df["company_ticker"].astype(str).str.strip().str.upper()
    df["statement_name"] = statement_name
    df["metric_name_ro"] = df["metric_name_ro"].astype(str).str.strip()


    # Convert date columns to the correct format: YYYY-MM-DD
    df["period_start"] = pd.to_datetime(df["period_start"], format="%Y-%m-%d %H:%M:%S", errors="coerce").dt.strftime("%Y-%m-%d")
    df["period_end"] = pd.to_datetime(df["period_end"], format="%Y-%m-%d %H:%M:%S", errors="coerce").dt.strftime("%Y-%m-%d")

    # Get mapping from financial_metrics
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT metric_name_ro, metric_parent FROM financial_metrics WHERE metric_parent IS NOT NULL
    """)
    metric_map = {row[0]: row[1] for row in cursor.fetchall()}

    # Add metric_parent and last_updated to DataFrame
    df["metric_parent"] = df["metric_name_ro"].map(metric_map)
    df["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # DELETE existing entries
    cursor.execute("""
        DELETE FROM financial_data
        WHERE company_ticker = ? AND statement_name = ?
    """, (ticker, statement_name))
    print("🧹 Existing entries deleted.")

    # Insert each row
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO financial_data (
                company_ticker, statement_name, statement_type, period_start,
                period_end, period_type, aggr_type, currency, metric_name_ro, value,
                metric_parent, last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["company_ticker"], row["statement_name"], row["statement_type"],
            row["period_start"], row["period_end"], row["period_type"],
            row["aggr_type"], row["currency"], row["metric_name_ro"], row["value"],
            row.get("metric_parent"), row.get("last_updated")
        ))

    conn.commit()
    conn.close()

    print(f"✅ Database updated: {len(df)} rows inserted for {ticker} - {statement_name}")

# ============================================= QTL GENERATOR =========================================================================
def generate_qtl_from_cml(db_path):
    print("🔄 Generating QTL values from CML...")

    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query("""
        SELECT * FROM financial_data
        WHERE aggr_type = 'cml'
          AND statement_name IN ('Profit&Loss', 'Cash Flow')
    """, conn)

    if df.empty:
        print("⚠️ No CML data found.")
        conn.close()
        return

    # Ensure datetime
    df["period_end"] = pd.to_datetime(df["period_end"]).dt.normalize()
    df["period_start"] = pd.to_datetime(df["period_start"]).dt.normalize()

    # Sort chronologically
    df = df.sort_values("period_end")

    # Index for fast lookup
    lookup = df.set_index([
        "company_ticker",
        "statement_name",
        "statement_type",
        "currency",
        "metric_name_ro",
        "period_end"
    ])

    rows_to_insert = []

    for _, curr in df.iterrows():
        curr_end = pd.to_datetime(curr["period_end"]).normalize()

        # ❌ Skip Q1 as target (we already have CML = QTL)
        if curr_end.month == 3 and curr_end.day == 31:
            continue

        # Look for prior period exactly 3 months earlier
        # Find prior period's true month-end
        prior_end = (curr_end - relativedelta(months=3)).replace(day=1) + pd.offsets.MonthEnd(0)


        key = (
            curr["company_ticker"],
            curr["statement_name"],
            curr["statement_type"],
            curr["currency"],
            curr["metric_name_ro"],
            prior_end
        )

        try:
            prev = lookup.loc[key]
        except KeyError:
            print(f"⏩ Skipping {curr_end.date()} — no prior CML found at {prior_end.date()}")
            continue

        qtl_value = curr["value"] - prev["value"]

        rows_to_insert.append({
            "company_ticker": curr["company_ticker"],
            "statement_name": curr["statement_name"],
            "statement_type": curr["statement_type"],
            "period_type": "quarter",
            "aggr_type": "qtl",
            "currency": curr["currency"],
            "metric_name_ro": curr["metric_name_ro"],
            "value": qtl_value,
            "period_start": (prior_end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "period_end": curr_end.strftime("%Y-%m-%d"),
            "metric_parent": None,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        print(f"✅ QTL: {curr['metric_name_ro']} | {curr['company_ticker']} | {rows_to_insert[-1]['period_start']} → {rows_to_insert[-1]['period_end']} | Δ = {qtl_value:.2f}")

    print(f"\n🧮 Prepared {len(rows_to_insert)} QTL rows. Inserting into database...")

    cursor = conn.cursor()
    for row in rows_to_insert:
        cursor.execute("""
            INSERT OR REPLACE INTO financial_data (
                company_ticker, statement_name, statement_type,
                period_start, period_end, period_type, aggr_type,
                currency, metric_name_ro, value,
                metric_parent, last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["company_ticker"], row["statement_name"], row["statement_type"],
            row["period_start"], row["period_end"], row["period_type"], row["aggr_type"],
            row["currency"], row["metric_name_ro"], row["value"],
            row["metric_parent"], row["last_updated"]
        ))

    conn.commit()
    conn.close()
    print("✅ QTL generation complete and stored in financial_data.")


# ===================================== DEBUGGING & CHECKING ========================================================

def check_db_entries(DB_PATH, ticker, statement_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT * FROM financial_data
        WHERE company_ticker = ? AND statement_name = ?
    """, conn, params=(ticker, statement_name))
    conn.close()

    print(f"📊 Found {len(df)} entries in DB for {ticker} - {statement_name}")
    return df

# ============================================ MAIN EXECUTION ============================================================
def main():
    available_tickers = ["AQ", "BRD", "TLV", "SNP", "SNG", "TGN", "TEL", "EL", "H2O", "SNN", "M", "PE", "SFG", "WINE", "ALR", "TRP", "FP", "ATB", "DIGI", "ONE", "TTS"]
    statement_names = {
        "PL": "Profit&Loss",
        "BS": "Balance Sheet",
        "CF": "Cash Flow"
    }

    print("Available tickers:", ", ".join(available_tickers))
    ticker = input("Enter the ticker symbol: ").strip().upper()
    while ticker not in available_tickers:
        ticker = input("❌ Invalid ticker. Try again: ").strip().upper()

    print("Statement types:")
    for code, desc in statement_names.items():
        print(f"  {code} - {desc}")
    statement_code = input("Enter statement type (PL, BS, CF): ").strip().upper()
    while statement_code not in statement_names:
        statement_code = input("❌ Invalid type. Try again (PL, BS, CF): ").strip().upper()

    statement_name = statement_names[statement_code]
    base_dir = r"C:\Users\irina\Project Element\Data source"

    convert_excel_to_csv(ticker, statement_code, base_dir)
    input_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_code}_history.csv")
    output_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_code}_history_long.csv")

    convert_csv_to_long_format(input_file, output_file)
    update_financials_db_from_csv(output_file, DB_PATH, ticker, statement_name)
    generate_qtl_from_cml(DB_PATH)
    check_db_entries(DB_PATH, ticker, statement_name)

if __name__ == "__main__":
    main()