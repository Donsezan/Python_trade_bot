import hashlib
from datetime import datetime
from trading_bot.persistence.sqlite_persistence import NewsRAG, persistence
from typing import List, Dict

class NewsAnalyzer:
    """Analyzes and processes news articles."""

    def __init__(self):
        """Initialize the NewsAnalyzer."""
        pass

    def process_news(self, articles: List[Dict[str, str]]):
        """
        Process a list of news articles and save them to the RAG store.

        Args:
            articles: A list of news articles.
        """
        for article in articles:
            fingerprint = self._generate_fingerprint(article["title"])

            session = persistence.get_session()
            existing_article = session.query(NewsRAG).filter_by(fingerprint=fingerprint).first()
            session.close()

            if not existing_article:
                summary = self._generate_summary(article.get("content", ""))
                news_record = NewsRAG(
                    title=article["title"],
                    summary=summary,
                    source=article["source"],
                    published_at=datetime.now(),
                    fingerprint=fingerprint,
                )
                persistence.save(news_record)

    def _generate_fingerprint(self, title: str) -> str:
        """
        Generate a unique fingerprint for a news article based on its title.
        """
        return hashlib.sha256(title.encode('utf-8')).hexdigest()

    def _generate_summary(self, content: str) -> str:
        """
        Generate a summary from the article content.
        """
        # A simple summary: the first three sentences
        sentences = content.split('.')
        return '.'.join(sentences[:3]) + '.' if len(sentences) > 3 else content

news_analyzer = NewsAnalyzer()
