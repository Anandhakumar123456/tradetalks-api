from services.cache_service import cache
from services.yahoo_service import get_ticker
from config import CACHE_YAHOO


def get_fundamentals(symbol):

    cache_key = f"fundamentals_{symbol}"

    cached = cache.get(cache_key)

    if cached:
        return cached

    ticker = get_ticker(symbol)

    info = ticker.info

    cache.set(
        cache_key,
        info,
        ttl=CACHE_YAHOO
    )

    return info