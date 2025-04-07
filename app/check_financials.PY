import sqlite3
import pandas as pd

DB_PATH = r"C:\Irina\Mosaiq8\app\data\financials.db"
THRESHOLD = 5
OUTPUT_FILE = "validation_results.xlsx"

### TO DO ###
# DE ACOMODAT Gain from bargain acquisition
# Non-numeric value skipped for 'change in provisions, net' at 31/03/2023S
# DE ADAUGAT REGULI PENTRU CF STATEMENT

def fetch_validation_rules():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM validation_rules WHERE is_active = 1", conn)
    conn.close()
    print(df)
    return df

def resolve_dynamic_components(target_metric):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT DISTINCT fm.generalized_metric_eng, fd.metric_parent
        FROM financial_metrics fm
        JOIN financial_data fd
          ON TRIM(LOWER(fm.metric_name_ro)) = TRIM(LOWER(fd.metric_name_ro))
        WHERE TRIM(LOWER(fd.metric_parent)) = ?
    """

    df = pd.read_sql(query, conn, params=(target_metric.strip().lower(),))
    conn.close()

    if df.empty:
        print(f"⚠️ No components found for parent: '{target_metric}'")
    #else:
        #print(f"✅ Components for '{target_metric}':")
        #print(df)

    return df['generalized_metric_eng'].dropna().str.strip().str.lower().unique().tolist()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df_data = pd.read_sql("SELECT * FROM financial_data", conn)
    df_metrics = pd.read_sql("SELECT * FROM financial_metrics", conn)
    conn.close()

    # Normalize
    df_data['metric_name_ro'] = df_data['metric_name_ro'].str.strip()
    df_metrics['metric_name_ro'] = df_metrics['metric_name_ro'].str.strip()
    map_dict = df_metrics.set_index('metric_name_ro')['generalized_metric_eng'].to_dict()
    df_data['generalized_metric_eng'] = df_data['metric_name_ro'].map(map_dict)

    # Split by statement name and aggr_type
    df_bs = df_data[df_data['statement_name'].str.lower().str.strip() == "balance sheet"]
    df_pl = df_data[df_data['statement_name'].str.lower().str.strip() == "profit&loss"]
    df_pl_cml = df_pl[df_pl['aggr_type'].str.lower() == "cml"]
    df_pl_qtl = df_pl[df_pl['aggr_type'].str.lower() == "qtl"]

    drop_cols = ["statement_type", "period_start", "currency", "metric_name_ro"]
    for df in [df_bs, df_pl_cml, df_pl_qtl]:
        df.drop(columns=drop_cols, errors="ignore", inplace=True)

    # Pivot
    dfs = {}
    for label, df in zip(['bs', 'pl_cml', 'pl_qtl'], [df_bs, df_pl_cml, df_pl_qtl]):
        dupes = df[df.duplicated(subset=['company_ticker', 'generalized_metric_eng', 'aggr_type', 'period_end'], keep=False)]
        if not dupes.empty:
            dupes.to_csv(f"pivot_duplicates_{label}.csv", index=False)
            raise ValueError(f"❌ Duplicates in {label} — check pivot_duplicates_{label}.csv")

        pivot = df.pivot(index=['company_ticker', 'generalized_metric_eng', 'aggr_type'],
                         columns='period_end', values='value').reset_index()
        dfs[label] = pivot
    
    
    
    # Save all to Excel
    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        dfs['pl_cml'].to_excel(writer, sheet_name="PL_CML", index=False)
        dfs['pl_qtl'].to_excel(writer, sheet_name="PL_QTL", index=False)
        dfs['bs'].to_excel(writer, sheet_name="BS", index=False)

    return dfs['pl_cml'], dfs['pl_qtl'], dfs['bs']

def validate_pivot_matrix(pivot_df, rule_df, threshold=5):
    results = []

    period_cols = [col for col in pivot_df.columns if col not in ['company_ticker', 'generalized_metric_eng', 'aggr_type']]
    pivot_df['generalized_metric_eng'] = pivot_df['generalized_metric_eng'].str.strip().str.lower()

    for _, rule in rule_df.iterrows():
        rule_name = rule["rule_name"]
        target = rule["target_metric"].strip().lower()
        method = rule.get("match_method", "static")

        #print(f"\n🔍 Evaluating rule: {rule_name} | target: {target} | method: {method}")

        if method == "dynamic":
            components = resolve_dynamic_components(target)
        else:
            components = rule["static_components"].split(",") if rule["static_components"] else []
            components = [c.strip().lower() for c in components]

        #print(f"📦 Components: {components}")

        for _, row in pivot_df.iterrows():
            if row['generalized_metric_eng'] != target:
                continue

            company = row['company_ticker']
            aggr = row['aggr_type']

            for period in period_cols:
                target_value = row.get(period)

                if pd.isna(target_value):
                    results.append({
                        "company_ticker": company,
                        "aggr_type": aggr,
                        "period_end": period,
                        "rule_name": rule_name,
                        "target_value": None,
                        "component_sum": None,
                        "diff": None,
                        "status": "missing target",
                        "components_found": None
                    })
                    continue

                # Get component values
                component_values = []
                components_found = []

                for comp in components:
                    match = pivot_df[
                        (pivot_df['company_ticker'] == company) &
                        (pivot_df['aggr_type'] == aggr) &
                        (pivot_df['generalized_metric_eng'] == comp)
                    ]
                    if not match.empty:
                        val = match.iloc[0].get(period)
                        try:
                            val = float(str(val).replace(",", "").strip())  # handle commas, strings
                            component_values.append(val)
                            components_found.append(comp)
                        except:
                            print(f"⚠️ Non-numeric value skipped for '{comp}' at {period}: {val}")

                if not component_values:
                    status = "missing components"
                    comp_sum = None
                    diff = None
                else:
                    comp_sum = sum(component_values)
                    try:
                        target_value = float(str(target_value).replace(",", "").strip())
                    except:
                        print(f"⚠️ Non-numeric target value at {period} for {target}: {target_value}")
                        target_value = None
                    if target_value is None or comp_sum is None:
                        status = "missing target or components"
                        diff = None
                    else:
                        diff = round(target_value - comp_sum, 2)
                        status = "ok" if abs(diff) <= threshold else "fail"

                results.append({
                    "company_ticker": company,
                    "aggr_type": aggr,
                    "period_end": period,
                    "rule_name": rule_name,
                    "target_value": target_value,
                    "component_sum": comp_sum,
                    "diff": diff,
                    "status": status,
                    "components_found": ", ".join(components_found) if components_found else None
                })

    return pd.DataFrame(results)

# Load data and rules
pl_cml, pl_qtl, bs = load_data()
rules = fetch_validation_rules()

# Validate each
results_cml = validate_pivot_matrix(pl_cml, rules)
results_qtl = validate_pivot_matrix(pl_qtl, rules)
results_bs = validate_pivot_matrix(bs, rules)

# Combine
final_results = pd.concat([results_cml, results_qtl, results_bs], ignore_index=True)

# Save
with pd.ExcelWriter("validation_results.xlsx", engine="openpyxl", mode="a") as writer:
    final_results.to_excel(writer, sheet_name="Validation_Results", index=False)
