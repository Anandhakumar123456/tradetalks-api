from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO

def safe_value(value, default=0):
    if value is None:
        return default
    return value


def calculate_growth_score(revenue_growth, earnings_growth):

    score = 50

    if revenue_growth > 15:
        score += 25
    elif revenue_growth > 8:
        score += 15
    elif revenue_growth > 3:
        score += 5

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

    return "This industry is growing slowly. Investors should review long-term prospects carefully."


def get_industry_growth(symbol):
    symbol = symbol.upper()
    cache_key = f"industry_growth_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker = get_ticker(symbol)

    try:
        info = ticker.get_info()
    except Exception:
        info = ticker.info

    revenue_growth = safe_value(info.get("revenueGrowth")) * 100
    earnings_growth = safe_value(info.get("earningsQuarterlyGrowth")) * 100

    score = calculate_growth_score(
        revenue_growth,
        earnings_growth
    )

    result = {

        "symbol": symbol.upper(),

        "metrics": {
            "revenue_growth": round(revenue_growth, 2),
            "earnings_growth": round(earnings_growth, 2)
        },

        "growth_score": score,

        "rating":
            "Fast Growing"
            if score >= 80
            else "Moderate Growth"
            if score >= 60
            else "Stable Growth"
            if score >= 40
            else "Slow Growth",

        "ai_insight":
            growth_insight(score)
    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result