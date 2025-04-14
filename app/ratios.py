import sqlite3
import pandas as pd
from datetime import datetime
import os
from dateutil.relativedelta import relativedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

def safe_divide(numerator, denominator, multiplier=1):
    if numerator is not None and denominator not in (None, 0):
        return (numerator / denominator) * multiplier
    return None

def average(ending_value, beginning_value):
    if ending_value is not None and beginning_value is not None:
        return (ending_value + beginning_value) / 2
    return None

def get_prior_period_end(current_end: datetime, period_type: str, aggr_type: str = None):
    if period_type == "annual":
        return (current_end - relativedelta(months=12)).replace(day=31)

    if period_type == "quarter":
        if aggr_type == "qtl":
            prior = current_end - relativedelta(months=3)
        elif aggr_type == "cml":
            month_offset = {
                3: 3,
                6: 6,
                9: 9,
                12: 12
            }.get(current_end.month, 3)
            prior = current_end - relativedelta(months=month_offset)
        else:
            return None

        # Force day to 31st or actual month-end
        # Set to last day of that month
        next_month = prior.replace(day=28) + relativedelta(days=4)
        # Return as string in dd/mm/yyyy format
        return (next_month - relativedelta(days=next_month.day)).strftime("%Y-%m-%d")

    return None

def get_yoy_period_end(current_end: datetime) -> str:
    prior = current_end - relativedelta(years=1)
    return prior.strftime("%Y-%m-%d")


def gross_profit_margin(gross_profit, revenue):
    return safe_divide(gross_profit, revenue, multiplier=100)

def operating_profit_margin(operating_income, revenue):
    return safe_divide(operating_income, revenue, multiplier=100)

def pretax_profit_margin(pretax_income, revenue):
    return safe_divide(pretax_income, revenue, multiplier=100)

def pretax_margin(pretax_income, revenue):
    return safe_divide(pretax_income, revenue, multiplier=100)

def net_profit_margin(net_income, revenue):
    return safe_divide(net_income, revenue, multiplier=100)

def EBIT_margin(EBIT, revenue):
    return safe_divide(EBIT, revenue, multiplier=100)

def EBITDA_margin(EBITDA, revenue):
    return safe_divide(EBITDA, revenue, multiplier=100)

def return_on_assets(net_income, assets_start, assets_end):
    avg_assets = average(assets_start, assets_end)
    return safe_divide(net_income, avg_assets, multiplier=100)

def return_on_equity(net_income, equity_start, equity_end):
    avg_equity = average(equity_start, equity_end)
    return safe_divide(net_income, avg_equity, multiplier=100)

def debt_to_assets(debt, assets):
    return safe_divide(debt, assets, multiplier=1)

def get_growth_prior_period_end(current_end: datetime, ratio_key: str) -> str:
    """
    Returns the prior period end for growth-based ratios.
    Supports y/y and q/q based on the ratio key.
    """
    if "y/y" in ratio_key.lower() or "yoy" in ratio_key.lower():
        prior = current_end - relativedelta(years=1)
    elif "q/q" in ratio_key.lower() or "qoq" in ratio_key.lower():
        prior = current_end - relativedelta(months=3)
    else:
        # fallback for unexpected cases
        return None
    return prior.strftime("%Y-%m-%d")

def rate_of_change(current: float, prior: float, multiplier: float = 100) -> float:
    """
    Computes the percentage rate of change between a current and prior value.
    
    Formula:
        ((current - prior) / abs(prior)) * multiplier

    Returns None if prior is None or zero (to avoid division error).

    Args:
        current (float): Current period value.
        prior (float): Prior period value (must not be 0).
        multiplier (float): Multiplier for scaling (default is 100 for %).

    Returns:
        float or None: Rate of change, or None if invalid.
    """
    if current is None or prior in (None, 0):
        return None
    try:
        return ((current - prior) / abs(prior)) * multiplier
    except Exception:
        return None


# Mapping of required metrics for each ratio
RATIO_DEFINITIONS = {
    "Gross profit margin": {
        "function": gross_profit_margin,
        "required_metrics": {"Gross profit": "Gross profit", "Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja bruta",
        "ratio_name_eng": "Gross profit margin",
        "measure_unit": "%",
        "formula": "Profit brut / Venituri",
        "category": "Profitabilitate"
    },
    "Operating profit margin": {
        "function": operating_profit_margin,
        "required_metrics": {"Operating profit": "Operating profit","Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja operationala",
        "ratio_name_eng": "Operating profit margin",
        "measure_unit": "%",
        "formula": "Profit operational / Venituri",
        "category": "Profitabilitate"
    },
    "Pretax margin": {
        "function": pretax_margin,
        "required_metrics": {"Pretax profit": "Profit before tax", "Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja profit inainte de impozitare",
        "ratio_name_eng": "Pretax margin",
        "measure_unit": "%",
        "formula": "Profit inainte de impozitare / Venituri",
        "category": "Profitabilitate"
    },
    "Net profit margin": {
        "function": net_profit_margin,
        "required_metrics": {"Net profit": "Net profit a.m.", "Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja neta a profitului",
        "ratio_name_eng": "Net profit margin",
        "measure_unit": "%",
        "formula": "Profit net / Venituri",
        "category": "Profitabilitate"
    },
    "EBIT margin": {
        "function": EBIT_margin,
        "required_metrics": {"EBIT": "EBIT","Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja EBIT",
        "ratio_name_eng": "EBIT margin",
        "measure_unit": "%",
        "formula": "EBIT / Venituri",
        "category": "Profitabilitate"
    },
    "EBITDA margin": {
        "function": EBITDA_margin,
        "required_metrics": {"EBITDA": "EBITDA","Revenue": "Total operating revenues"},
        "ratio_name_ro": "Marja EBITDA",
        "ratio_name_eng": "EBITDA margin",
        "measure_unit": "%",
        "formula": "EBITDA / Venituri",
        "category": "Profitabilitate"
    },
    "ROA": {
        "function": return_on_assets,
        "required_metrics": {"Net profit": "Net profit a.m.","Total assets start": "Total assets_begin", "Total assets end":"Total assets"},
        "ratio_name_ro": "ROA",
        "ratio_name_eng": "ROA",
        "measure_unit": "%",
        "formula": "Profit net a.m. / Active totale medii",
        "category": "Profitabilitate"
    },
    "ROE": {
        "function": return_on_equity,
        "required_metrics": {"Net profit": "Net profit a.m.","Total equity start": "Total equity_begin", "Total equity end":"Total equity"},
        "ratio_name_ro": "ROE",
        "ratio_name_eng": "ROE",
        "measure_unit": "%",
        "formula": "Profit net a.m. / Capitaluri proprii medii",
        "category": "Profitabilitate"
    },
    "Debt/Assets": {
        "function": debt_to_assets,
        "required_metrics": {"Total debt": "Interest-bearing debt","Total assets": "Total assets"},
        "ratio_name_ro": "Datorii/Active",
        "ratio_name_eng": "Debt/Assets",
        "measure_unit": "%",
        "formula": "Datorii purtatoare de dobanda / Active total",
        "category": "Indatorare"
    },
    "Revenue growth y/y": {
    "function": rate_of_change,
    "required_metrics": {"Current revenue": "Revenue", "Prior revenue": "Revenue_prior"},
    "ratio_name_ro": "Rata de crestere venituri (an/an)",
    "ratio_name_eng": "Revenue growth y/y",
    "measure_unit": "%",
    "formula": "(Venituri curente - Venituri anterioare) / Venituri anterioare",
    "category": "Rate de crestere"
    },
    "Operating profit growth y/y": {
        "function": rate_of_change,
        "required_metrics": {"Current op profit": "Operating profit", "Prior op profit": "Operating profit_prior"},
        "ratio_name_ro": "Rata de crestere profit operational (an/an)",
        "ratio_name_eng": "Operating profit growth y/y",
        "measure_unit": "%",
        "formula": "(Profit op curent - Profit op anterior) / Profit op anterior",
        "category": "Rate de crestere"
    },
    "Net profit growth y/y": {
        "function": rate_of_change,
        "required_metrics": {"Current net profit": "Net profit a.m.", "Prior net profit": "Net profit a.m._prior"},
        "ratio_name_ro": "Rata de crestere profit net (an/an)",
        "ratio_name_eng": "Net profit growth y/y",
        "measure_unit": "%",
        "formula": "(Profit net curent - Profit net anterior) / Profit net anterior",
        "category": "Rate de crestere"
    }


    # Additional ratios can be added here
}

def calculate_and_store_ratio(DB_PATH, ticker, ratio_key, period_type, aggr_type):
    # Retrieve the ratio definition
    ratio_def = RATIO_DEFINITIONS[ratio_key]
    metrics_needed = tuple(ratio_def["required_metrics"].values())

    # Connect to DB and fetch relevant data
    conn = sqlite3.connect(DB_PATH)

    if period_type == "annual":
        query_raw = f"""
            SELECT 
                f.company_ticker,
                f.period_start,
                f.period_end,
                f.period_type,
                f.aggr_type,
                m.generalized_metric_eng AS metric,
                f.value
            FROM financial_data f
            JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
            WHERE f.company_ticker = ?
              AND f.period_type = 'annual'
              AND f.aggr_type = ?
              AND m.generalized_metric_eng IN ({','.join('?' for _ in metrics_needed)})"""
    
        params = [ticker, aggr_type] + list(metrics_needed)

    elif period_type == "quarter" and aggr_type == "cml":
        query_raw = f"""
            SELECT 
                f.company_ticker,
                f.period_start,
                f.period_end,
                f.period_type,
                f.aggr_type,
                m.generalized_metric_eng AS metric,
                f.value
            FROM financial_data f
            JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
            WHERE f.company_ticker = ?
              AND f.aggr_type = 'cml'
              AND (f.period_type = 'quarter' OR f.period_type = 'annual')
              AND m.generalized_metric_eng IN ({','.join('?' for _ in metrics_needed)})"""
        
        params = [ticker] + list(metrics_needed)

    elif period_type == "quarter" and aggr_type == "qtl":
        query_raw = f"""
            SELECT 
                f.company_ticker,
                f.period_start,
                f.period_end,
                f.period_type,
                f.aggr_type,
                m.generalized_metric_eng AS metric,
                f.value
            FROM financial_data f
            JOIN financial_metrics m ON f.metric_name_ro = m.metric_name_ro
            WHERE f.company_ticker = ?
              AND f.period_type = 'quarter'
              AND f.aggr_type = ?
              AND m.generalized_metric_eng IN ({','.join('?' for _ in metrics_needed)})"""
        
        params = [ticker, aggr_type] + list(metrics_needed)

    df_raw = pd.read_sql_query(query_raw, conn, params=params)

    if period_type == "annual":
        query_derived = f"""
            SELECT
                company_ticker,
                period_start,
                period_end,
                period_type,
                aggr_type,
                metric_name_eng AS metric,
                value
            FROM derived_metrics
            WHERE company_ticker = ?
              AND period_type = 'annual'
              AND aggr_type = ?
              AND metric_name_eng IN ({','.join('?' for _ in metrics_needed)})
        """
        params_derived = [ticker, aggr_type] + list(metrics_needed)

    elif period_type == "quarter" and aggr_type == "cml":
        query_derived = f"""
            SELECT
                company_ticker,
                period_start,
                period_end,
                period_type,
                aggr_type,
                metric_name_eng AS metric,
                value
            FROM derived_metrics
            WHERE company_ticker = ?
              AND aggr_type = 'cml'
              AND (period_type = 'quarter' OR period_type = 'annual')
              AND metric_name_eng IN ({','.join('?' for _ in metrics_needed)})
        """
        params_derived = [ticker] + list(metrics_needed)

    elif period_type == "quarter" and aggr_type == "qtl":
        query_derived = f"""
            SELECT
                company_ticker,
                period_start,
                period_end,
                period_type,
                aggr_type,
                metric_name_eng AS metric,
                value
            FROM derived_metrics
            WHERE company_ticker = ?
              AND period_type = 'quarter'
              AND aggr_type = ?
              AND metric_name_eng IN ({','.join('?' for _ in metrics_needed)})
        """
        params_derived = [ticker, aggr_type] + list(metrics_needed)

    df_derived = pd.read_sql_query(query_derived, conn, params=params_derived)
    # Combine both
    df = pd.concat([df_raw, df_derived], ignore_index=True)

    print(f"\n📊 Retrieved {len(df)} rows of raw + derived data for {ticker} - {ratio_key}")
    print(f"\n📊 [Step 1] Combined data preview for {ticker} | {ratio_key}")
    print(df.head(5))

    conn.close()
    df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", "", regex=False).str.replace(" ", ""), errors="coerce")
    if df.empty:
        return f"No data available for {ticker} - {ratio_key}"

    # ✅ Normalize numeric values (mixed comma/float-safe)
    def clean_numeric(val):
        """
        Cleans financial strings:
        - Removes commas and spaces
        - Converts to float safely
        - Leaves real decimals intact
        """
        if isinstance(val, str):
            val = val.replace(",", "").replace(" ", "").strip()
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
        
    # Pivot the data: one row per period_end
    df_pivot = df.pivot_table(
        index=["company_ticker", "period_start", "period_end", "period_type", "aggr_type"],
        columns="metric",
        values="value"
    ).reset_index()

    # Convert period_end to datetime
    df_pivot["period_start"] = pd.to_datetime(df_pivot["period_start"], format="%Y-%m-%d")
    df_pivot["period_end"] = pd.to_datetime(df_pivot["period_end"], format="%Y-%m-%d")


    # Compute prior_period_end using different logic for growth ratios
    ratio_key_lower = ratio_key.lower()

    if "growth" in ratio_key_lower:
        if "y/y" in ratio_key_lower or "yoy" in ratio_key_lower:
            growth_mode = "yoy"
        elif "q/q" in ratio_key_lower or "qoq" in ratio_key_lower:
            growth_mode = "qoq"
        else:
            raise ValueError(f"❌ Cannot determine growth type for: {ratio_key}")
        
        print(f"📈 Growth ratio detected → Using {growth_mode.upper()} logic for prior_period_end.")
        df_pivot["prior_period_end"] = df_pivot["period_end"].apply(lambda d: get_growth_prior_period_end(d, growth_mode))

    else:
        print(f"📊 Non-growth ratio → Using default logic based on period_type and aggr_type.")
        df_pivot["prior_period_end"] = df_pivot.apply(
            lambda row: get_prior_period_end(row["period_end"], row["period_type"], row["aggr_type"]),
            axis=1
        )


    print(f"\n🧹 [Step 2] Pivoted data (one row per period_end):")
    print(df_pivot.head(3))

    current_df = df_pivot.copy()
  
    current_df["prior_period_end"] = current_df["prior_period_end"].astype(str)
    current_df["period_end"] = current_df["period_end"].astype(str)

    print(f"\n⏳ [Step 3] With prior_period_end calculated:")
    print(current_df[["period_end", "prior_period_end"]].tail(3))

    # Create a prior_df that doesn't include "prior_period_end"
    prior_df = current_df.copy()
    prior_df = prior_df.drop(columns=["prior_period_end"], errors="ignore")
    prior_df = prior_df.rename(columns={"period_end": "prior_period_end"})

    # Merge
    suffix = "_prior" if "growth" in ratio_key.lower() else "_begin"
    merged = pd.merge(current_df, prior_df, how="left",
            on=["company_ticker", "prior_period_end"], suffixes=("", suffix))

    # Check if all required columns exist before debug print or computation
    required_columns = list(ratio_def["required_metrics"].values())
    missing_columns = [col for col in required_columns if col not in merged.columns]

    if missing_columns:
        print(f"⚠️ Skipping '{ratio_key}' for {ticker} ({period_type}, {aggr_type}) — missing metrics: {missing_columns}")
        return f"Skipped: missing columns {missing_columns} for {ratio_key}"
    
    print(f"\n🔁 [Step 4] Merged current vs prior:")
    print(merged[["company_ticker", "period_end", "prior_period_end"] + list(ratio_def["required_metrics"].values())].tail(3))

    # Calculate the ratio
    results = []
    for _, row in merged.iterrows():
        try:
            metric_values = [row.get(val) for val in ratio_def["required_metrics"].values()]
            print("🧪 Inputs:", metric_values)
            print("🧪 Ratio being computed:", ratio_key)

            for label, std_name in ratio_def["required_metrics"].items():
                print(f"🔍 {label} => {std_name}: {row.get(std_name)}")

            val = ratio_def["function"](*metric_values)
        except Exception:
            val = None

        results.append({
            "company_ticker": row["company_ticker"],
            "period_start": row["period_start"],            
            "period_end": row["period_end"],
            "period_type": row["period_type"],
            "aggr_type": row["aggr_type"],
            "ratio_name_eng": ratio_key,
            "ratio_name_ro": ratio_def["ratio_name_ro"],
            "measure_unit": ratio_def["measure_unit"],
            "value": val,
            "category":ratio_def["category"],
            "formula": ratio_def["formula"],
            "calculated_at": datetime.now().isoformat()
        })
        print(f"\n🔍 [Step 5] Computing ratio: {ratio_key} for {row['company_ticker']} | {row['period_type']} | {row['aggr_type']} | period_end: {row['period_end']}")
        for label, std_name in ratio_def["required_metrics"].items():
            print(f"   - {label}: {row.get(std_name)}")

        print(f"   ➕ Result: {val}")

    # Insert into financial_ratios table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_ratios (
            company_ticker TEXT,
            period_start DATE,
            period_end DATE,
            period_type TEXT,
            aggr_type TEXT,
            ratio_name_eng TEXT,
            ratio_name_ro TEXT,
            measure_unit TEXT,
            value REAL,
            category TEXT,
            formula TEXT,
            calculated_at TEXT,
            PRIMARY KEY (company_ticker, period_end, period_type, aggr_type, ratio_name_eng)
        )
    """)

    insert_query = """
        INSERT OR REPLACE INTO financial_ratios (
            company_ticker, period_start, period_end, period_type, aggr_type,
            ratio_name_eng, ratio_name_ro, measure_unit, value, category, formula, calculated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for r in results:
        cursor.execute(insert_query, (
            r["company_ticker"], 
            r["period_start"] if isinstance(r["period_start"], str) else r["period_start"].strftime("%Y-%m-%d"),  
            r["period_end"] if isinstance(r["period_end"], str) else r["period_end"].strftime("%Y-%m-%d"), 
            r["period_type"], r["aggr_type"],   
            r["ratio_name_eng"], r["ratio_name_ro"], r["measure_unit"], r["value"], r["category"],
            r["formula"], r["calculated_at"]
        ))

    conn.commit()
    conn.close()

    return f"{len(results)} rows inserted/updated for ratio '{ratio_key}' and ticker '{ticker}'"

tickers = ["AQ"] 

def run_all_ratios(DB_PATH, tickers):
    ratios = list(RATIO_DEFINITIONS.keys())
    period_types = ["annual", "quarter"]
    aggr_types = ["cml", "qtl"]

    for ticker in tickers:
        for ratio in ratios:
            for period_type in period_types:
                for aggr_type in aggr_types:
                    print(f"\n🔄 {ticker} | {ratio} | {period_type} | {aggr_type}")
                    calculate_and_store_ratio(DB_PATH, ticker, ratio, period_type, aggr_type)

run_all_ratios(DB_PATH, tickers)