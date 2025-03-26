import sqlite3
import pandas as pd

# Connect to the database
db_path = r"C:\Irina\Mosaiq8\financials.db"
conn = sqlite3.connect(db_path)

# SQL Query
query = """
SELECT 
    f.company_ticker,
    m.id AS metric_id,
    f.company_ticker,
    f.metric_name, 
    f.value, 
    f.period_end, 
    f.currency
FROM financial_data f
JOIN financial_metrics m ON f.metric_name=m.metric_name_ro
WHERE f.company_ticker = 'AQ'
AND f.statement_name = 'Profit&Loss'
AND f.period_type = 'annual'
ORDER BY m.id ASC, f.period_end ASC
"""

# Convert to Pandas DataFrame
df = pd.read_sql_query(query, conn)
conn.close()

# Pivot table to structure: metric_name as rows, period_end as columns
df_pivot = df.pivot(index="metric_id", columns="period_end", values="value")

# Reset index to include metric names
df_pivot = df_pivot.merge(df[['metric_id', 'metric_name']].drop_duplicates(), on="metric_id").set_index("metric_name")

# Drop metric_id column (only needed for sorting)
df_pivot.drop(columns=["metric_id"], inplace=True)

# Display transformed table
print(df_pivot)
