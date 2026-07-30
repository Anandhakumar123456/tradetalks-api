from datetime import date

from services.cache_service import cache
from services.upstox_service import holiday_api
from utils.logger import logger

ACTIVE_MARKET_STATUSES = {
    "PRE_OPEN_START",
    "PRE_OPEN_END",
    "NORMAL_OPEN",
    "CLOSING_START",
}

HOLIDAY_CACHE_KEY = "market_holidays"
HOLIDAY_CACHE_TTL = 60 * 60 * 24  # 24 hours


def get_market_status():
    """
    Returns current NSE market status.
    """

    try:
        response = holiday_api.get_market_status("NSE").to_dict()

        market_status = response["data"]["status"]

        logger.info(f"Market Status: {market_status}")

        return market_status

    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        return None


def is_market_open():
    """
    Returns True only when market session is active.
    """

    market_status = get_market_status()

    return market_status in ACTIVE_MARKET_STATUSES


def get_holidays():
    """
    Returns holiday list from cache or Upstox API.
    """

    holidays = cache.get(HOLIDAY_CACHE_KEY)

    if holidays is not None:
        logger.info("Holiday list loaded from cache.")
        return holidays

    try:
        response = holiday_api.get_holidays().to_dict()

        holidays = response.get("data", [])

        cache.set(
            HOLIDAY_CACHE_KEY,
            holidays,
            HOLIDAY_CACHE_TTL,
        )

        logger.info("Holiday list fetched from Upstox API.")

        return holidays

    except Exception as e:
        logger.error(f"Failed to fetch holidays: {e}")
        return []


def is_trading_day():
    """
    Returns True if today is a valid NSE trading day.
    """

    try:
        today = date.today()

        holidays = get_holidays()

        for holiday in holidays:

            holiday_date = holiday.get("_date")

            if holiday_date is None:
                continue

            if holiday_date.date() != today:
                continue

            if "NSE" in holiday.get("closed_exchanges", []):
                logger.info(
                    f"Trading Holiday: {holiday['description']}"
                )
                return False

        return True

    except Exception as e:
        logger.error(f"Failed to determine trading day: {e}")
        return False