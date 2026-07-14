from services.cache_service import cache
from services.yahoo_service import get_ticker
from config import CACHE_YAHOO
from utils.logger import logger


def get_fundamentals(symbol):

    cache_key = f"fundamentals_{symbol}"

    cached = cache.get(cache_key)

    if cached:
        logger.debug(f"[High-level Cache Hit] Fundamentals fetching for {symbol}")
        return cached

    logger.info(f"[High-level Cache Miss / Calculating] Fetching Fundamentals for {symbol}")

    ticker = get_ticker(symbol)

    info = ticker.info

    cache.set(
        cache_key,
        info,
        ttl=CACHE_YAHOO
    )

    return info