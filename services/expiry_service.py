import requests
from services.upstox_service import ACCESS_TOKEN
from services.cache_service import cache
from config import CACHE_EXPIRY


def get_expiry_list(instrument_key):
    cache_key = f"expiry_list_{instrument_key}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = "https://api.upstox.com/v2/option/contract"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    params = {
        "instrument_key": instrument_key
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    contracts = data.get("data", [])

    expiries = sorted(
        list(
            {
                item["expiry"]
                for item in contracts
            }
        )
    )

    result = {
        "current_expiry": expiries[0] if expiries else None,
        "expiries": expiries
    }
    cache.set(cache_key, result, ttl=CACHE_EXPIRY)
    return result