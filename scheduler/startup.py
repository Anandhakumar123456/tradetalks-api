"""
Scheduler startup module.

Registers all scheduler jobs and starts the shared APScheduler
instance during application startup.
"""

import atexit

from scheduler.learning_scheduler import start_learning_scheduler
from scheduler.market_scheduler import start_market_scheduler
from scheduler.scheduler import scheduler
from utils.logger import logger


def start_all_schedulers():
    """
    Register all scheduler jobs and start the scheduler.
    """

    try:

        logger.info("Registering scheduler jobs...")

        start_market_scheduler()
        start_learning_scheduler()

        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started successfully.")

        atexit.register(
            lambda: scheduler.shutdown(wait=False)
        )

    except Exception as e:

        logger.exception(
            f"Failed to start scheduler: {e}"
        )

        raise