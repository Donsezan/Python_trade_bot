import requests
from bs4 import BeautifulSoup
from trading_bot.config import config
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re

class NewsIngestor:
    """Ingests news from various sources."""

    def __init__(self):
        """Initialize the NewsIngestor."""
        self.news_config = config.get_news_config()

    def fetch_cointelegraph_news(self, last_run_time: Optional[datetime] = None) -> List[Dict[str, str]]:
        """
        Fetch the latest news from CoinTelegraph.

        Returns:
            A list of dictionaries, where each dictionary represents a news article.
        """

        url = "https://cointelegraph.com/tags/bitcoin"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching news from {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        for post in soup.find_all('article', class_='post-card-inline'):
            title_element = post.find('span', class_='post-card-inline__title')
            link_element = post.find('a', class_='post-card-inline__figure-link')
            if title_element and link_element:
                article_url = link_element['href']
                if not article_url.startswith('http'):
                    article_url = f"https://cointelegraph.com{article_url}"

                article_date = self._parse_article_date(post)
                
                if last_run_time and article_date:
                    # Ensure timezone awareness compatibility
                    if last_run_time.tzinfo is None and article_date.tzinfo:
                        last_run_time = last_run_time.replace(tzinfo=article_date.tzinfo)
                    elif last_run_time.tzinfo and article_date.tzinfo is None:
                        article_date = article_date.replace(tzinfo=last_run_time.tzinfo)
                        
                    if article_date <= last_run_time:
                        break

                content = self._fetch_article_content(article_url)

                articles.append({
                    "title": title_element.get_text(strip=True),
                    "url": article_url,
                    "source": "CoinTelegraph",
                    "published_at": article_date.isoformat() if article_date else None,
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
            content_div = soup.find('div', {'data-gtm-locator': 'articles'})
            return content_div.get_text(strip=True) if content_div else ""
        except requests.RequestException as e:
            print(f"Error fetching article content from {url}: {e}")
            return ""

    def _parse_article_date(self, post_element) -> Optional[datetime]:
        """Parse the publication date from the article element."""
        try:
            # Try to find a <time> element with datetime attribute
            time_element = post_element.find('time')
            if time_element and time_element.has_attr('datetime'):
                return datetime.fromisoformat(time_element['datetime'].replace('Z', '+00:00'))
            
            # Fallback: Parse "X hours ago" text
            # This is a basic implementation and might need to be more robust
            if time_element:
                text = time_element.get_text(strip=True)
                now = datetime.now()
                
                match = re.search(r'(\d+)\s+(minute|hour|day)s?\s+ago', text)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    
                    if unit == 'minute':
                        return now - timedelta(minutes=value)
                    elif unit == 'hour':
                        return now - timedelta(hours=value)
                    elif unit == 'day':
                        return now - timedelta(days=value)
            
            return None
        except Exception as e:
            print(f"Error parsing date: {e}")
            return None

news_ingestor = NewsIngestor()
