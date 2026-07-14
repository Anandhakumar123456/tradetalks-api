import requests
from services.upstox_service import ACCESS_TOKEN
from services.cache_service import cache
from config import CACHE_OPTION


def get_option_chain(instrument_key, expiry):
    cache_key = f"option_chain_{instrument_key}_{expiry}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = "https://api.upstox.com/v2/option/chain"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    params = {
        "instrument_key": instrument_key,
        "expiry_date": expiry
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    result = response.json()
    cache.set(cache_key, result, ttl=CACHE_OPTION)
    return result