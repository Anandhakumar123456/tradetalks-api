import os
import requests
from dotenv import load_dotenv
from services.cache_service import cache
from config import CACHE_NEWS
from utils.logger import logger

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

URL = "https://newsapi.org/v2/everything"


def get_market_news():
    cache_key = "market_news"
    cached = cache.get(cache_key)
    if cached:
        logger.debug("[High-level Cache Hit] Market news")
        return cached

    logger.info("[High-level Cache Miss / API Fetch] Fetching market news from NewsAPI")

    params = {
        "q": "(stock market OR nifty OR sensex OR bank nifty OR dow jones OR nasdaq OR wall street)",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(
        URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    articles = response.json().get("articles", [])

    news = []

    for article in articles:

        news.append({

            "title": article.get("title", ""),

            "summary": article.get("description", ""),

            "publisher": article.get("source", {}).get("name", ""),

            "pubDate": article.get("publishedAt", ""),

            "url": article.get("url", ""),

            "image": article.get("urlToImage", "")

        })

    cache.set(cache_key, news, ttl=CACHE_NEWS)
    return news