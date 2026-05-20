from __future__ import annotations

from typing import Any, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleKnowledgeRetriever:
    """Lightweight local RAG style retriever.

    This avoids any external vector database for the first demo. In production,
    replace this with pgvector, Pinecone, Weaviate, Elasticsearch, or Vertex AI Search.
    """

    def __init__(self, rows: List[Dict[str, Any]]):
        self.rows = rows
        self.documents = [self._row_to_text(row) for row in rows]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.documents) if self.documents else None

    @staticmethod
    def _row_to_text(row: Dict[str, Any]) -> str:
        source = row.get("_source_table", "knowledge")
        fields = []
        for key, value in row.items():
            if value is None:
                continue
            fields.append(f"{key}: {value}")
        return f"source_table: {source}. " + ". ".join(fields)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
        ranked_indices = scores.argsort()[::-1][:top_k]
        results: List[Dict[str, Any]] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                continue
            row = dict(self.rows[idx])
            row["retrieval_score"] = round(float(scores[idx]), 4)
            row["document_text_combined"] = self.documents[idx]
            results.append(row)
        return results
