from services.upstox_service import market_api
from pprint import pprint

symbols = (
    "NSE_INDEX|Nifty 50,"
    "NSE_INDEX|Nifty Bank,"
    "BSE_INDEX|SENSEX"
)

response = market_api.get_full_market_quote(
    symbol=symbols,
    api_version="2.0"
)

pprint(response.to_dict())