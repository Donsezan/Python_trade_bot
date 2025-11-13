from abc import ABC, abstractmethod
from typing import List, Dict
from trading_bot.models import NewsRecord

class NewsAnalyzer(ABC):
    """Abstract base class for a news analyzer."""

    @abstractmethod
    def ingest(self, raw_source: Dict) -> NewsRecord:
        """Ingest a raw news source and return a NewsRecord."""
        pass

    @abstractmethod
    def summarize(self, news: Dict) -> str:
        """Summarize a news article."""
        pass

    @abstractmethod
    def query(self, query_text: str, k: int = 5) -> List[NewsRecord]:
        """Query the RAG store for relevant news."""
        pass
