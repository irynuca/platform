# seed_aliases.py
# ----------------
# This script initializes and seeds the `metric_aliases` table in your SQLite database.
# It uses a HYBRID approach: manually curated aliases from METRIC_ALIASES + automatically
# inferred aliases from your existing `financial_metrics` table.
#
# 📌 Run this during setup or whenever you want to refresh your alias mapping.
# ✅ Manual aliases = high quality, curated
# ✅ Auto aliases = scale from what's already in your DB
#
# ➕ You can store a README/USAGE guide alongside this file (see `alias_guide.md`).

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database

# ✅ Manually curated dictionary of standardized metrics and their known aliases, per language
METRIC_ALIASES = {
    "Short-term debt": {
        "ro": [
            "Datorii curente purtătoare de dobândă",
            "Imprumuturi bancare pe termen scurt"
        ],
        "en": [
            "Short-term bank borrowings",
            "Current bank liabilities",
            "Borrowings due within 1 year"
        ]
    },
    "Long-term debt": {
        "ro": [
            "Datorii bancare pe termen lung",
            "Imprumuturi bancare - termen lung",
            "Imprumuturi bancare pe termen lung"
        ],
        "en": [
            "Long-term bank borrowings",
            "LT loans"
        ]
    },
    "Interest-bearing debt": {
        "en": [
            "Total bank loans",
            "Bank debt",
            "Total debt"
        ]
    }
}

def seed_metric_aliases(DB_PATH):
    """
    Create the `metric_aliases` table and populate it with:
    1. Manual alias mappings from METRIC_ALIASES
    2. Automatically extracted aliases from financial_metrics table
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Create the alias table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_aliases (
            alias TEXT PRIMARY KEY,
            standardized_metric TEXT NOT NULL,
            language TEXT DEFAULT NULL,
            country TEXT DEFAULT NULL,
            source TEXT DEFAULT NULL
        )
    """)

    # Step 2: Seed manual aliases (by language)
    for std_name, lang_dict in METRIC_ALIASES.items():
        for lang, aliases in lang_dict.items():
            for alias in aliases:
                cursor.execute(
                    "INSERT OR REPLACE INTO metric_aliases (alias, standardized_metric, language, country, source) VALUES (?, ?, ?, ?, ?)",
                    (alias, std_name, lang, "Romania", "manual")
                )

    # Step 3: Auto-generate from financial_metrics (with country)
    for lang, col in [("en", "metric_name_eng"), ("ro", "metric_name_ro")]:
        cursor.execute(f"""
            INSERT OR REPLACE INTO metric_aliases (alias, standardized_metric, language, country, source)
            SELECT DISTINCT {col}, generalized_metric_eng, ?, 'Romania', 'auto_generated'
            FROM financial_metrics
            WHERE {col} IS NOT NULL
              AND generalized_metric_eng IS NOT NULL
              AND {col} != generalized_metric_eng
        """, (lang,))

    conn.commit()
    conn.close()
    print("✅ metric_aliases table seeded (manual + auto).")


# Example usage (uncomment to run directly)
#seed_metric_aliases(DB_PATH)
