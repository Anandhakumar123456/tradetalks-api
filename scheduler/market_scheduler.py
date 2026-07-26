from scheduler.scheduler import scheduler

from services.firebase_service import send_topic_notification
from utils.logger import logger


TOPIC = "tradetalks_all"


def market_open_reminder():
    """Send market opening reminder."""

    try:

        send_topic_notification(
            TOPIC,
            "⏰ Market Opens in 5 Minutes",
            "Prepare your watchlist and trading plan.",
            data={
                "screen": "home",
            },
        )

        logger.info("Market open reminder sent.")

    except Exception as e:

        logger.error(f"Market open reminder failed: {e}")


def market_open():
    """Send market open notification."""

    try:

        send_topic_notification(
            TOPIC,
            "🟢 Market Open",
            "NSE & BSE are now live. Happy Trading!",
            data={
                "screen": "home",
            },
        )

        logger.info("Market open notification sent.")

    except Exception as e:

        logger.error(f"Market open notification failed: {e}")


def market_close_reminder():
    """Send market closing reminder."""

    try:

        send_topic_notification(
            TOPIC,
            "⏰ Market Closes in 10 Minutes",
            "Review your open positions.",
        )

        logger.info("Market close reminder sent.")

    except Exception as e:

        logger.error(f"Market close reminder failed: {e}")


def market_closed():
    """Send market closed notification."""

    try:

        send_topic_notification(
            TOPIC,
            "🔴 Market Closed",
            "Today's trading session has ended.",
        )

        logger.info("Market closed notification sent.")

    except Exception as e:

        logger.error(f"Market closed notification failed: {e}")


def start_market_scheduler():
    """Register all market scheduler jobs."""

    scheduler.add_job(
        market_open_reminder,
        trigger="cron",
        hour=9,
        minute=10,
        id="market_open_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        market_open,
        trigger="cron",
        hour=9,
        minute=15,
        id="market_open",
        replace_existing=True,
    )

    scheduler.add_job(
        market_close_reminder,
        trigger="cron",
        hour=15,
        minute=20,
        id="market_close_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        market_closed,
        trigger="cron",
        hour=15,
        minute=30,
        id="market_closed",
        replace_existing=True,
    )

    logger.info("Market scheduler jobs registered successfully.")