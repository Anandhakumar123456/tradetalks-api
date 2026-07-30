import json
import random
from pathlib import Path

from scheduler.scheduler import scheduler
from services.firebase_service import send_topic_notification
from services.market_status_service import is_trading_day
from utils.logger import logger

TOPIC = "all_users"

# ============================================================
# Last Notification Storage
# ============================================================

LAST_NOTIFICATION_FILE = Path("data/last_notifications.json")


def load_last_notifications():
    LAST_NOTIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    if LAST_NOTIFICATION_FILE.exists():
        try:
            with open(LAST_NOTIFICATION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    return {}


def save_last_notifications(data):
    LAST_NOTIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(LAST_NOTIFICATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


_last_notifications = load_last_notifications()


# ============================================================
# Notification Templates
# ============================================================

MARKET_OPEN_REMINDER_NOTIFICATIONS = [
    {
        "title": "⏰ Market Opens in 5 Minutes",
        "body": "Prepare your watchlist and trading plan.",
    },
    {
        "title": "📈 Opening Bell Soon",
        "body": "Only 5 minutes left before trading begins.",
    },
    {
        "title": "🚀 Get Ready",
        "body": "Markets are opening in just 5 minutes.",
    },
    {
        "title": "💹 Trading Starts Soon",
        "body": "Review your strategy before the opening bell.",
    },
    {
        "title": "🎯 Ready for Today?",
        "body": "The market opens in 5 minutes.",
    },
    {
        "title": "📊 Morning Alert",
        "body": "Check today's watchlist before the market opens.",
    },
    {
        "title": "🔥 Opening Countdown",
        "body": "Trading begins in just 5 minutes.",
    },
    {
        "title": "💼 Prepare to Trade",
        "body": "Review your plan before the opening bell.",
    },
    {
        "title": "📣 Market Alert",
        "body": "Get ready! Markets open in 5 minutes.",
    },
    {
        "title": "⌛ Final Preparation",
        "body": "Just 5 minutes left before trading starts.",
    },
]

MARKET_OPEN_NOTIFICATIONS = [
    {
        "title": "🟢 Market Open",
        "body": "NSE & BSE are now live. Happy Trading!",
    },
    {
        "title": "🚀 Trading Begins",
        "body": "The market is now open. Trade wisely.",
    },
    {
        "title": "📈 Markets Are Live",
        "body": "Keep an eye on today's opportunities.",
    },
    {
        "title": "💹 Opening Bell Rang",
        "body": "The trading session has officially started.",
    },
    {
        "title": "🔥 Let's Trade",
        "body": "Markets are active. Stay disciplined.",
    },
    {
        "title": "🎯 Time to Invest",
        "body": "Your next opportunity could be today.",
    },
    {
        "title": "📊 Live Market",
        "body": "Track your favorite stocks now.",
    },
    {
        "title": "💼 Trading Session Started",
        "body": "Stay focused and trade smart.",
    },
    {
        "title": "⚡ Market in Action",
        "body": "The opening bell has rung.",
    },
    {
        "title": "🌅 Good Morning Trader",
        "body": "Markets are officially open.",
    },
]

MARKET_CLOSE_REMINDER_NOTIFICATIONS = [
    {
        "title": "⏰ Market Closes in 10 Minutes",
        "body": "Review your open positions.",
    },
    {
        "title": "📉 Closing Bell Soon",
        "body": "Only 10 minutes left today.",
    },
    {
        "title": "⚠️ Wrap Up",
        "body": "Check your positions before market close.",
    },
    {
        "title": "📝 Final Review",
        "body": "Take one last look at today's trades.",
    },
    {
        "title": "⌛ Last 10 Minutes",
        "body": "Prepare for market close.",
    },
    {
        "title": "📊 End of Session",
        "body": "Monitor your portfolio before closing.",
    },
    {
        "title": "💼 Final Trading Minutes",
        "body": "Finish today's trades wisely.",
    },
    {
        "title": "📣 Market Closing Alert",
        "body": "The session ends in 10 minutes.",
    },
    {
        "title": "🔔 Closing Countdown",
        "body": "Only 10 minutes remain.",
    },
    {
        "title": "📈 Review Before Close",
        "body": "Don't forget to check your positions.",
    },
]

MARKET_CLOSED_NOTIFICATIONS = [
    {
        "title": "🔴 Market Closed",
        "body": "Today's trading session has ended.",
    },
    {
        "title": "📊 Trading Day Complete",
        "body": "Review your trades and prepare for tomorrow.",
    },
    {
        "title": "📉 Markets Have Closed",
        "body": "See how your portfolio performed today.",
    },
    {
        "title": "💼 Session Ended",
        "body": "Time to analyze today's market.",
    },
    {
        "title": "🌙 Trading Finished",
        "body": "Rest well and prepare for tomorrow.",
    },
    {
        "title": "📈 Market Wrap-Up",
        "body": "Review today's winners and losers.",
    },
    {
        "title": "🎯 End of Trading",
        "body": "Analyze today's decisions.",
    },
    {
        "title": "📚 Learn From Today",
        "body": "Every trading day is a learning opportunity.",
    },
    {
        "title": "💹 Closing Bell",
        "body": "Markets are closed for today.",
    },
    {
        "title": "🏁 Trading Complete",
        "body": "Great job! Prepare for the next session.",
    },
]


# ============================================================
# Helper Functions
# ============================================================

def should_send_notification():
    if not is_trading_day():
        logger.info("Today is not a trading day. Notification skipped.")
        return False

    return True


def get_random_notification(notification_list, key):
    total = len(notification_list)

    if total == 1:
        return notification_list[0]

    last_index = _last_notifications.get(key)

    available_indexes = list(range(total))

    if last_index in available_indexes:
        available_indexes.remove(last_index)

    selected_index = random.choice(available_indexes)

    _last_notifications[key] = selected_index
    save_last_notifications(_last_notifications)

    return notification_list[selected_index]


def send_market_notification(notification_list, screen, key):
    if not should_send_notification():
        return

    notification = get_random_notification(notification_list, key)

    try:
        send_topic_notification(
            TOPIC,
            notification["title"],
            notification["body"],
            data={
                "screen": screen,
            },
        )

        logger.info(
            f"Notification sent: {notification['title']}"
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


# ============================================================
# Scheduler Jobs
# ============================================================

def market_open_reminder():
    send_market_notification(
        MARKET_OPEN_REMINDER_NOTIFICATIONS,
        "home",
        "market_open_reminder",
    )


def market_open():
    send_market_notification(
        MARKET_OPEN_NOTIFICATIONS,
        "home",
        "market_open",
    )


def market_close_reminder():
    send_market_notification(
        MARKET_CLOSE_REMINDER_NOTIFICATIONS,
        "paper_trading",
        "market_close_reminder",
    )


def market_closed():
    send_market_notification(
        MARKET_CLOSED_NOTIFICATIONS,
        "paper_trading",
        "market_closed",
    )


# ============================================================
# Scheduler Registration
# ============================================================

def start_market_scheduler():
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

    logger.info("✅ Market scheduler jobs registered successfully.")
