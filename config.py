import os

UPSTOX_BASE_URL = "https://api.upstox.com/v2"

REQUEST_TIMEOUT = 10

CACHE_MARKET = 1          # seconds
CACHE_OPTION = 1
CACHE_EXPIRY = 86400      # 24 hours
CACHE_NEWS = 300          # 5 minutes
CACHE_YAHOO = 36000        # 10 hour (36000 seconds)

DEBUG = True

APP_NAME = "TradeTalks API"
APP_VERSION = "1.0.0"

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")