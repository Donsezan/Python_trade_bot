from typing import List, Dict
from trading_bot.rag_store.chromadb_service import chroma_db_service
from datetime import datetime

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
            if not chroma_db_service.is_news_present(article["title"]):
                summary = self._generate_summary(article.get("content", ""))
                chroma_db_service.add_news(
                    title=article["title"],
                    summary=summary,
                    source=article["source"],
                    published_at=datetime.now()
                )

    def _generate_summary(self, content: str) -> str:
        """
        Generate a summary from the article content.
        """
        # A simple summary: the first three sentences
        sentences = content.split('.')
        return '.'.join(sentences[:3]) + '.' if len(sentences) > 3 else content

news_analyzer = NewsAnalyzer()
