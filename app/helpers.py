# helpers.py
# ----------
# Utility functions for metric normalization using the `metric_aliases` table.
# These allow the webapp to map raw company-reported metrics to standardized names
# by leveraging a curated alias list stored in the database.

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database


def get_standardized_metric_name(DB_PATH, raw_metric_name):
    """
    Look up the standardized metric name for a given alias.
    This is used when importing or processing raw financial statement data.

    Parameters:
    - DB_PATH: str, path to the SQLite database.
    - raw_metric_name: str, name reported by the company or scraped externally.

    Returns:
    - str: The standardized metric name, or None if no match found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT standardized_metric FROM metric_aliases WHERE alias = ?", (raw_metric_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_aliases_for(DB_PATH, standardized_name):
    """
    Retrieve all known aliases for a given standardized metric name.
    This is useful when querying the DB or scraping and needing to match alternate labels.

    Parameters:
    - DB_PATH: str, path to the SQLite database.
    - standardized_name: str, your platform's standardized metric label.

    Returns:
    - List[str]: All alias names that map to this standardized metric.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT alias FROM metric_aliases WHERE standardized_metric = ?", (standardized_name,))
    aliases = [row[0] for row in cursor.fetchall()]
    conn.close()
    return aliases

result1=get_standardized_metric_name(DB_PATH, "Beneficiile angajatilor - termen lung")
result2=get_aliases_for(DB_PATH, "Short-term debt")
print(result1)
print(result2)