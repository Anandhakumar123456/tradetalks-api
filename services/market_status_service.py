from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.cache_service import cache
from services.upstox_service import holiday_api
from utils.logger import logger

IST = ZoneInfo("Asia/Kolkata")

ACTIVE_MARKET_STATUSES = {
    "PRE_OPEN_START",
    "PRE_OPEN_END",
    "NORMAL_OPEN",
    "CLOSING_START",
    "CLOSING_END",
}

HOLIDAY_CACHE_KEY = "market_holidays"
HOLIDAY_CACHE_TTL = 60 * 60 * 24  # 24 hours


def get_market_status():
    """
    Returns current NSE market status string (e.g., 'NORMAL_OPEN', 'CLOSING_END')
    or None if the request fails.
    """
    try:
        response = holiday_api.get_market_status("NSE").to_dict()
        data = response.get("data") if isinstance(response, dict) else None
        market_status = data.get("status") if isinstance(data, dict) else None

        logger.info(f"Market Status: {market_status}")
        return market_status

    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        return None


def is_market_open(status: str | None = None) -> bool:
    """
    Returns True only when the market session is active.
    Optionally accepts an already fetched status string to avoid redundant API calls.
    """
    if status is None:
        status = get_market_status()

    return status in ACTIVE_MARKET_STATUSES


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
        holidays = response.get("data", []) if isinstance(response, dict) else []

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


def _parse_holiday_date(holiday_date):
    """
    Safely converts a holiday date (datetime, date, or ISO string) to a datetime.date object.
    """
    if isinstance(holiday_date, datetime):
        return holiday_date.date()
    if isinstance(holiday_date, date):
        return holiday_date
    if isinstance(holiday_date, str):
        try:
            return datetime.fromisoformat(holiday_date.split("T")[0]).date()
        except Exception:
            return None
    return None


def is_trading_day():
    """
    Returns True if today is a valid NSE trading day (not a weekend and not an exchange holiday).
    """
    try:
        # Use Indian Standard Time
        today = datetime.now(IST).date()

        # -----------------------------------------
        # Saturday / Sunday Check
        # -----------------------------------------
        if today.weekday() >= 5:
            logger.info(f"Weekend: NSE market is closed. Date: {today}")
            return False

        # -----------------------------------------
        # NSE Holiday Check
        # -----------------------------------------
        holidays = get_holidays()

        for holiday in holidays:
            raw_date = holiday.get("_date") or holiday.get("date")
            parsed_date = _parse_holiday_date(raw_date)

            if parsed_date is None or parsed_date != today:
                continue

            closed_exchanges = holiday.get("closed_exchanges") or []
            if "NSE" in closed_exchanges:
                logger.info(f"Trading Holiday: {holiday.get('description')}")
                return False

        # -----------------------------------------
        # Valid Trading Day
        # -----------------------------------------
        logger.info(f"Trading Day: {today}")
        return True

    except Exception as e:
        logger.error(f"Failed to determine trading day: {e}")
        # Fail-safe: Don't send market notifications if trading-day status cannot be determined.
        return False
