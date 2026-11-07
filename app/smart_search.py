"""Ranked search over scheme records using TF-IDF and cosine similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fields combined into one searchable document per record.
TEXT_FIELDS = (
    "scheme_name",
    "category",
    "ministry",
    "benefit",
    "eligibility",
    "documents_required",
)


def record_to_text(record):
    """Flatten the searchable fields of one record into a single string."""
    parts = []
    for field in TEXT_FIELDS:
        value = record.get(field)
        if not value:
            continue
        if isinstance(value, (list, tuple, set)):
            parts.append(" ".join(str(item) for item in value))
        else:
            parts.append(str(value))
        if field == "scheme_name":
            # Repeat the name so name matches rank above body-text matches.
            parts.append(str(value))
    return " ".join(parts)


class SmartSearcher:
    """Fit TF-IDF once on the records, then rank any number of queries."""

    def __init__(self, records):
        self.records = list(records)
        self._vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 2)
        )
        self._matrix = None
        if self.records:
            texts = [record_to_text(record) for record in self.records]
            self._matrix = self._vectorizer.fit_transform(texts)

    def search(self, query, top_k=5):
        """Return up to top_k (record, score) pairs, best first.

        Records with a score of 0 are dropped, so an unrelated query
        returns an empty list.
        """
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if not query.strip() or self._matrix is None or top_k < 1:
            return []

        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix).ravel()
        ranked = sorted(
            range(len(scores)), key=lambda index: scores[index], reverse=True
        )
        return [
            (self.records[index], float(scores[index]))
            for index in ranked[:top_k]
            if scores[index] > 0
        ]
