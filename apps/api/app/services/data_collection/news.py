"""News data collection using web search.

For MVP, we use a simple approach to collect recent news about a company.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class NewsCollector:
    """Collect recent news articles about a company."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def search_news(
        self,
        company_name: str,
        days_back: int = 365,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Search for recent news articles about a company.

        Uses Google News RSS as a free news source for MVP.

        Args:
            company_name: Name of the company to search for.
            days_back: How many days back to search.
            max_results: Maximum number of results.

        Returns:
            List of news article dicts with title, url, published_date, source.
        """
        client = await self._get_client()
        articles: list[dict[str, Any]] = []

        try:
            # Google News RSS feed (no API key required)
            url = "https://news.google.com/rss/search"
            params = {
                "q": f"{company_name} 企業",
                "hl": "ja",
                "gl": "JP",
                "ceid": "JP:ja",
            }
            resp = await client.get(url, params=params)
            resp.raise_for_status()

            # Parse RSS XML
            from xml.etree import ElementTree

            root = ElementTree.fromstring(resp.content)
            channel = root.find("channel")
            if channel is None:
                return articles

            cutoff_date = date.today() - timedelta(days=days_back)

            for item in channel.findall("item")[:max_results]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source = item.findtext("source", "")

                articles.append({
                    "title": title,
                    "url": link,
                    "published_date": pub_date,
                    "source": source,
                })

        except (httpx.HTTPError, Exception) as e:
            logger.warning("Failed to fetch news for %s: %s", company_name, e)

        return articles

    async def summarize_news_context(
        self, articles: list[dict[str, Any]]
    ) -> str:
        """Create a text summary of news articles for AI analysis.

        Args:
            articles: List of news article dicts.

        Returns:
            Formatted text summary of recent news.
        """
        if not articles:
            return "直近のニュース記事は見つかりませんでした。"

        lines = ["【直近のニュース記事】"]
        for i, article in enumerate(articles[:15], 1):
            source = article.get("source", "不明")
            title = article.get("title", "")
            pub_date = article.get("published_date", "")
            lines.append(f"{i}. [{source}] {title} ({pub_date})")

        return "\n".join(lines)
