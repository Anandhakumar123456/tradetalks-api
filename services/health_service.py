from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO


# -----------------------------
# Health Status
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


# -----------------------------
# Health Score
# -----------------------------
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
# Main Service
# -----------------------------
def get_health(symbol):
    symbol = symbol.upper()
    cache_key = f"health_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker = get_ticker(symbol)

    info = ticker.info

    roe = info.get("returnOnEquity") or 0

    de = info.get("debtToEquity") or 0

    rev_growth = info.get("revenueGrowth") or 0

    curr_ratio = info.get("currentRatio") or 0

    score = calculate_health_score(
        roe,
        de,
        rev_growth,
        curr_ratio,
    )

    result = {

        "symbol": symbol.upper(),

        "health_score": score,

        "metrics": {

            "roe": {
                "label": "Return on Equity",
                "value": round(roe * 100, 2) if roe else None,
                "status": get_health_status(
                    "roe",
                    roe
                )
            },

            "debt_to_equity": {
                "label": "Debt to Equity",
                "value": de,
                "status": get_health_status(
                    "debt_to_equity",
                    de
                )
            },

            "revenue_growth": {
                "label": "Revenue Growth",
                "value": round(
                    rev_growth * 100,
                    2
                ) if rev_growth else None,
                "status": get_health_status(
                    "revenue_growth",
                    rev_growth
                )
            },

            "current_ratio": {
                "label": "Current Ratio",
                "value": curr_ratio,
                "status": get_health_status(
                    "current_ratio",
                    curr_ratio
                )
            }
        }
    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result