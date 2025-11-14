from typing import List
from trading_bot.persistence.sqlite_persistence import NewsRAG, persistence

class RAGStore:
    """Provides an interface to the RAG store."""

    def __init__(self):
        """Initialize the RAGStore."""
        pass

    def get_latest_news(self, k: int = 5) -> List[NewsRAG]:
        """
        Get the k most recent news articles from the RAG store.

        Args:
            k: The number of news articles to retrieve.

        Returns:
            A list of NewsRAG objects.
        """
        session = persistence.get_session()
        try:
            return session.query(NewsRAG).order_by(NewsRAG.published_at.desc()).limit(k).all()
        finally:
            session.close()

rag_store = RAGStore()
