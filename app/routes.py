from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .data_handler import (get_stock_overview, get_historical_stock_data, get_financial_statement, get_grouped_financial_ratios, 
                           get_revenue_data, get_segment_revenue_notes, get_profit_and_margin_data, get_revenue_qtl_and_change_data, 
                           get_operating_profit_qtl_and_margin_data, get_net_profit_qtl_and_margin_data, get_chart_comment, 
                           get_revenue_annual_and_change_data, get_dividends, get_dividends_dps_and_growth, get_dividend_yield_history,
                           get_payout_ratio_history, get_dividends_to_fcfe_history)
import json

main = Blueprint('main', __name__)

# List of tickers
tickers = ["AAG","ALR","ALT","ALU","AQ","ARM","AROBS","ARS","ARTE","ATB","BCM","BIO","BNET","BRD","BRK","BRM","BVB","CAOR","CBC","CMCM","CMF","CMP","CNTE","COMI","COTE","CRC","DIGI","EBS","ECT","EFO","EL","ELGS","ELJ","ELMA","ENP","EVER","FP","GREEN","H2O","IARV","IMP","INFINITY","LION","LONG","M","MCAB","MECE","MECF","NAPO","OIL","ONE","PBK","PE","PPL","PREB","PREH","PTR","RMAH","ROC1","ROCE","RPH","RRC","SAFE","SCD","SFG","SMTL","SNG","SNN","SNO","SNP","SOCP","STZ","TBK","TBM","TEL","TGN","TLV","TRANSI","TRP","TTS","TUFE","UAM","UCM","UZT","VESY","VNC","WINE","2P","4RT","AAB","ABN","ADISS","ADMY","ADS","AG","AGCM","ALB","ALCQ","ALDANI","ALRV","ALV","ALW","AMAL","ANIM","ANTA","APP","ARAX","ARCU","ARCV","ARJI","ARMT","ARO","ASC","ASP","AST","ATRD","AUXI","AVIO","AVSL","BADE","BALN","BAYAN","BBGA","BENTO","BIBU","BIOW","BLEA","BMW","BNAT","BONA","BRCR","BRNA","BUCS","BUCU","BUCV","CAB","CACU","CAIN","CBKN","CBOT","CC","CCOM","CEPO","CFED","CHIA","CHRD","CICE","CICO","CLAIM","CLUB","CMBU","CMIL","CMVX","COBL","COBU","COCB","COCR","CODE","COEC","COET","COKG","COKJ","COLK","COMY","CONK","CORO","COTM","COTN","COUT","COVB","CPHA","CPLB","CRMC","CRPC","CTT","CTUL","DAI","DBK","DENT","DIAS","DN","DOIS","DPW","DTE","DTG","DUPX","EEAI","ELCT","ELEL","ELER","ELJA","ELRD","ELV","ELZY","EMAI","EMTL","EOAN","EPN","FACY","FAMZ","FEP","FERO","FIMA","FLAO","FMAR","FOJE","FOMA","FOSB","FRB","GALF","GAOY","GDP","GGC","GHIM","GRIU","GROB","GSH","HAI","HEAL","HLEB","HUNT","IAMU","IANY","IASX","ICEV","ICMA","ICSH","IMMO","INCT","INMA","INOX","INSI","INTA","IORB","IPHI","IPRO","IPRU","IUBR","JTG","LCSI","LHA","LIH","LITO","MACO","MALI","MAM","MAMA","MEBY","MECA","MECP","MELE","MEOR","MEOY","MESA","MET","METT","METY","MIB","MILK","MINO","MINX","MOBD","MOBE","MOBG","MOBT","MODY","MOIB","MORA","MRDO","NAXY","NCHI","NEOL","NORD","NRF","NTEX","NUIA","OMAL","OMSE","PACY","PCTM","PELA","PETY","POBR","POTI","PPLI","PRAE","PRBU","PRDI","PRIB","PRIN","PRSN","PVBS","RANT","RCHI","REFE","REIT","RELE","REMM","REVA","RKOT","ROOF","RORX","RRD","SAP","SATU","SCBC","SCDM","SEBZ","SECE","SEOL","SEOM","SERC","SEVE","SIDG","SIEP","SIEP","SIFI","SIGS","SINA","SINT","SIRJ","SLBB","SNC","SOMR","SOPL","SOTA","SPTU","SPX","STKP","STNM","STOF","STOZ","TALD","TERA","TIGH","TRCS","TRGI","TRNG","TRSB","TRSK","TRVM","TSLA","TSND","TUAA","UARG","UCET","UNIR","UNISEM","UNVR","UPET","UPRR","URBA","URCB","UTGR","UZC","UZIN","VAC","VIAG","VIRO","VITK"]

# Home page with search bar and dropdown
@main.route('/')
def home():
    return render_template("home.html", tickers=tickers)  # ✅ Pass tickers to HTML

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


@main.route("/app-calender.html")
def calender():
    return render_template("app-calender.html", tickers=tickers)
