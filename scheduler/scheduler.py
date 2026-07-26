"""
Global APScheduler instance used across the application.

All scheduler modules should import this instance instead of
creating their own scheduler.
"""

from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata"
)