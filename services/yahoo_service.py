import yfinance as yf
from services.cache_service import cache
from config import CACHE_YAHOO

_cache = {}


class CachedTicker:

    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.ticker = yf.Ticker(f"{self.symbol}.NS")

    @property
    def info(self):
        cache_key = f"yf_info_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.ticker.info
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    def get_info(self):
        cache_key = f"yf_info_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            data = self.ticker.get_info()
        except AttributeError:
            data = self.ticker.info
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    @property
    def financials(self):
        cache_key = f"yf_financials_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.ticker.financials
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    @property
    def balance_sheet(self):
        cache_key = f"yf_balance_sheet_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.ticker.balance_sheet
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    @property
    def dividends(self):
        cache_key = f"yf_dividends_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        data = self.ticker.dividends
        cache.set(cache_key, data, CACHE_YAHOO)
        return data


def get_ticker(symbol):
    symbol = symbol.upper()

    if symbol not in _cache:
        _cache[symbol] = CachedTicker(symbol)

    return _cache[symbol]