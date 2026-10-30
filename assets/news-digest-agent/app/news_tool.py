"""News fetching tool for the News Digest Agent.

Fetches recent news articles for a given topic from a public news API.
The API key is read from the NEWS_API_KEY environment variable.
"""

import logging
import os
from typing import Any

import requests
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"
NEWS_API_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"


def _fetch_articles(topic: str) -> list[dict[str, Any]]:
    """Fetch news articles for a given topic from NewsAPI.

    Args:
        topic: The news topic to search for.

    Returns:
        List of article dicts with keys: title, url, publishedAt, description, source.
        Returns empty list on any error.
    """
    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        logger.warning("NEWS_API_KEY environment variable not set; returning empty results.")
        return []

    try:
        params: dict[str, Any] = {
            "q": topic,
            "apiKey": api_key,
            "pageSize": 10,
            "sortBy": "publishedAt",
            "language": "en",
        }
        response = requests.get(NEWS_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])
        result = []
        for article in articles:
            result.append({
                "title": article.get("title", "No title"),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
                "description": article.get("description") or article.get("content") or "",
                "source": article.get("source", {}).get("name", "Unknown Source"),
            })
        return result

    except requests.exceptions.RequestException as e:
        logger.error("News API request failed: %s", str(e))
        return []
    except Exception as e:
        logger.error("Unexpected error fetching news: %s", str(e))
        return []


def select_top_articles(articles: list[dict[str, Any]], n: int = 3) -> list[dict[str, Any]]:
    """Select the top N articles by recency (most recent first).

    Args:
        articles: List of article dicts.
        n: Number of top articles to return.

    Returns:
        List of up to n articles sorted by publishedAt descending.
    """
    sorted_articles = sorted(
        articles,
        key=lambda a: a.get("publishedAt", ""),
        reverse=True,
    )
    return sorted_articles[:n]


@tool
def fetch_top_news(topic: str) -> list[dict[str, Any]]:
    """Fetch the top recent news articles for a given topic.

    Calls the NewsAPI to retrieve up to 10 recent articles for the specified
    topic, then returns the top 3 most recent ones sorted by publication date.

    Args:
        topic: The news topic to search for (e.g., 'AI', 'finance', 'politics').

    Returns:
        List of up to 3 article dicts, each with:
        - title: Article headline
        - url: Link to the full article
        - publishedAt: ISO 8601 publication timestamp
        - description: Brief article description or excerpt
        - source: Name of the news source
    """
    articles = _fetch_articles(topic)
    return select_top_articles(articles, n=3)
