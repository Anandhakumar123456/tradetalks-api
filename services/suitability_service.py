from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO
from utils.logger import logger


def risk_score(info):
    beta = info.get("beta", 1)
    debt = info.get("debtToEquity", 0)

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


def growth_score(info):
    growth = info.get("revenueGrowth", 0)

    if growth > 0.15:
        return 25
    elif growth > 0.08:
        return 18
    else:
        return 10


def income_score(info):
    dividend = info.get("dividendYield", 0)

    if dividend > 0.04:
        return 20
    elif dividend > 0.02:
        return 12
    else:
        return 5


def value_score(info):
    pe = info.get("trailingPE", 0)

    if pe == 0 or pe is None:
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
        return (
            "This company demonstrates strong financial stability, "
            "growth potential, and reasonable valuation, making it "
            "highly suitable for long-term investors."
        )

    if verdict_text == "Buy":
        return (
            "The company shows solid fundamentals and moderate "
            "growth potential. It may suit investors seeking "
            "balanced opportunities."
        )

    if verdict_text == "Hold":
        return (
            "The company appears fairly valued with moderate "
            "fundamentals. Investors may consider holding rather "
            "than aggressively buying."
        )

    if verdict_text == "Risky":
        return (
            "The stock carries higher volatility or financial risk "
            "and may be suitable only for aggressive investors."
        )

    return (
        "The company fundamentals suggest weak investment "
        "suitability at the moment."
    )


def get_suitability(symbol):

    symbol = symbol.upper()

    cache_key = f"suitability_{symbol}"

    cached = cache.get(cache_key)

    if cached:
        logger.debug(f"[High-level Cache Hit] Suitability analysis for {symbol}")
        return cached

    logger.info(
        f"[High-level Cache Miss / Calculating] Computing Suitability analysis for {symbol}"
    )

    ticker = get_ticker(symbol)

    info = ticker.info

    risk = risk_score(info)
    growth = growth_score(info)
    income = income_score(info)
    value = value_score(info)

    total_score = risk + growth + income + value

    result = {
        "symbol": symbol,
        "score": total_score,
        "level": verdict(total_score),
        "ai_insight": explanation(total_score, verdict(total_score)),
        "riskScore": risk,
        "growthScore": growth,
        "incomeScore": income,
        "valueScore": value,
    }

    cache.set(cache_key, result, ttl=CACHE_YAHOO)

    return result