from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO


def get_suitability(symbol):
    symbol = symbol.upper()
    cache_key = f"suitability_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker = get_ticker(symbol)

    info = ticker.info

    beta = info.get("beta", 1)

    pe = info.get("trailingPE")

    roe = info.get("returnOnEquity")

    debt = info.get("debtToEquity")

    score = 0

    risk_score = 0
    growth_score = 0
    income_score = 0

    # -------------------------
    # Risk
    # -------------------------

    if beta <= 1:
        risk_score = 90
        score += 25
    elif beta <= 1.5:
        risk_score = 70
        score += 15
    else:
        risk_score = 40
        score += 5

    # -------------------------
    # Growth
    # -------------------------

    if roe:
        if roe > 0.15:
            growth_score = 90
            score += 25
        elif roe > 0.08:
            growth_score = 70
            score += 15
        else:
            growth_score = 40
            score += 5

    # -------------------------
    # Income
    # -------------------------

    if pe:
        if pe < 20:
            income_score = 90
            score += 25
        elif pe < 35:
            income_score = 70
            score += 15
        else:
            income_score = 40
            score += 5

    # -------------------------
    # Debt Bonus
    # -------------------------

    if debt:
        if debt < 50:
            score += 25
        elif debt < 120:
            score += 15
        else:
            score += 5

    # -------------------------
    # Verdict
    # -------------------------

    if score >= 80:

        level = "Highly Suitable"

        insight = (
            "This stock appears suitable for beginners due to stable "
            "fundamentals and relatively lower risk."
        )

    elif score >= 60:

        level = "Moderately Suitable"

        insight = (
            "This stock is suitable for investors who can tolerate "
            "moderate market fluctuations."
        )

    else:

        level = "High Risk"

        insight = (
            "This stock may not be ideal for beginners because of higher "
            "volatility or weaker financial metrics."
        )

    result = {

        "symbol": symbol.upper(),

        "score": score,

        "level": level,

        "ai_insight": insight,

        "riskScore": risk_score,

        "growthScore": growth_score,

        "incomeScore": income_score
    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result