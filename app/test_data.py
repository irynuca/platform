import sys
import os
import pandas as pd
from datetime import datetime

# Add the parent directory to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
COMPANY_INFO_FILE = os.path.join(DATA_DIR, "company_info.csv")  # Full path to CSV
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database


#------------------------ Test_data_handler.py upper part of stock_analysis.html---------------------------------------------------

from data_handler import (
    get_company_details_from_db,
    get_latest_stock_indicators,
    get_latest_net_income,
    get_next_earnings_date,
    get_stock_overview
)

def test_company_details(ticker):
    print("➡️ Testing get_company_details_from_db")
    details = get_company_details_from_db(ticker)
    print("Result:", details)
    print()

def test_stock_indicators(ticker):
    print("➡️ Testing get_latest_stock_indicators")
    indicators = get_latest_stock_indicators(ticker)
    print("Result:", indicators)
    print()

def test_net_income(ticker):
    print("➡️ Testing get_latest_net_income")
    net_income = get_latest_net_income(ticker)
    print("Result:", net_income)
    print()

def test_earnings_date(ticker):
    print("➡️ Testing get_next_earnings_date")
    earnings_date = get_next_earnings_date(ticker)
    print("Result:", earnings_date)
    print()

def test_full_stock_overview(ticker):
    print("➡️ Testing get_stock_overview")
    overview = get_stock_overview(ticker)
    for key, value in overview.items():
        print(f"{key}: {value}")
    print()


if __name__ == "__main__":
    # Replace with a real ticker from your DB
    sample_ticker = "AQ"

    test_company_details(sample_ticker)
    test_stock_indicators(sample_ticker)
    test_net_income(sample_ticker)
    test_earnings_date(sample_ticker)
    test_full_stock_overview(sample_ticker)



#--------------------Test if PL displays correctly in various combinations-----------------------------------------------------------------------------------
from data_handler import get_financial_statement
print(get_financial_statement("AQ", "Profit&Loss", "annual", "cml"))

import json
from data_handler import get_grouped_financial_ratios
print(get_grouped_financial_ratios("AQ", "annual", "cml"))

from data_handler import get_revenue_data
print(get_revenue_data("AQ"))

from data_handler import get_segment_revenue_notes
print(get_segment_revenue_notes("AQ"))

from data_handler import get_profit_and_margin_data
print(get_profit_and_margin_data("AQ"))