from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .data_handler import (get_stock_overview, get_historical_stock_data, get_financial_statement, get_company_details_from_db,
                           get_grouped_financial_ratios, 
                           get_revenue_data, get_segment_revenue_notes, get_profit_and_margin_data, get_revenue_qtl_and_change_data, 
                           get_operating_profit_qtl_and_margin_data, get_net_profit_qtl_and_margin_data, get_chart_comment, 
                           get_revenue_annual_and_change_data, get_dividends, get_dividends_dps_and_growth, get_dividend_yield_history,
                           get_payout_ratio_history, get_dividends_to_fcfe_history, get_calendar_events, get_operating_profit_annual_and_margin_data,
                           get_net_profit_annual_and_margin_data)
import json
import sqlite3
import os
import logging

main = Blueprint('main', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db") 
# List of tickers
tickers = ["AQ", "WINE"]

@main.route('/')
def home():
    companies = []  # Fetch all companies for the dropdown
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT company_ticker, company_name FROM companies")
            companies = cursor.fetchall()
    except Exception as e:
        logging.error(f"Error fetching companies for the home page: {e}")

    # Convert to a list of dicts for the template
    companies_list = [{"company_ticker": ticker, "company_name": name} for ticker, name in companies if ticker in tickers]
    return render_template("home.html", companies=companies_list)



# Handling search form submission (GET)
@main.route('/analyze', methods=['GET'])
def analyze():
    selected_ticker = request.args.get('ticker')  
    if selected_ticker:
        return redirect(url_for('main.analysis', ticker=selected_ticker)) 
    return redirect(url_for('main.home'))  # If no ticker is entered, stay on home page

# Analysis page with financials selection
@main.route('/analysis/<ticker>', methods=['GET'])
def analysis(ticker):
    stock_info = get_stock_overview(ticker)
    historical_data = get_historical_stock_data(ticker)
    revenue_data = get_revenue_qtl_and_change_data(ticker)
    latest_quarter = revenue_data["periods"][-1] if revenue_data and revenue_data["periods"] else "N/A"
    comment_revenue_growth = get_chart_comment(ticker, "revenue_qtl_and_change_data", latest_quarter)
    comment_operating_profit=get_chart_comment(ticker, "operating_profit_qtl_and_margin_data", latest_quarter)
    comment_net_profit=get_chart_comment(ticker, "net_profit_qtl_and_margin_data", latest_quarter)

    # Get period type and aggregation type from request (default: annual cumulative)
    period_type = request.args.get('period_type', 'annual')
    aggr_type = request.args.get('aggr_type', 'cml')
    print(f"➡️ Requested period_type: {period_type}, aggr_type: {aggr_type}")
    pl_statement = get_financial_statement(ticker, "Profit&Loss", period_type, aggr_type)
    bs_statement = get_financial_statement(ticker, "Balance Sheet", period_type, aggr_type)
    cf_statement = get_financial_statement(ticker, "Cash Flow", period_type, aggr_type)
    grouped_ratios = get_grouped_financial_ratios(ticker, period_type, aggr_type)
    print("✅ Ratios statement sent to template:")
    print(json.dumps(grouped_ratios, indent=2, ensure_ascii=False))
    if "error" in stock_info:
        return f"<h1>{stock_info['error']}</h1>", 404

    business_description = stock_info.get("longBusinessSummary", "Descrierea companiei nu este disponibilă.")
    dividends=get_dividends(ticker)
    last=dividends[0] if dividends else {}
    previous = dividends[1] if len(dividends) > 1 else {}

    return render_template(
        "stock_analysis.html",
        ticker=ticker,
        business_description=business_description,
        historical_data=historical_data,
        pl_statement=pl_statement,
        bs_statement=bs_statement,
        cf_statement=cf_statement,
        grouped_ratios=grouped_ratios,
        selected_period_type=period_type,
        selected_aggr_type=aggr_type,
        latest_quarter=latest_quarter,
        comment_revenue_growth=comment_revenue_growth,
        comment_operating_profit=comment_operating_profit,
        comment_net_profit=comment_net_profit,
        #get_dividends
        DPS_yoy_change=last.get("dividends_yoy_change"),
        dividend_status=last.get("dividend_status", "").strip().lower(),
        last_amount=last.get("DPS_value"),
        payment_date=last.get("payment_date"),
        previous_payment_date=previous.get("payment_date"),
        last_ex_date=last.get("ex_dividend_date"),
        last_type=last.get("dividend_type"),
        last_frequency="Trimestrial",  # or from another field if stored
        dividend_yield=last.get("dividend_yield"),
        previous_dividend_yield=previous.get("dividend_yield"),  # optional
        payout_ratio=last.get("payout_ratio"),
        previous_payout_ratio=previous.get("payout_ratio"),      # optional
        **stock_info
    )

@main.route('/historical_data/<ticker>/<period>')
def historical_data(ticker, period):
    data=get_historical_stock_data(ticker, period)
    if not data:
        return jsonify({"error": "No available data"}), 404
    
    return jsonify(data)

# API endpoint to get financials dynamically
@main.route('/pl_data/<ticker>/<period_type>/<aggr_type>', methods=['GET'])
def get_pl_data(ticker, period_type, aggr_type):
    try:
        data=get_financial_statement(ticker, "Profit&Loss", period_type, aggr_type)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/bs_data/<ticker>/<period_type>/<aggr_type>', methods=['GET'])
def get_bs_data(ticker, period_type, aggr_type):
    try:
        data=get_financial_statement(ticker, "Balance Sheet", period_type, aggr_type)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/cf_data/<ticker>/<period_type>/<aggr_type>', methods=['GET'])
def get_cf_data(ticker, period_type, aggr_type):
    try:
        data=get_financial_statement(ticker, "Cash Flow", period_type, aggr_type)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main.route("/ratios_data/<ticker>/<period_type>/<aggr_type>")
def ratios_data(ticker, period_type, aggr_type):
    data = get_grouped_financial_ratios(ticker, period_type, aggr_type)
    
    return jsonify(data)

@main.route('/revenue_data/<ticker>')
def revenue_data(ticker):
    data = get_revenue_data(ticker)
    if not data:
        return jsonify({"labels": [], "values": []})
    return jsonify(data)

@main.route("/segment_revenue_data/<ticker>")
def segment_revenue_data(ticker):
    data = get_segment_revenue_notes(ticker)
    return jsonify(data)

@main.route("/profit_and_margin_data/<ticker>")
def profit_and_margin_data(ticker):
    data=get_profit_and_margin_data(ticker)
    return jsonify(data)

@main.route("/revenue_qtl_and_change_data/<ticker>")
def revenue_qtl_and_change_data(ticker):
    data = get_revenue_qtl_and_change_data(ticker)
    return jsonify(data)

@main.route("/operating_profit_qtl_and_margin_data/<ticker>")
def operating_profit_qtl_and_margin_data(ticker):
    data=get_operating_profit_qtl_and_margin_data(ticker)
    return jsonify(data)

@main.route("/net_profit_qtl_and_margin_data/<ticker>")
def net_profit_qtl_and_margin_data(ticker):
    data=get_net_profit_qtl_and_margin_data(ticker)
    return jsonify(data)

@main.route("/revenue_annual_and_change_data/<ticker>")
def revenue_annual_and_change_data(ticker):
    data = get_revenue_annual_and_change_data(ticker)
    return jsonify(data)

@main.route("/operating_profit_annual_and_margin_data/<ticker>")
def operating_profit_annual_and_margin_data(ticker):
    data = get_operating_profit_annual_and_margin_data(ticker)
    return jsonify(data)

@main.route("/net_profit_annual_and_margin_data/<ticker>")
def net_profit_annual_and_margin_data(ticker):
    data = get_net_profit_annual_and_margin_data(ticker)
    return jsonify(data)

@main.route("/dividends/dps_and_growth/<ticker>")
def dividends_dps_and_growth(ticker):
    data = get_dividends_dps_and_growth(ticker)
    return jsonify(data)

@main.route("/dividends/yield_history/<ticker>")
def dividend_yield_history(ticker):
    data = get_dividend_yield_history(ticker)
    return jsonify(data)

@main.route("/dividends/payout_ratio/<ticker>")
def payout_ratio_history(ticker):
    data = get_payout_ratio_history(ticker)
    return jsonify(data)

@main.route("/dividends/dividends_to_fcfe/<ticker>")
def dividends_to_fcfe_history(ticker):
    data = get_dividends_to_fcfe_history(ticker)
    return jsonify(data)


@main.route("/calendar")
def calendar_page():
    return render_template("calendar.html")


@main.route("/calendar/events")
def calendar_events():
    events = get_calendar_events()
    return jsonify(events)
