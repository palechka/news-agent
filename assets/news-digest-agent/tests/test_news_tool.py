"""Unit tests for the news_tool module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import patch, MagicMock
import pytest

from news_tool import _fetch_articles, select_top_articles, fetch_top_news


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_article(title: str, published: str, source: str = "Test Source") -> dict:
    return {
        "title": title,
        "url": f"https://example.com/{title.lower().replace(' ', '-')}",
        "publishedAt": published,
        "description": f"Description of {title}",
        "source": source,
    }


def _make_api_response(articles: list[dict]) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    # Convert our clean dicts into the raw API shape
    raw_articles = []
    for a in articles:
        raw_articles.append({
            "title": a["title"],
            "url": a["url"],
            "publishedAt": a["publishedAt"],
            "description": a["description"],
            "content": None,
            "source": {"name": a["source"]},
        })
    mock_resp.json.return_value = {"articles": raw_articles, "status": "ok", "totalResults": len(raw_articles)}
    return mock_resp


# --------------------------------------------------------------------------- #
# _fetch_articles
# --------------------------------------------------------------------------- #

class TestFetchArticles:
    def test_returns_articles_on_success(self):
        articles = [_make_article("AI Breakthrough", "2024-10-30T10:00:00Z")]
        with patch("news_tool.requests.get", return_value=_make_api_response(articles)) as mock_get:
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                result = _fetch_articles("AI")
        assert len(result) == 1
        assert result[0]["title"] == "AI Breakthrough"
        assert result[0]["source"] == "Test Source"
        mock_get.assert_called_once()

    def test_returns_empty_list_when_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NEWS_API_KEY", None)
            result = _fetch_articles("finance")
        assert result == []

    def test_returns_empty_list_on_request_exception(self):
        import requests as req_lib
        with patch("news_tool.requests.get", side_effect=req_lib.exceptions.ConnectionError("fail")):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                result = _fetch_articles("politics")
        assert result == []

    def test_returns_empty_list_on_api_error_status(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP 429")
        with patch("news_tool.requests.get", return_value=mock_resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                result = _fetch_articles("politics")
        assert result == []

    def test_handles_missing_description_with_content_fallback(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "articles": [{
                "title": "Test",
                "url": "https://example.com",
                "publishedAt": "2024-10-30T09:00:00Z",
                "description": None,
                "content": "Article content fallback",
                "source": {"name": "Source A"},
            }]
        }
        with patch("news_tool.requests.get", return_value=mock_resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                result = _fetch_articles("test")
        assert result[0]["description"] == "Article content fallback"

    def test_returns_empty_list_when_api_returns_no_articles(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"articles": [], "status": "ok", "totalResults": 0}
        with patch("news_tool.requests.get", return_value=mock_resp):
            with patch.dict(os.environ, {"NEWS_API_KEY": "test-key"}):
                result = _fetch_articles("obscure topic xyz")
        assert result == []


# --------------------------------------------------------------------------- #
# select_top_articles
# --------------------------------------------------------------------------- #

class TestSelectTopArticles:
    def test_returns_top_3_by_recency(self):
        articles = [
            _make_article("Old News", "2024-10-28T08:00:00Z"),
            _make_article("Latest News", "2024-10-30T12:00:00Z"),
            _make_article("Mid News", "2024-10-29T10:00:00Z"),
            _make_article("Very Old", "2024-10-25T06:00:00Z"),
            _make_article("Recent", "2024-10-30T08:00:00Z"),
        ]
        result = select_top_articles(articles, n=3)
        assert len(result) == 3
        assert result[0]["title"] == "Latest News"
        assert result[1]["title"] == "Recent"
        assert result[2]["title"] == "Mid News"

    def test_returns_all_articles_when_fewer_than_n(self):
        articles = [
            _make_article("Only One", "2024-10-30T10:00:00Z"),
            _make_article("Only Two", "2024-10-29T10:00:00Z"),
        ]
        result = select_top_articles(articles, n=3)
        assert len(result) == 2

    def test_returns_empty_list_for_empty_input(self):
        result = select_top_articles([], n=3)
        assert result == []

    def test_default_n_is_3(self):
        articles = [_make_article(f"Article {i}", f"2024-10-{20+i}T10:00:00Z") for i in range(5)]
        result = select_top_articles(articles)
        assert len(result) == 3

    def test_handles_missing_published_at(self):
        articles = [
            {"title": "No Date", "url": "", "publishedAt": "", "description": "", "source": "S"},
            {"title": "Has Date", "url": "", "publishedAt": "2024-10-30T10:00:00Z", "description": "", "source": "S"},
        ]
        result = select_top_articles(articles, n=2)
        # Should not raise; sorted by empty string for missing dates
        assert len(result) == 2


# --------------------------------------------------------------------------- #
# fetch_top_news (LangChain @tool wrapper)
# --------------------------------------------------------------------------- #

class TestFetchTopNewsTool:
    def test_tool_invokable_with_topic(self):
        articles = [_make_article(f"News {i}", f"2024-10-{28+i}T10:00:00Z") for i in range(3)]
        with patch("news_tool._fetch_articles", return_value=articles):
            result = fetch_top_news.invoke({"topic": "AI"})
        assert isinstance(result, list)
        assert len(result) == 3

    def test_tool_returns_top_3_when_more_available(self):
        articles = [_make_article(f"News {i}", f"2024-10-{20+i}T10:00:00Z") for i in range(8)]
        with patch("news_tool._fetch_articles", return_value=articles):
            result = fetch_top_news.invoke({"topic": "finance"})
        assert len(result) == 3

    def test_tool_returns_empty_list_when_no_results(self):
        with patch("news_tool._fetch_articles", return_value=[]):
            result = fetch_top_news.invoke({"topic": "nonexistent topic xyz"})
        assert result == []
