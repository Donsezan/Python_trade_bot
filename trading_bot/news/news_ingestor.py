import requests
from bs4 import BeautifulSoup
from trading_bot.config import config
from typing import List, Dict

class NewsIngestor:
    """Ingests news from various sources."""

    def __init__(self):
        """Initialize the NewsIngestor."""
        self.news_config = config.get_news_config()

    def fetch_cointelegraph_news(self) -> List[Dict[str, str]]:
        """
        Fetch the latest news from CoinTelegraph.

        Returns:
            A list of dictionaries, where each dictionary represents a news article.
        """
        url = self.news_config.get("cointelegraph", {}).get("url")
        if not url:
            return []

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching news from {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        for post in soup.find_all('li', class_='posts-listing__item'):
            title_element = post.find('h3', class_='post-card-inline__title')
            link_element = post.find('a', class_='post-card-inline__figure-link')

            if title_element and link_element:
                article_url = link_element['href']
                if not article_url.startswith('http'):
                    article_url = f"https://cointelegraph.com{article_url}"

                content = self._fetch_article_content(article_url)

                articles.append({
                    "title": title_element.get_text(strip=True),
                    "url": article_url,
                    "source": "CoinTelegraph",
                    "content": content
                })

        return articles

    def _fetch_article_content(self, url: str) -> str:
        """Fetch the content of a single news article."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # This selector is simplified and might need adjustment
            content_div = soup.find('div', class_='post-content')
            return content_div.get_text(strip=True) if content_div else ""
        except requests.RequestException as e:
            print(f"Error fetching article content from {url}: {e}")
            return ""

news_ingestor = NewsIngestor()
