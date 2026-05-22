from flask import Flask, jsonify,request
import yfinance as yf
import pandas as pd
import numpy as np
from flask_cors import CORS
from services.upstox_service import (
    market_api,
    options_api,
    ACCESS_TOKEN
)
import requests

app = Flask(__name__)

@app.route('/')
def home():
    # This is what the user sees in their browser
    return """
    <html>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h1>Server Status: Online</h1>
            <p>Greetings! This page is being served by Python and Flask.</p>
        </body>
    </html>
    """


@app.route('/fundamentals/<symbol>')
def fundamentals(symbol):

    try:
        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info
        information = ticker.financials
        df= information.to_json
    

        data = {
            "symbol": symbol,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            # "cash_flow": info.get("trailingEps"),
            "revenue": info.get("totalRevenue"),
            "revenueGrowth": info.get("revenueGrowth"),
            "profit_margin": info.get("profitMargins"),
            "dividend_yield": info.get("dividendYield"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "profitMargins": info.get("profitMargins"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            
        }
        print("?????????????????????????????")
        print(information)
        print("?????????????------Type-------????????????????")
        print(type(information))
        print(df)

        return jsonify(info)
        # return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})




# Dividends Stability Analyzer and Dividend History API

@app.route("/dividend/<symbol>")   # Dividend Stability
def dividend_history(symbol):

    try:
        ticker = yf.Ticker(symbol + ".NS")

        dividends = ticker.dividends

        if dividends.empty:
            return jsonify({"symbol": symbol, "dividends": []})

        df = dividends.reset_index()
        df["year"] = df["Date"].dt.year

        yearly = df.groupby("year")["Dividends"].sum().reset_index()

        result = []

        for _, row in yearly.iterrows():
            result.append({
                "year": int(row["year"]),
                "dividend": round(float(row["Dividends"]), 2)
            })

        return jsonify({
            "symbol": symbol,
            "dividends": result
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# Financial Health Checkup API
# -----------------------------

def get_health_status(metric, value):

    if value is None:
        return "unknown"

    if metric == "roe":
        return "good" if value > 0.15 else "weak"

    if metric == "debt_to_equity":
        return "good" if value < 100 else "risky"

    if metric == "revenue_growth":
        return "good" if value > 0.10 else "slow"

    if metric == "current_ratio":
        return "good" if value > 1.5 else "weak"

    return "unknown"


def calculate_health_score(roe, de, rev_growth, curr_ratio):

    score = 0

    if roe is not None and roe > 0.15:
        score += 25

    if de is not None and de < 100:
        score += 25

    if rev_growth is not None and rev_growth > 0.10:
        score += 25

    if curr_ratio is not None and curr_ratio > 1.5:
        score += 25

    return score

# -----------------------------
# Financial Health Checkup
# -----------------------------
@app.route('/health/<symbol>')
def check_health(symbol):

    try:

        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.get_info()

        roe = info.get("returnOnEquity") or 0
        de = info.get("debtToEquity") or 0
        rev_growth = info.get("revenueGrowth") or 0
        curr_ratio = info.get("currentRatio") or 0

        score = calculate_health_score(roe, de, rev_growth, curr_ratio)

        data = {
            "symbol": symbol,
            "health_score": score,

            "metrics": {

                "roe": {
                    "label": "Return on Equity",
                    "value": round(roe * 100, 2) if roe else None,
                    "status": get_health_status("roe", roe)
                },

                "debt_to_equity": {
                    "label": "Debt to Equity",
                    "value": de,
                    "status": get_health_status("debt_to_equity", de)
                },

                "revenue_growth": {
                    "label": "Revenue Growth",
                    "value": round(rev_growth * 100, 2) if rev_growth else None,
                    "status": get_health_status("revenue_growth", rev_growth)
                },

                "current_ratio": {
                    "label": "Current Ratio",
                    "value": curr_ratio,
                    "status": get_health_status("current_ratio", curr_ratio)
                }
            }
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


# ---------------------------
# Debt level and safty meter API
# ---------------------------


def calculate_debt_score(de, icr, da):

    score = 100

    if de is not None:
        if de > 1.5:
            score -= 40
        elif de > 1.0:
            score -= 20
        elif de > 0.5:
            score -= 10

    if icr is not None:
        if icr < 1.5:
            score -= 40
        elif icr < 3:
            score -= 20

    if da is not None:
        if da > 0.6:
            score -= 20
        elif da > 0.4:
            score -= 10

    return max(0, score)

def debt_insight(score):

    if score >= 80:
        return "The company has very safe debt levels and strong financial stability."

    if score >= 60:
        return "Debt levels are manageable but investors should monitor borrowing."

    if score >= 40:
        return "Debt appears moderately high. Investors should review cash flow."

    return "Debt risk is high. Beginners should carefully analyze financial stability."


def safe_get(df, key):
    if key in df.index:
        return df.loc[key].iloc[0]
    return None


# ----------------------------------
#  Debt level and safty meter
# ----------------------------------


@app.route("/debt/<symbol>")  
def debt_analysis(symbol):

    try:

        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info

        income_stmt = ticker.financials 
        balance_sheet = ticker.balance_sheet

        total_debt = safe_get(balance_sheet, "Total Debt")
        equity = safe_get(balance_sheet, "Stockholders Equity")
        assets = safe_get(balance_sheet, "Total Assets")
        ebitda = info.get("ebitda")

        interest_expense = None
        if 'Interest Expense' in income_stmt.index:
            # We use .abs() because interest is usually a negative number in reports
            interest_expense = abs(income_stmt.loc['Interest Expense'].iloc[0])

        de_ratio = (total_debt / equity) if total_debt and equity else None
        
        # Interest Coverage: Using EBITDA as a proxy for EBIT for beginners
        interest_coverage = (ebitda / interest_expense) if ebitda and interest_expense and interest_expense != 0 else None
        
        debt_assets = (total_debt / assets) if total_debt and assets else None

        # 4. Score & Insight (Pass the calculated ratios)
        score = calculate_debt_score(de_ratio, interest_coverage, debt_assets)
        insight = debt_insight(score) 
        return jsonify({
    "symbol": symbol.upper(),

    "metrics": {
        "debt_to_equity": round(de_ratio,2) if de_ratio else None,
        "interest_coverage": round(interest_coverage,2) if interest_coverage else None,
        "debt_to_assets": round(debt_assets,2) if debt_assets else None
    },

    "score": score,

    "rating": (
        "Safe" if score >= 80 else
        "Moderate" if score >= 60 else
        "Risky"
    ),

    "ai_insight": insight
    })

    except Exception as e:
        return jsonify({"error": f"Could not fetch data: {str(e)}"}), 500




# --------------------------------
# Industry growth Gauge API
# --------------------------------


def safe_value(value, default=0):
    """
    Ensures API never crashes if value is None
    """
    try:
        if value is None:
            return default
        return value
    except:
        return default


def calculate_growth_score(revenue_growth, earnings_growth):

    score = 50

    # Revenue Growth Contribution
    if revenue_growth > 15:
        score += 25
    elif revenue_growth > 8:
        score += 15
    elif revenue_growth > 3:
        score += 5

    # Earnings Growth Contribution
    if earnings_growth > 15:
        score += 25
    elif earnings_growth > 8:
        score += 15
    elif earnings_growth > 3:
        score += 5

    return min(score, 100)


def growth_insight(score):

    if score >= 80:
        return "This industry is growing rapidly. Companies in this sector may benefit from strong demand."

    elif score >= 60:
        return "The industry shows moderate growth. Stable expansion is expected."

    elif score >= 40:
        return "Industry growth appears stable but not very fast."

    else:
        return "This industry is growing slowly. Investors should review long-term prospects carefully."

# -----------------
# Industry Growth 
# -----------------


@app.route("/industry-growth/<symbol>")
def industry_growth(symbol):

    try:

        if not symbol:
            return jsonify({
                "error": "Symbol is required"
            }), 400

        ticker = yf.Ticker(symbol + ".NS")

        try:
            info = ticker.get_info()
        except:
            info = ticker.info

        if not info:
            return jsonify({
                "error": "No financial data available"
            }), 404

        revenue_growth = safe_value(info.get("revenueGrowth"))
        earnings_growth = safe_value(info.get("earningsQuarterlyGrowth"))

        # Convert decimal to percentage
        revenue_growth = revenue_growth * 100
        earnings_growth = earnings_growth * 100

        score = calculate_growth_score(revenue_growth, earnings_growth)

        insight = growth_insight(score)

        return jsonify({
            "symbol": symbol.upper(),

            "metrics": {
                "revenue_growth": round(revenue_growth, 2),
                "earnings_growth": round(earnings_growth, 2)
            },

            "growth_score": score,

            "rating": (
                "Fast Growing" if score >= 80 else
                "Moderate Growth" if score >= 60 else
                "Stable Growth" if score >= 40 else
                "Slow Growth"
            ),

            "ai_insight": insight
        })


    except Exception as e:

        return jsonify({
            "error": "Industry growth analysis failed",
            "details": str(e)
        }), 500


# -----------------------------
# Valution Fairness Checker API
# -----------------------------
def calculate_valuation_score(pe, peg, pb, ev_ebitda, div_yield):

    score = 0

    # P/E ratio
    if pe:
        if pe < 15:
            score += 25
        elif pe < 25:
            score += 18
        elif pe < 35:
            score += 10

    # PEG ratio
    if peg:
        if peg < 1:
            score += 25
        elif peg < 1.5:
            score += 18
        elif peg < 2:
            score += 10

    # P/B ratio
    if pb:
        if pb < 1:
            score += 20
        elif pb < 3:
            score += 14
        elif pb < 5:
            score += 8

    # EV / EBITDA
    if ev_ebitda:
        if ev_ebitda < 10:
            score += 20
        elif ev_ebitda < 20:
            score += 14
        elif ev_ebitda < 30:
            score += 8

    # Dividend Yield
    if div_yield:
        if div_yield > 4:
            score += 10
        elif div_yield > 2:
            score += 7
        elif div_yield > 1:
            score += 4

    return score


def valuation_insight(score):

    if score >= 80:
        return "The stock appears undervalued relative to its earnings and assets."

    if score >= 60:
        return "The stock seems fairly valued compared with its financial performance."

    if score >= 40:
        return "The stock may be slightly expensive. Investors should check growth expectations."

    return "The stock appears overvalued compared with its fundamentals."


# ---------------------------------
# Valution Fairness Checker 
# ---------------------------------

@app.route("/valuation/<symbol>")
def valuation(symbol):

    try:

        ticker = yf.Ticker(symbol + ".NS")

        info = ticker.info

        pe = info.get("trailingPE")
        peg = info.get("trailingPegRatio")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        div_yield = info.get("dividendYield")

        # ✅ Rounding
        pe = round(pe, 2) if pe is not None else None
        pb = round(pb, 2) if pb is not None else None

        if div_yield:
            div_yield = round(div_yield * 100, 2)

        score = calculate_valuation_score(pe, peg, pb, ev_ebitda, div_yield)

        insight = valuation_insight(score)

        return jsonify({

            "symbol": symbol.upper(),

            "metrics": {
                "pe_ratio": pe,
                "peg_ratio": peg,
                "pb_ratio": pb,
                "ev_ebitda": ev_ebitda,
                "dividend_yield": div_yield
            },

            "valuation_score": score,

            "rating":
                "Undervalued" if score >= 80 else
                "Fair Value" if score >= 60 else
                "Slightly Expensive" if score >= 40 else
                "Overvalued",

            "ai_insight": insight

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# -----------------------------
# Beginner Risk Assessment API
# -----------------------------

def get_debt_metric(info):

    de = info.get("debtToEquity")

    if de is None:
        return "N/A", 10

    if de < 50:
        return "Safe", 25

    elif de < 120:
        return "Moderate", 15

    else:
        return "Risky", 5


def get_revenue_stability(info):

    growth = info.get("revenueGrowth")

    if growth is None:
        return "N/A", 10

    if growth > 0.15:
        return "Stable", 25

    elif growth > 0.05:
        return "Moderate", 15

    else:
        return "Weak", 5


def get_volatility(info):

    beta = info.get("beta")

    if beta is None:
        return "N/A", 10

    if beta < 0.9:
        return "Low", 25

    elif beta < 1.3:
        return "Moderate", 15

    else:
        return "High", 5


def get_sector_risk(sector):

    safe_sectors = [
        "Consumer Defensive",
        "Utilities",
        "Healthcare"
    ]

    moderate_sectors = [
        "Technology",
        "Financial Services"
    ]

    risky_sectors = [
        "Real Estate",
        "Energy",
        "Metals & Mining"
    ]

    if sector in safe_sectors:
        return "Low", 25

    elif sector in moderate_sectors:
        return "Moderate", 15

    elif sector in risky_sectors:
        return "High", 5

    return "N/A", 10


def risk_level(score):

    if score >= 80:
        return "Low Risk"

    elif score >= 50:
        return "Medium Risk"

    else:
        return "High Risk"


def risk_insight(score):

    if score >= 80:
        return "The company appears financially stable with manageable debt and steady performance. This stock may be suitable for beginner investors seeking lower risk."

    elif score >= 50:
        return "The company shows moderate risk. Some factors like volatility or sector conditions may cause price fluctuations."

    else:
        return "This stock carries higher risk due to unstable metrics or market volatility. Beginners should analyze carefully before investing."
    


# --------------------------
# Beginner Risk Indicator
# --------------------------

@app.route("/risk/<symbol>")
def beginner_risk(symbol):

    try:
        
        # de = info.get("debtToEquity") 
        # growth = info.get("revenueGrowth")
        # beta = info.get("beta")    should be get and calculated    beta for volatility

        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info

        sector = info.get("sector")

        debt_label, debt_score = get_debt_metric(info)
        revenue_label, revenue_score = get_revenue_stability(info)
        vol_label, vol_score = get_volatility(info)
        sector_label, sector_score = get_sector_risk(sector)

        risk_score = debt_score + revenue_score + vol_score + sector_score

        return jsonify({

            "risk_score": risk_score,
            "risk_level": risk_level(risk_score),
            "ai_insight": risk_insight(risk_score),
            "metrics": {
                "debt": debt_label,
                "revenue": revenue_label,
                "volatility": vol_label,
                "sector": sector_label
            }

        })

    except Exception as e:

        return jsonify({"error": str(e)})



# --------------------------
# Investor suitability matcher API
# --------------------------

def risk_score(stock):
    beta = stock.info.get("beta", 1)
    debt = stock.info.get("debtToEquity", 0)

    score = 0

    if beta < 0.9:
        score += 15
    elif beta < 1.2:
        score += 10
    else:
        score += 5

    if debt < 50:
        score += 15
    elif debt < 100:
        score += 10
    else:
        score += 5

    return score


def growth_score(stock):
    growth = stock.info.get("revenueGrowth", 0)

    if growth > 0.15:
        return 25
    elif growth > 0.08:
        return 18
    else:
        return 10


def income_score(stock):
    dividend = stock.info.get("dividendYield", 0)

    if dividend > 0.04:
        return 20
    elif dividend > 0.02:
        return 12
    else:
        return 5


def value_score(stock):
    pe = stock.info.get("trailingPE", 0)

    if pe == 0:
        return 5

    if pe < 20:
        return 25
    elif pe < 35:
        return 18
    else:
        return 8


def verdict(score):

    if score >= 80:
        return "Strong Buy"
    elif score >= 65:
        return "Buy"
    elif score >= 50:
        return "Hold"
    elif score >= 35:
        return "Risky"
    else:
        return "Avoid"


def explanation(score, verdict_text):

    if verdict_text == "Strong Buy":
        return "This company demonstrates strong financial stability, growth potential, and reasonable valuation, making it highly suitable for long-term investors."

    if verdict_text == "Buy":
        return "The company shows solid fundamentals and moderate growth potential. It may suit investors seeking balanced opportunities."

    if verdict_text == "Hold":
        return "The company appears fairly valued with moderate fundamentals. Investors may consider holding rather than aggressively buying."

    if verdict_text == "Risky":
        return "The stock carries higher volatility or financial risk and may be suitable only for aggressive investors."

    return "The company fundamentals suggest weak investment suitability at the moment."


# -------------------------------
# Investor Suitability Matcher 
# -------------------------------

@app.get("/investor-suitability/<symbol>")
def investor_suitability(symbol):
    
    # beta = stock.info.get("beta", 1)
    # debt = stock.info.get("debtToEquity", 0)
    # growth = stock.info.get("revenueGrowth", 0)
    # dividend = stock.info.get("dividendYield", 0)
    # pe = stock.info.get("trailingPE", 0)  These are calculated

    stock = yf.Ticker(symbol+".NS")

    risk = risk_score(stock)
    growth = growth_score(stock)
    income = income_score(stock)
    value = value_score(stock)

    total_score = risk + growth + income + value

    verdict_text = verdict(total_score)

    ai_text = explanation(total_score, verdict_text)

    return {
        "ticker": symbol,
        "suitabilityScore": total_score,
        "verdict": verdict_text,
        "riskScore": risk,
        "growthScore": growth,
        "incomeScore": income,
        "valueScore": value,
        "aiExplanation": ai_text
    }

# --------------------------------
# Market data (Live) API
# --------------------------------


tickers = {

    "NIFTY": "^NSEI",

    "SENSEX": "^BSESN",

    "BANKNIFTY": "^NSEBANK"

}


@app.route('/market-data', methods=['GET'])
def get_market_data():
    results = []
    try:
        for name, symbol in tickers.items():
            ticker = yf.Ticker(symbol)
            data = ticker.fast_info
            
            # Fetch history to get the previous close
            hist = ticker.history(period="2d")
            if len(hist) < 2:
                # Fallback if history is missing (e.g., market just opened)
                prev_close = data['previous_close']
            else:
                prev_close = hist['Close'].iloc[-2]

            current_price = data['last_price']
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100

            results.append({
                "title": name,
                "price": f"{current_price:,.2f}",
                "change": f"{'+' if change > 0 else ''}{change:.2f} ({percent_change:.2f}%)",
                "isBullish": bool(change > 0) # Ensure it's a JSON-serializable boolean
            })
            
        print(f"DEBUG: {results}") # Useful for your console
        return jsonify(results)    # THIS IS THE CRITICAL LINE
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# -----------------------------------------
#  Market News API
# -----------------------------------------

@app.route('/market-news', methods=['GET'])
def get_market_news():
    try:
        tickers = [
            "SPY",        
            "^NSEI",     
            "^BSESN",  
        ]

        raw_news = []

        for symbol in tickers:
            ticker = yf.Ticker(symbol)
            raw_news.extend(ticker.news)

        flattened_news = []
        for item in raw_news[:5]:

            content = item.get('content', {})
            thumbnail_url = ""
            thumb_data = content.get('thumbnail')
            if thumb_data and 'resolutions' in thumb_data:
                thumbnail_url = thumb_data['resolutions'][0]['url']

            flattened_news.append({
                "title": content.get('title', 'No Title'),
                "summary": content.get(
                    'summary',
                    'No Summary Available'
                ),
                "publisher": content.get(
                    'provider',
                    {}
                ).get(
                    'displayName',
                    'Market Source'
                ),
                "pubDate": content.get('pubDate', ''),
                "url": content.get(
                    'canonicalUrl',
                    {}
                ).get(
                    'url',
                    ''
                ),
                "image": thumbnail_url
            })
            print(flattened_news)
        return jsonify(flattened_news)
    except Exception as e:
        print(f"News Fetch Error: {e}")

        return jsonify({
            "error": "Failed to fetch news"
        }), 500

@app.route("/option-chain")
def option_chain():

    try:

        instrument_key = request.args.get(
                "instrument_key"
            )

        expiry =request.args.get(
                "expiry"
            )

        url = "https://api.upstox.com/v2/option/chain"

        params = {

            "instrument_key":
                instrument_key,

            "expiry_date":
                expiry
        }

        headers = {

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",

            "Authorization":
                f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(

            url,

            params=params,

            headers=headers
        )

        data = response.json()

        return jsonify(data)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500
        
        

@app.route("/expiry-list")
def expiry_list():

    try:

        instrument_key = request.args.get(
                "instrument_key"
            )

        url ="https://api.upstox.com/v2/option/contract"

        params = {

            "instrument_key":
                instrument_key
        }

        headers = {

            "Accept":
                "application/json",

            "Authorization":
                f"Bearer {ACCESS_TOKEN}"
        }

        response = requests.get(

            url,

            params=params,

            headers=headers
        )

        data = response.json()

        contracts = data["data"]

        expiries = sorted(
            list(
                set(
                    item["expiry"]
                    for item in contracts
                )
            )
        )

        return jsonify({

            "current_expiry":
                expiries[0],

            "expiries":
                expiries
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    # app.run(app, debug=True)