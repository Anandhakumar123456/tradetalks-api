from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO
from utils.logger import logger


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

    safe = [
        "Consumer Defensive",
        "Utilities",
        "Healthcare"
    ]

    moderate = [
        "Technology",
        "Financial Services"
    ]

    risky = [
        "Real Estate",
        "Energy",
        "Metals & Mining"
    ]

    if sector in safe:
        return "Low", 25

    if sector in moderate:
        return "Moderate", 15

    if sector in risky:
        return "High", 5

    return "N/A", 10


def risk_level(score):

    if score >= 80:
        return "Low Risk"

    if score >= 50:
        return "Medium Risk"

    return "High Risk"


def risk_insight(score):

    if score >= 80:
        return "The company appears financially stable with manageable debt and steady performance. This stock may be suitable for beginner investors seeking lower risk."

    if score >= 50:
        return "The company shows moderate risk. Some factors like volatility or sector conditions may cause price fluctuations."

    return "This stock carries higher risk due to unstable metrics or market volatility. Beginners should analyze carefully before investing."


def get_risk(symbol):
    symbol = symbol.upper()
    cache_key = f"risk_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"[High-level Cache Hit] Risk analysis for {symbol}")
        return cached

    logger.info(f"[High-level Cache Miss / Calculating] Computing Risk analysis for {symbol}")

    ticker = get_ticker(symbol)

    info = ticker.info

    sector = info.get("sector")

    debt_label, debt_score = get_debt_metric(info)
    revenue_label, revenue_score = get_revenue_stability(info)
    vol_label, vol_score = get_volatility(info)
    sector_label, sector_score = get_sector_risk(sector)

    total = (
        debt_score +
        revenue_score +
        vol_score +
        sector_score
    )

    result = {

        "risk_score": total,

        "risk_level": risk_level(total),

        "ai_insight": risk_insight(total),

        "metrics": {

            "debt": debt_label,

            "revenue": revenue_label,

            "volatility": vol_label,

            "sector": sector_label

        }

    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result