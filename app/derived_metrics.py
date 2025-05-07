# derived_metrics.py
# -------------------------------------------------------------------------------------------------------------------------------------------------------
# This module defines and calculates derived financial metrics that are not directly reported in the financial statements,
# but are essential for valuation and fundamental analysis (e.g., EBIT, EBITDA, Net Debt, FCFF, etc).

# ✅ Uses `generalized_metric_eng` as the unified name for calculations.
# ✅ Integrates with `helpers.py` to resolve all known aliases for a standardized metric name

#TO DO:
# - de acomodat cazul in care daca compania are datorii purtatoare de dobanda>0 atunci, interest_expense este obligatoriu (dupa ce adauog interest expense)
# - de completat tickers list
# - de completat DERIVED_METRIC_DEFINITIONS cu alti indicatori

import sqlite3
import pandas as pd
import os
from datetime import datetime
from helpers import get_aliases_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database


def calculate_ebit(net_income, interest_expense, taxes):
    if net_income is None or taxes is None:
        return None
    interest_expense = interest_expense or 0
    return net_income + (-interest_expense) +(-taxes)


def calculate_ebitda(net_income, interest_expense, taxes, depreciation_amortization):
    if net_income is None or taxes is None or depreciation_amortization is None:
        return None  # Net income and taxes are mandatory
    interest_expense = interest_expense or 0
    return net_income + (-interest_expense) + (-taxes) + (-depreciation_amortization)

def calculate_interest_bearing_debt(long_term_debt, long_term_debt_current, short_term_debt):
    if long_term_debt is None and long_term_debt_current is None and short_term_debt is None:
        print("⚠️ No debt fields found — assuming zero interest-bearing debt.")
    return (long_term_debt or 0) + (long_term_debt_current or 0) + (short_term_debt or 0)

def calculate_net_debt(interest_bearing_debt, cash_and_equivalents):
    if interest_bearing_debt is None:
        return None
    return interest_bearing_debt - (cash_and_equivalents or 0)

def calculate_FCFE(net_operating_cash_flow, capex, net_borrowings):
    if net_operating_cash_flow is None or capex is None:
        print("❌ Missing required fields: Operating Cash Flow or CAPEX.")
        return None

    net_borrowings = net_borrowings or 0  # Treat None as 0
    return net_operating_cash_flow - capex + net_borrowings

def calculate_capex(purchases_of_ppe, purchases_of_intangibles):
    if purchases_of_ppe is None:
        print("❌ CAPEX data missing — cannot compute.")
        return None
    purchases_of_intangibles=purchases_of_intangibles or 0
    return -(purchases_of_ppe+purchases_of_intangibles)

def calculate_net_borrowings(repayment_lt, repayment_st, proceeds_lt, proceeds_st):
    all_missing = all(x is None for x in [repayment_lt, repayment_st, proceeds_lt, proceeds_st])
    
    if all_missing:
        print("⚠️ All net borrowing fields are missing — assuming zero.")
    
    total_repayment = (repayment_lt or 0) + (repayment_st or 0)
    total_proceeds = (proceeds_lt or 0) + (proceeds_st or 0)
    
    return total_proceeds + total_repayment


DERIVED_METRIC_DEFINITIONS = {
    "EBIT": {
        "function": calculate_ebit,
        "required_metrics": {"Net profit": "Net profit a.m.","Interest": "Interest expense", "Tax": "Income tax expense"},
        "metric_name_ro": "EBIT",
        "metric_name_eng": "EBIT",
        "formula": "Profit net + Cheltuieli cu dobanzile + Impozit pe profit"
    },
    "EBITDA": {
        "function": calculate_ebitda,
        "required_metrics": {"Net profit": "Net profit a.m.","Interest": "Interest expense", "Tax": "Income tax expense", "Depreciation and amortisation":"Depreciation and amortization"},
        "metric_name_ro": "EBITDA",
        "metric_name_eng": "EBITDA",
        "formula": "Profit net + Cheltuieli cu dobanzile + Impozit pe profit + Depreciere & amortizare"
    },
    "Interest-bearing debt": {
        "function": calculate_interest_bearing_debt,
        "required_metrics": {"Long-term debt": "Long-term bank borrowings", "Long=term debt due soon": "Long-term bank borrowings (ST)", "Short-term debt": "Short-term bank borrowings"},
        "metric_name_eng": "Interest-bearing debt",
        "metric_name_ro": "Datorii purtatoare de dobanda",
        "formula": "Datorii purtatoare de dobanda pe termen lung + Datorii purtatoare de dobanda pe termen scurt"
    },
    "Net debt": {
        "function": calculate_net_debt,
        "required_metrics": {"Interest-bearing debt": "Interest-bearing debt", "Cash and equivalents": "Cash and cash equivalents"},
        "metric_name_eng": "Net debt",
        "metric_name_ro": "Datorie neta",
        "formula": "Datorii purtatoare de dobanda - Numerar si echivalente de numerar"
    },
    "Capex": {
        "function": calculate_capex,
        "required_metrics": {"Purchases of property, plant and equipment":"Purchases of property, plant and equipment", "Purchases of intangible assets": "Purchases of intangible assets"},
        "metric_name_eng": "Capex",
        "metric_name_ro": "Capex",
        "formula": "Plati pentru achizitia de imobilizari corporale+Plati pentru achizitia de imobilizari necorporale"
    },
    "Net borrowings": {
        "function": calculate_net_borrowings,
        "required_metrics": {"Repayment of long-term borrowings":"Repayment of long-term borrowings", 
                             "Repayment of short-term borrowings": "Repayment of short-term borrowings", 
                             "Proceeds from long-term borrowings":"Proceeds from long-term borrowings", 
                             "Proceeds from short-term borrowings":"Proceeds from short-term borrowings"},
        "metric_name_eng": "Net borrowings",
        "metric_name_ro": "Imprumuturi nete",
        "formula": "Plati ale imprumuturilor bancare pe termen lung+Plati ale imprumuturilor bancare pe termen scurt+Trageri din imprumuturi bancare pe termen scurt+Trageri din imprumuturi bancare pe termen lung"
    },
    "FCFE": {
        "function": calculate_FCFE,
        "required_metrics": {"Net operating cash flow":"Net operating cash flow", "Capex": "Capex", "Net borrowings": "Net borrowings"},
        "metric_name_eng": "FCFE",
        "metric_name_ro": "FCFE",
        "formula": "Numerar net din exploatare-Capex+Imprumuturi nete"
    },
    
    # More metrics can be added here
}

# ------------------------------
# Derived Metric Calculation
# ------------------------------
def calculate_and_store_derived_metric(DB_PATH, ticker, metric_key, period_type, aggr_type):
    if metric_key not in DERIVED_METRIC_DEFINITIONS:
        print(f"❌ Metric '{metric_key}' is not defined in DERIVED_METRIC_DEFINITIONS.")
        return None

    metric_def = DERIVED_METRIC_DEFINITIONS[metric_key]
    std_metric = metric_def["metric_name_eng"]
    metric_labels = metric_def["required_metrics"]

    # Step 1: Query raw data using standardized names only (assuming data already normalized)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"""
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
          AND f.period_type = ?
          AND f.aggr_type = ?
          AND m.generalized_metric_eng IN ({','.join('?' for _ in metric_labels.values())})
    """
    params = [ticker, period_type, aggr_type] + list(metric_labels.values())
    df_raw = pd.read_sql_query(query, conn, params=params)

    query_notes = f"""
    SELECT 
        n.company_ticker,
        n.period_start,
        n.period_end,
        n.period_type,
        n.aggr_type,
        m.generalized_metric_eng AS metric,
        n.value
    FROM notes n
    JOIN financial_metrics m
        ON n.note_element = m.metric_name_ro
       AND n.company_ticker = m.company_ticker
    WHERE n.company_ticker = ?
      AND n.period_type = ?
      AND n.aggr_type = ?
      AND m.generalized_metric_eng IN ({','.join('?' for _ in metric_labels.values())})
"""
    params_notes = [ticker, period_type, aggr_type] + list(metric_labels.values())

    df_notes = pd.read_sql_query(query_notes, conn, params=params_notes)
    #df_notes["metric"] = df_notes["note_element"]  # unify column names
    df_notes = df_notes[["company_ticker", "period_start", "period_end", "period_type", "aggr_type", "metric", "value"]]

    print(df_notes)
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
          AND period_type = ?
          AND aggr_type = ?
          AND metric_name_eng IN ({','.join('?' for _ in metric_labels.values())})
    """
    df_derived = pd.read_sql_query(query_derived, conn, params=params)

    # Combine both
    df = pd.concat([df_raw, df_derived, df_notes], ignore_index=True)
    conn.close()

    if df.empty:
        print(f"⚠️ No relevant data found for ticker '{ticker}' and metric '{metric_key}' — skipping.")
        return None

    # Clean numeric values
    df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", "", regex=False).str.replace(" ", ""), errors="coerce")

    #print(f"📌 Final combined dataset shape: {df.shape}")
    #print("📌 Unique metrics found:", df["metric"].unique())


    # Pivot the data for easy access
    df_pivot = df.pivot_table(
        index=["company_ticker", "period_start", "period_end", "period_type", "aggr_type"],
        columns="metric",
        values="value"
    ).reset_index()
    missing_cols = [m for m in metric_labels.values() if m not in df_pivot.columns]
    if missing_cols:
        print("⚠️ Missing columns in pivot:", missing_cols)
    print(df_pivot)
    results = []
    for _, row in df_pivot.iterrows():
        try:
            args = [row.get(std_name) for std_name in metric_labels.values()]
            #print("🧪 Inputs:", args)
            #print("🧪 Metric being computed:", std_metric)

            for label, std_name in metric_labels.items():
                print(f"🔍 {label} => {std_name}: {row.get(std_name)}")
                #print("📎 Required metrics:", metric_labels)

            val = metric_def["function"](*args)
        except Exception:
            val = None

        results.append({
            "company_ticker": row["company_ticker"],
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "period_type": row["period_type"],
            "aggr_type": row["aggr_type"],
            "metric_name_eng": std_metric,
            "metric_name_ro": metric_def["metric_name_ro"],
            "value": val,
            "formula": metric_def["formula"],
            "calculated_at": datetime.now().isoformat()
        })

    # Store results into derived_metrics table
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS derived_metrics (
            company_ticker TEXT,
            period_start DATE
            period_end DATE,
            period_type TEXT,
            aggr_type TEXT,
            metric_name_eng TEXT,
            metric_name_ro TEXT,
            value REAL,
            formula TEXT,
            calculated_at TEXT,
            PRIMARY KEY (company_ticker, period_end, period_type, aggr_type, metric_name_eng)
        )
    """)

    insert_query = """
        INSERT OR REPLACE INTO derived_metrics (
            company_ticker, period_start, period_end, period_type, aggr_type,
            metric_name_eng, metric_name_ro, value, formula, calculated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for r in results:
        cursor.execute(insert_query, (
            r["company_ticker"], r["period_start"], r["period_end"], r["period_type"], r["aggr_type"],
            r["metric_name_eng"], r["metric_name_ro"], r["value"], r["formula"], r["calculated_at"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ Stored {len(results)} derived rows for '{metric_key}' and '{ticker}'")


# ------------------------------
# Batch Derived Metrics Runner
# ------------------------------

tickers = ["AQ"]  # Replace with dynamic ticker list if needed

def run_all_derived_calculations(DB_PATH, tickers):
    # Create table once up front
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS derived_metrics (
            company_ticker TEXT,
            period_start DATE,
            period_end DATE,
            period_type TEXT,
            aggr_type TEXT,
            metric_name_eng TEXT,
            metric_name_ro TEXT,
            value REAL,
            formula TEXT,
            calculated_at TEXT,
            PRIMARY KEY (company_ticker, period_end, period_type, aggr_type, metric_name_eng)
        )
    """)
    conn.commit()
    conn.close()

    # Now run metrics in proper order
    metric_keys = [
        "EBIT",
        "EBITDA",
        "Interest-bearing debt",  # dependency
        "Net debt",
        "Capex",
        "Net borrowings",
        "FCFE"              
    ]

    period_types = ["annual", "quarter"]
    aggr_types = ["cml", "qtl"]

    for ticker in tickers:
        for metric in metric_keys:
            for period_type in period_types:
                for aggr_type in aggr_types:
                    print(f"\n🔄 {ticker} | {metric} | {period_type} | {aggr_type}")
                    calculate_and_store_derived_metric(DB_PATH, ticker, metric, period_type, aggr_type)


run_all_derived_calculations(DB_PATH, ["AQ"])
