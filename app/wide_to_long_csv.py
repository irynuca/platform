import os
import pandas as pd
import sqlite3
from datetime import datetime

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


def update_financials_db_from_csv(output_file, db_path, ticker, statement_name):
    print("🗃️ Updating SQLite database...")

    df = pd.read_csv(output_file)
    print(df)
    df["company_ticker"] = df["company_ticker"].astype(str).str.strip().str.upper()
    df["statement_name"] = df["statement_name"].astype(str).str.strip().str.title()

    ticker = ticker.strip().upper()
    statement_name = statement_name.strip().title()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 🧹 DELETE existing entries before inserting new ones
    cursor.execute("""
        DELETE FROM financial_data
        WHERE company_ticker = ? AND statement_name = ?
    """, (ticker, statement_name))
    print("🧹 Existing entries deleted.")

    for _, row in df.iterrows():
        # ✅ Format dates (convert from 'YYYY-MM-DD HH:MM:SS' to 'DD/MM/YYYY')
        period_start = datetime.strptime(row["period_start"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        period_end = datetime.strptime(row["period_end"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
        cursor.execute("""
            INSERT INTO financial_data (
                company_ticker, statement_name, statement_type, period_start,
                period_end, period_type, aggr_type, currency, metric_name_ro, value
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["company_ticker"], row["statement_name"], row["statement_type"], period_start,
            period_end, row["period_type"], row["aggr_type"], row["currency"], row["metric_name_ro"], row["value"]
        ))

    conn.commit()
    conn.close()

    print(f"✅ Database updated: {len(df)} rows inserted for {ticker} - {statement_name}")


def check_db_entries(db_path, ticker, statement_name):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT * FROM financial_data
        WHERE company_ticker = ? AND statement_name = ?
    """, conn, params=(ticker, statement_name))
    conn.close()

    print(f"📊 Found {len(df)} entries in DB for {ticker} - {statement_name}")
    return df

# === MAIN EXECUTION ===
available_tickers = ["AQ", "BRD", "TLV", "SNP", "SNG", "TGN", "TEL", "EL", "H2O", "SNN", "M", "PE", "SFG", "WINE", "ALR", "TRP", "FP", "ATB", "DIGI", "ONE", "TTS"]
statement_names = {
    "PL": "Profit & Loss",
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
statement_name = input("Enter statement type (PL, BS, CF): ").strip().upper()
while statement_name not in statement_names:
    statement_name = input("❌ Invalid type. Try again (PL, BS, CF): ").strip().upper()

base_dir = r"C:\Users\irina\Project Element\Data source"

# Convert Excel → CSV before doing anything else
convert_excel_to_csv(ticker, statement_name, base_dir)

input_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_name}_history.csv")
output_file = os.path.join(base_dir, ticker, f"{ticker}_{statement_name}_history_long.csv")
db_path = r"C:\Irina\Mosaiq8\app\data\financials.db"

# Run conversion and DB update
convert_csv_to_long_format(input_file, output_file)
update_financials_db_from_csv(output_file, db_path, ticker, statement_names[statement_name])
check_db_entries(db_path, ticker, statement_names[statement_name])
