from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class NewsRecord:
    """Data model for a news article in the RAG store."""
    id: int
    title: str
    summary: str
    source: str
    published_at: datetime
    fingerprint: str
    embedding: Optional[bytes] = None
    created_at: datetime = datetime.now()
