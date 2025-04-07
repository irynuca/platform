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

# Load and print CSV to check if it's loading correctly
if os.path.exists(COMPANY_INFO_FILE):
    df = pd.read_csv(COMPANY_INFO_FILE)
    print("✅ CSV File Loaded Successfully!")
    print(df.head())  # Print first few rows of CSV
else:
    print("❌ ERROR: CSV file not found!")

import yfinance as yf

ticker = "SNP.RO"  # Change this to test different stocks

stock = yf.Ticker(ticker)

# Fetch historical stock prices (1 day)
data = stock.history(period="1d")
print("\n📊 STOCK PRICE HISTORY:")
print(data)

# Fetch all fundamental company details
info = stock.info

# Check if 'earningsTimestamp' exists
if "earningsTimestamp" in info:
    earnings_date = datetime.utcfromtimestamp(info["earningsTimestamp"]).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"\n📅 Next Earnings Date: {earnings_date}")
else:
    print("\n❌ Earnings date not available for this stock.")

print("\n📋 FUNDAMENTAL DATA (stock.info):")
for key, value in info.items():
    print(f"{key}: {value}")


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