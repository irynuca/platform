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

# Import all your data_handler functions
from data_handler import (
    get_company_details_from_db,
    get_latest_stock_indicators,
    get_latest_net_income,
    get_next_earnings_date,
    get_stock_overview,
    get_financial_statement,
    get_grouped_financial_ratios,
    get_revenue_data,
    get_segment_revenue_notes,
    get_profit_and_margin_data,
    get_revenue_qtl_and_change_data,
    get_operating_profit_qtl_and_margin_data,
    get_net_profit_qtl_and_margin_data,
    get_dividends,
    get_dividends_dps_and_growth,
    get_dividend_yield_history,
    get_payout_ratio_history,
    get_dividends_to_fcfe_history,
)

# ---------------- TEST FUNCTIONS ---------------- #

def test_company_details(ticker):
    print("➡️ Testing get_company_details_from_db")
    print(get_company_details_from_db(ticker))
    print()

def test_stock_indicators(ticker):
    print("➡️ Testing get_latest_stock_indicators")
    print(get_latest_stock_indicators(ticker))
    print()

def test_net_income(ticker):
    print("➡️ Testing get_latest_net_income")
    print(get_latest_net_income(ticker))
    print()

def test_earnings_date(ticker):
    print("➡️ Testing get_next_earnings_date")
    print(get_next_earnings_date(ticker))
    print()

def test_full_stock_overview(ticker):
    print("➡️ Testing get_stock_overview")
    overview = get_stock_overview(ticker)
    for key, value in overview.items():
        print(f"{key}: {value}")
    print()

def test_financial_statement(ticker):
    print("➡️ Testing get_financial_statement")
    print(get_financial_statement(ticker, "Profit&Loss", "annual", "cml"))
    print()

def test_grouped_financial_ratios(ticker):
    print("➡️ Testing get_grouped_financial_ratios")
    print(get_grouped_financial_ratios(ticker, "annual", "cml"))
    print()

def test_revenue_data(ticker):
    print("➡️ Testing get_revenue_data")
    print(get_revenue_data(ticker))
    print()

def test_segment_revenue_notes(ticker):
    print("➡️ Testing get_segment_revenue_notes")
    print(get_segment_revenue_notes(ticker))
    print()

def test_profit_and_margin_data(ticker):
    print("➡️ Testing get_profit_and_margin_data")
    print(get_profit_and_margin_data(ticker))
    print()

def test_revenue_qtl_and_change_data(ticker):
    print("➡️ Testing get_revenue_qtl_and_change_data")
    print(get_revenue_qtl_and_change_data(ticker))
    print()

def test_operating_profit_qtl_and_margin_data(ticker):
    print("➡️ Testing get_operating_profit_qtl_and_margin_data")
    print(get_operating_profit_qtl_and_margin_data(ticker))
    print()

def test_net_profit_qtl_and_margin_data(ticker):
    print("➡️ Testing get_net_profit_qtl_and_margin_data")
    print(get_net_profit_qtl_and_margin_data(ticker))
    print()

def test_get_dividends(ticker):
    print("➡️ Testing get_dividends")
    print(get_dividends(ticker))
    print()

def test_get_dividends_dps_and_growth(ticker):
    print("➡️ Testing historical DPS and yoy change")
    print(get_dividends_dps_and_growth(ticker))
    print()

def test_get_dividend_yield_history(ticker):
    print("➡️ Testing historical dividend yield")
    print(get_dividend_yield_history(ticker))
    print()

def test_get_payout_ratio_history(ticker):
    print("➡️ Testing historical dividend payout ratio")
    print(get_payout_ratio_history(ticker))
    print()

def test_get_dividends_to_fcfe_history(ticker):
    print("➡️ Testing historical Dividend/FCFE ratio")
    print(get_dividends_to_fcfe_history(ticker))
    print()

# ---------------- RUNNER ---------------- #

test_functions = {
    "1": test_company_details,
    "2": test_stock_indicators,
    "3": test_net_income,
    "4": test_earnings_date,
    "5": test_full_stock_overview,
    "6": test_financial_statement,
    "7": test_grouped_financial_ratios,
    "8": test_revenue_data,
    "9": test_segment_revenue_notes,
    "10": test_profit_and_margin_data,
    "11": test_revenue_qtl_and_change_data,
    "12": test_operating_profit_qtl_and_margin_data,
    "13": test_net_profit_qtl_and_margin_data,
    "14": test_get_dividends,
    "15": test_get_dividends_dps_and_growth,
    "16": test_get_dividend_yield_history,
    "17": test_get_payout_ratio_history,
    "18": test_get_dividends_to_fcfe_history
}

def main():
    sample_ticker = "AQ"  # Default ticker for testing

    print("\n🛠 Available tests:")
    for key, func in test_functions.items():
        print(f"{key}: {func.__name__}")

    choices = input("\n🔎 Enter test numbers to run (comma-separated, example: 1,5,9): ").split(",")

    for choice in choices:
        func = test_functions.get(choice.strip())
        if func:
            func(sample_ticker)
        else:
            print(f"❌ Invalid choice: {choice}")

if __name__ == "__main__":
    main()
