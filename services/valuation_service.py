from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO
from utils.logger import logger


def calculate_valuation_score(pe, peg, pb, ev_ebitda, div_yield):

    score = 0

    if pe:
        if pe < 15:
            score += 25
        elif pe < 25:
            score += 18
        elif pe < 35:
            score += 10

    if peg:
        if peg < 1:
            score += 25
        elif peg < 1.5:
            score += 18
        elif peg < 2:
            score += 10

    if pb:
        if pb < 1:
            score += 20
        elif pb < 3:
            score += 14
        elif pb < 5:
            score += 8

    if ev_ebitda:
        if ev_ebitda < 10:
            score += 20
        elif ev_ebitda < 20:
            score += 14
        elif ev_ebitda < 30:
            score += 8

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


def get_valuation(symbol):
    symbol = symbol.upper()
    cache_key = f"valuation_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"[High-level Cache Hit] Valuation analysis for {symbol}")
        return cached

    logger.info(f"[High-level Cache Miss / Calculating] Computing Valuation analysis for {symbol}")

    ticker = get_ticker(symbol)

    info = ticker.info

    pe = info.get("trailingPE")
    peg = info.get("trailingPegRatio")
    pb = info.get("priceToBook")
    ev_ebitda = info.get("enterpriseToEbitda")
    div_yield = info.get("dividendYield")

    pe = round(pe, 2) if pe is not None else None
    pb = round(pb, 2) if pb is not None else None

    if div_yield:
        div_yield = round(div_yield * 100, 2)

    score = calculate_valuation_score(
        pe,
        peg,
        pb,
        ev_ebitda,
        div_yield
    )

    result = {

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
            "Undervalued"
            if score >= 80
            else "Fair Value"
            if score >= 60
            else "Slightly Expensive"
            if score >= 40
            else "Overvalued",

        "ai_insight":
            valuation_insight(score)
    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result