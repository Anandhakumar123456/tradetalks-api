# scheduler/__init__.py

import atexit

from .scheduler import scheduler
from .market_scheduler import start_market_scheduler
from .learning_scheduler import start_learning_scheduler


def start_scheduler():
    """
    Register all scheduler jobs and start the scheduler.
    This function should be called only once during application startup.
    """

    # Register Market Notification Jobs
    start_market_scheduler()

    # Register Learning Reminder Jobs
    start_learning_scheduler()

    # Start scheduler only once
    if not scheduler.running:
        scheduler.start()

    # Shutdown scheduler gracefully when application exits
    atexit.register(lambda: scheduler.shutdown(wait=False))