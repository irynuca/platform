import pandas as pd

# Load the wide-format CSV
input_file = r"C:\Users\irina\Project Element\Data source\AQ\AQ_PL_history.csv"
output_file = r"C:\Users\irina\Project Element\Data source\AQ\AQ_PL_history_long.csv"

# Read CSV without headers (avoid index_col issues)
df = pd.read_csv(input_file, header=None)
# Number of metadata rows (adjust as needed)
metadata_rows = 10 
metadata = df.iloc[:metadata_rows]  # Extract metadata separately

# Extract financial metrics (start after metadata)
df_metrics = df.iloc[metadata_rows:]  # No reset_index() needed here!

# Set first column (metric names) as index, then transpose
df_metrics_transposed = df_metrics.set_index(0).T  # No extra columns!

# Add metadata back as new columns
for i in range(metadata_rows):
    df_metrics_transposed[metadata.iloc[i, 0]] = metadata.iloc[i, 1:].values

# Define metadata column names
metadata_columns = list(metadata.iloc[:, 0])  # Extract column names from metadata

# Get the actual column names (excluding extra NaNs)
valid_metric_columns = df_metrics_transposed.columns.difference(metadata_columns, sort=False).tolist()

# Ensure df_final includes ONLY valid metadata + financial data
df_final = df_metrics_transposed[metadata_columns + valid_metric_columns]

# Convert wide to long format using melt()
df_long = df_final.melt(
    id_vars=metadata_columns,  # Keep metadata unchanged
    var_name="metric_name",  # Convert financial metrics into row categories
    value_name="value"
)

# Save the long-format CSV
df_long.to_csv(output_file, index=False)

print("✅ CSV successfully transformed to long format!")

import sqlite3

# File paths
csv_file = r"C:\Users\irina\Project Element\Data source\AQ\AQ_PL_history_long.csv"
db_path = r"C:\Irina\Mosaiq8\app\data\financials.db"

import sqlite3
import pandas as pd

# Connect to SQLite database
db_path = r"C:\Irina\Mosaiq8\app\data\financials.db"
conn = sqlite3.connect(db_path)

query = "PRAGMA table_info(financial_data);"
df_schema = pd.read_sql_query(query, conn)
print(df_schema)


# Load CSV into Pandas
df = pd.read_csv(csv_file)

# Connect to SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Loop through each row in the DataFrame
for _, row in df.iterrows():
    cursor.execute("""
        INSERT OR REPLACE INTO financial_data (
            company_ticker, statement_name, statement_type, period_start,
            period_end, period_type, aggr_type, currency, metric_name, value
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (row["company_ticker"], row["statement_name"], row["statement_type"], row["period_start"],
          row["period_end"], row["period_type"], row["aggr_type"], row["currency"], row["metric_name"], row["value"]))

# Commit changes and close connection
conn.commit()
conn.close()

print("✅ Database updated: Existing records modified, new records added!")