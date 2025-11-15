import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from typing import List, Dict

class ChromaDBService:
    """Provides an interface to the ChromaDB service."""

    def __init__(self, path: str = "./chroma_db"):
        """
        Initialize the ChromaDBService.

        Args:
            path: The path to the ChromaDB database.
        """
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="news",
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"}
        )

    def add_news(self, title: str, summary: str, source: str, published_at: datetime):
        """
        Add a news article to the ChromaDB collection.

        Args:
            title: The title of the news article.
            summary: The summary of the news article.
            source: The source of the news article.
            published_at: The publication timestamp of the article.
        """
        self.collection.add(
            documents=[title],
            metadatas=[{
                "source": source,
                "summary": summary,
                "title": title,
                "published_at": int(published_at.timestamp())
            }],
            ids=[title]
        )

    def is_news_present(self, title: str, threshold: float = 0.9) -> bool:
        """
        Check if a similar news article is already present in the collection.
        Similarity is checked based on the title embedding.

        Args:
            title: The title of the news article.
            threshold: The similarity threshold (e.g., 0.9 for 90% similarity).

        Returns:
            True if a similar article is found, False otherwise.
        """
        if self.collection.count() == 0:
            return False

        results = self.collection.query(
            query_texts=[title],
            n_results=1
        )

        if not results['distances'] or not results['distances'][0]:
            return False

        # Cosine similarity = 1 - cosine_distance. We want similarity >= threshold.
        # So 1 - distance >= threshold  => distance <= 1 - threshold
        return results['distances'][0][0] <= (1 - threshold)

    def get_latest_news(self, k: int = 5) -> List[Dict]:
        """
        Get the k most recent news articles from the RAG store.

        Args:
            k: The number of news articles to retrieve.

        Returns:
            A list of dictionaries, where each dictionary is the metadata of a news article.
        """
        all_news = self.collection.get()

        if 'metadatas' not in all_news or not all_news['metadatas']:
            return []

        # Sort the news by 'published_at' timestamp in descending order.
        sorted_news_metadatas = sorted(
            all_news['metadatas'],
            key=lambda meta: meta.get('published_at', 0),
            reverse=True
        )

        return sorted_news_metadatas[:k]

chroma_db_service = ChromaDBService()
