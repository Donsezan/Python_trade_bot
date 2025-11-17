from typing import List, Dict
from trading_bot.rag_store.chromadb_service import chroma_db_service

class RAGStore:
    """Provides an interface to the RAG store."""

    def __init__(self):
        """Initialize the RAGStore."""
        pass

    def get_latest_news(self, k: int = 5) -> List[Dict]:
        """
        Get the k most recent news articles from the RAG store.

        Args:
            k: The number of news articles to retrieve.

        Returns:
            A list of dictionaries containing the latest news articles.
        """
        return chroma_db_service.get_latest_news(k)

rag_store = RAGStore()
