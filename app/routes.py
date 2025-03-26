from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .data_handler import get_yahoo_stock_price, get_historical_stock_data, get_pl_statement
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
    stock_info = get_yahoo_stock_price(ticker)
    historical_data = get_historical_stock_data(ticker)

    # Get period type and aggregation type from request (default: annual cumulative)
    period_type = request.args.get('period_type', 'annual')
    aggr_type = request.args.get('aggr_type', 'cml')

    pl_statement = get_pl_statement(ticker, period_type, aggr_type)

    if "error" in stock_info:
        return f"<h1>{stock_info['error']}</h1>", 404

    business_description = stock_info.get("longBusinessSummary", "Descrierea companiei nu este disponibilă.")

    return render_template(
        "stock_analysis.html",
        ticker=ticker,
        business_description=business_description,
        historical_data=historical_data,
        pl_statement=pl_statement,
        selected_period_type=period_type,
        selected_aggr_type=aggr_type,
        **stock_info
    )

# API endpoint to get financials dynamically
@main.route('/get_financials/<ticker>/<period_type>/<aggr_type>', methods=['GET'])
def get_financials(ticker, period_type, aggr_type):
    pl_statement = get_pl_statement(ticker, period_type, aggr_type)
    if not pl_statement:
        return jsonify({"error": "No financial data available"}), 404

    return jsonify(pl_statement)


@main.route('/historical_data/<ticker>/<period>')
def historical_data(ticker, period):
    data=get_historical_stock_data(ticker, period)
    if not historical_data:
        return jsonify({"error":"No available data"}), 404
    
    return jsonify(data)