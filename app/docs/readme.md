# 🧾 Financial Data Pipeline - Script Guide

Welcome to the core data processing toolkit for financial statement extraction, validation, enrichment, and transformation. This guide documents the role of each script in the `/app` folder.

---

## 📂 Main Processing Scripts

### `data_collection.py`
**Purpose:** Extracts and normalizes notes from Excel files and writes results to the database.

- Locates rows by fuzzy keyword search (e.g., "cheltuieli cu dobânzile").
- Parses dates and period formats automatically.
- Stores clean structured output in the `notes` table.

---

### `check_financials.PY`
**Purpose:** Runs validation rules across statements to ensure data consistency and logic checks.

- Performs static and dynamic breakdown checks (e.g., total assets = equity + liabilities).
- Logs results and exports to Excel.
- Supports rule expansion using generalized metric hierarchy.

---

### `derived_metrics.py`
**Purpose:** Creates calculated metrics from base financial values.

- Examples: EBITDA, Net Debt, Working Capital.
- Stores results in a separate `derived_metrics` table for easier access and analysis.

---

### `ratios.py`
**Purpose:** Computes key financial ratios using both raw and derived data.

- Examples: Return on Equity, Gross Margin, Leverage.
- Output can be exported or stored in a `ratios` table.

---

### `wide_to_long_csv.py`
**Purpose:** Converts manually structured or legacy Excel files from wide format to long format.

- Automatically extracts period metadata.
- Creates normalized records suitable for DB ingestion.

---

## 🔧 Utilities & Support Scripts

### `helpers.py`
**Purpose:** Contains utility functions and constants shared across scripts.

- Path handling
- File cleanup
- Logging helpers

---

### `seed_aliases.py`
**Purpose:** Seeds a table of aliases for metric names (e.g., translations, fuzzy match alternatives).

- Helps when different companies use inconsistent naming for the same metric.
- Populate once or refresh periodically.

---

## 📄 How to Use

Typical workflow:

```bash
# Step 1: Extract & store structured data
python data_collection.py

# Step 2: Validate business logic and breakdowns
python check_financials.PY

# Step 3: Derive additional metrics (EBITDA, Net Debt)
python derived_metrics.py

# Step 4: Calculate final ratios
python ratios.py
