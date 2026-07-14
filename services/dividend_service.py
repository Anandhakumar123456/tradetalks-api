from services.yahoo_service import get_ticker
from services.cache_service import cache
from config import CACHE_YAHOO


def get_dividend(symbol):
    symbol = symbol.upper()
    cache_key = f"dividend_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker = get_ticker(symbol)

    dividends = ticker.dividends

    if dividends.empty:
        result = {
            "symbol": symbol.upper(),
            "dividends": []
        }
        cache.set(cache_key, result, ttl=CACHE_YAHOO)
        return result

    df = dividends.reset_index()
    df["year"] = df["Date"].dt.year

    yearly = df.groupby("year")["Dividends"].sum().reset_index()

    result_list = []

    for _, row in yearly.iterrows():

        result_list.append({
            "year": int(row["year"]),
            "dividend": round(float(row["Dividends"]), 2)
        })

    result = {
        "symbol": symbol.upper(),
        "dividends": result_list
    }
    cache.set(cache_key, result, ttl=CACHE_YAHOO)
    return result