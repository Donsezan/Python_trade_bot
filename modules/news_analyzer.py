# news_analyzer.py
import sqlite3
import datetime
import difflib
from typing import List, Dict, Any, Optional

DEFAULT_SIMILARITY_THRESHOLD = 0.80

class NewsAnalyzer:
    """
    RAG backed News Analyzer.
    - Keeps a `news_rag` table in the same SQLite DB as the logger (or its own DB).
    - Accepts a list of raw news items and returns summaries and an aggregated summary.
    - Uses fuzzy title matching to avoid re-evaluating similar/duplicate titles.
    - Replace `summarize_text_via_llm` stub with real LLM call later.
    """

    def __init__(self, db_path: str = "trading_bot.db", similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._cursor = self._conn.cursor()
        self._ensure_table()

    def _ensure_table(self):
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_rag (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                url TEXT,
                fingerprint TEXT,
                summary TEXT,
                created_at TEXT
            )
        """)
        self._conn.commit()

    def _fingerprint_title(self, title: str) -> str:
        # Lightweight normalization fingerprint. Replace with embedding in future.
        return ''.join(ch for ch in title.lower() if ch.isalnum() or ch.isspace()).strip()

    def _find_similar(self, title_fp: str) -> Optional[Dict[str, Any]]:
        # naive scan through stored fingerprints -> compute fuzzy similarity vs stored titles
        self._cursor.execute("SELECT id, title, fingerprint, summary FROM news_rag")
        rows = self._cursor.fetchall()
        best = None
        best_ratio = 0.0
        for r in rows:
            r_id, r_title, r_fp, r_summary = r
            ratio = difflib.SequenceMatcher(a=title_fp, b=r_fp).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best = {"id": r_id, "title": r_title, "fp": r_fp, "summary": r_summary, "ratio": ratio}
        if best and best_ratio >= self.similarity_threshold:
            return best
        return None

    def summarize_text_via_llm(self, title: str, content: str) -> Dict[str, Any]:
        """
        Placeholder LLM summarizer.
        Replace this method with real LLM integration (e.g., OpenAI, Google Flash).
        Returns {'summary': str, 'sentiment': 'positive/neutral/negative', 'score': float}
        """
        # Simple heuristic summarizer for demo: use title + first 200 chars of content
        summary = f"{title}. {content[:200].split('.')[0]}."
        # Naive sentiment placeholder based on keywords
        low = content.lower()
        score = 0.5
        sentiment = "neutral"
        if any(w in low for w in ("surge", "moon", "rally", "bull")):
            sentiment = "positive"; score = 0.85
        elif any(w in low for w in ("crash", "selloff", "dump", "bear", "drop")):
            sentiment = "negative"; score = 0.85
        return {"summary": summary, "sentiment": sentiment, "score": score}

    def ingest_news_items(self, raw_news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        raw_news_items: list[{"title":..., "content":..., "source":..., "url":..., "timestamp":...}]
        Returns a list of dicts with stored/returned summaries and metadata.
        - avoids re-summarising similar items (uses fuzzy title matching)
        """
        results = []
        for item in raw_news_items:
            title = item.get("title", "")[:800]
            content = item.get("content", "")
            source = item.get("source", "")
            url = item.get("url", "")
            ts = item.get("timestamp", datetime.datetime.utcnow().isoformat())

            fp = self._fingerprint_title(title)
            similar = self._find_similar(fp)
            if similar:
                # reuse existing summary
                results.append({
                    "title": title,
                    "source": source,
                    "url": url,
                    "summary": similar["summary"],
                    "cached": True,
                    "similarity": similar["ratio"]
                })
            else:
                # summarize with LLM (placeholder)
                llm_res = self.summarize_text_via_llm(title, content)
                summary_text = llm_res["summary"]
                # store in RAG
                self._cursor.execute(
                    "INSERT INTO news_rag (title, source, url, fingerprint, summary, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, source, url, fp, summary_text, ts)
                )
                self._conn.commit()
                results.append({
                    "title": title,
                    "source": source,
                    "url": url,
                    "summary": summary_text,
                    "sentiment": llm_res.get("sentiment"),
                    "score": llm_res.get("score"),
                    "cached": False
                })
        return results

    def aggregate_cycle_summary(self, items: List[Dict[str, Any]], max_sentences: int = 5) -> Dict[str, Any]:
        """
        Create an aggregated summary for recent items. Returns:
        {
          'summary': str,
          'sentiment': 'positive'|'neutral'|'negative',
          'score': float,
          'items': [...]
        }
        """
        if not items:
            return {"summary": "", "sentiment": "neutral", "score": 0.5, "items": []}

        # Concatenate summaries and compute naive aggregate sentiment
        concat = " ".join(i.get("summary", "") for i in items)
        # Very naive "aggregation" - in future call LLM to synthesize; here we pick first N sentences
        sentences = concat.split('.')
        agg_sents = [s.strip() for s in sentences if s.strip()][:max_sentences]
        aggregated_summary = ". ".join(agg_sents) + ('.' if agg_sents else '')

        # Aggregate sentiment by simple averaging of provided scores (if available)
        scores = [i.get("score") for i in items if i.get("score") is not None]
        avg_score = (sum(scores)/len(scores)) if scores else 0.5
        # map to label
        sentiment = "neutral"
        if avg_score >= 0.66:
            sentiment = "positive"
        elif avg_score <= 0.34:
            sentiment = "negative"

        return {
            "summary": aggregated_summary,
            "sentiment": sentiment,
            "score": avg_score,
            "items": items
        }

    def get_recent_items(self, limit: int = 20) -> List[Dict[str, Any]]:
        self._cursor.execute("SELECT title, source, url, summary, created_at FROM news_rag ORDER BY id DESC LIMIT ?", (limit,))
        rows = self._cursor.fetchall()
        return [{"title": r[0], "source": r[1], "url": r[2], "summary": r[3], "created_at": r[4]} for r in rows]

    def close(self):
        self._conn.close()
