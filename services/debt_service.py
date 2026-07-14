from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO
from utils.logger import logger

def safe_get(df, key):
    if key in df.index:
        return df.loc[key].iloc[0]
    return None


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


def get_debt(symbol):
    symbol = symbol.upper()
    cache_key = f"debt_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"[High-level Cache Hit] Debt analysis for {symbol}")
        return cached

    logger.info(f"[High-level Cache Miss / Calculating] Computing Debt analysis for {symbol}")

    ticker = get_ticker(symbol)

    info = ticker.info

    income_stmt = ticker.financials

    balance_sheet = ticker.balance_sheet

    total_debt = safe_get(balance_sheet, "Total Debt")

    equity = safe_get(balance_sheet, "Stockholders Equity")

    assets = safe_get(balance_sheet, "Total Assets")

    ebitda = info.get("ebitda")

    interest_expense = None

    if "Interest Expense" in income_stmt.index:
        interest_expense = abs(
            income_stmt.loc["Interest Expense"].iloc[0]
        )

    de_ratio = (
        total_debt / equity
        if total_debt and equity
        else None
    )

    interest_coverage = (
        ebitda / interest_expense
        if ebitda and interest_expense and interest_expense != 0
        else None
    )

    debt_assets = (
        total_debt / assets
        if total_debt and assets
        else None
    )

    score = calculate_debt_score(
        de_ratio,
        interest_coverage,
        debt_assets
    )

    result = {

        "symbol": symbol.upper(),

        "metrics": {

            "debt_to_equity":
                round(de_ratio, 2)
                if de_ratio else None,

            "interest_coverage":
                round(interest_coverage, 2)
                if interest_coverage else None,

            "debt_to_assets":
                round(debt_assets, 2)
                if debt_assets else None
        },

        "score": score,

        "rating":
            "Safe"
            if score >= 80
            else "Moderate"
            if score >= 60
            else "Risky",

        "ai_insight":
            debt_insight(score)

    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result