import yfinance as yf
from services.cache_service import cache
from config import CACHE_YAHOO
from utils.logger import logger

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
            logger.debug(f"[Low-level Cache Hit] Yahoo Finance info for {self.symbol}")
            return cached
        logger.info(f"[Low-level Cache Miss / API Fetch] Fetching Yahoo Finance info for {self.symbol}")
        data = self.ticker.info
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    def get_info(self):
        cache_key = f"yf_info_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"[Low-level Cache Hit] Yahoo Finance get_info for {self.symbol}")
            return cached
        logger.info(f"[Low-level Cache Miss / API Fetch] Fetching Yahoo Finance get_info for {self.symbol}")
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
            logger.debug(f"[Low-level Cache Hit] Yahoo Finance financials for {self.symbol}")
            return cached
        logger.info(f"[Low-level Cache Miss / API Fetch] Fetching Yahoo Finance financials for {self.symbol}")
        data = self.ticker.financials
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    @property
    def balance_sheet(self):
        cache_key = f"yf_balance_sheet_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"[Low-level Cache Hit] Yahoo Finance balance_sheet for {self.symbol}")
            return cached
        logger.info(f"[Low-level Cache Miss / API Fetch] Fetching Yahoo Finance balance_sheet for {self.symbol}")
        data = self.ticker.balance_sheet
        cache.set(cache_key, data, CACHE_YAHOO)
        return data

    @property
    def dividends(self):
        cache_key = f"yf_dividends_{self.symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"[Low-level Cache Hit] Yahoo Finance dividends for {self.symbol}")
            return cached
        logger.info(f"[Low-level Cache Miss / API Fetch] Fetching Yahoo Finance dividends for {self.symbol}")
        data = self.ticker.dividends
        cache.set(cache_key, data, CACHE_YAHOO)
        return data


def get_ticker(symbol):
    symbol = symbol.upper()

    if symbol not in _cache:
        _cache[symbol] = CachedTicker(symbol)

    return _cache[symbol]