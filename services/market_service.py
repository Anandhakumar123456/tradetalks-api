from services.cache_service import cache
from config import CACHE_MARKET
from services.upstox_service import market_api

MARKET_SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX": "BSE_INDEX|SENSEX",
}


def get_market_data():
    cached = cache.get("market-data")

    if cached:
        return cached
    symbols = ",".join(MARKET_SYMBOLS.values())

    response = market_api.get_full_market_quote(
        symbol=symbols,
        api_version="2.0"
    )

    data = response.to_dict()["data"]

    results = []

    for title, instrument in MARKET_SYMBOLS.items():

        quote = data[instrument.replace("|", ":")]

        last_price = float(quote["last_price"])
        net_change = float(quote["net_change"])

        previous_close = last_price - net_change

        percent_change = (
            (net_change / previous_close) * 100
            if previous_close != 0
            else 0
        )

        ohlc = quote["ohlc"]

        results.append({
    "title": title,

    # Flutter expects String
    "price": f"{last_price:,.2f}",

    # Flutter expects "+102.35 (0.42%)"
    "change": f"{'+' if net_change >= 0 else ''}{net_change:.2f} ({percent_change:.2f}%)",

    # Keep this for future use
    "percent_change": round(percent_change, 2),

    "open": round(float(ohlc["open"]), 2),
    "high": round(float(ohlc["high"]), 2),
    "low": round(float(ohlc["low"]), 2),
    "previous_close": round(previous_close, 2),

    "isBullish": bool(net_change >= 0),
})
    cache.set(
    "market-data",
    results,
    CACHE_MARKET
)
    return results