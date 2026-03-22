"""
Semantic Keyword Clustering for SwarmOps.
Groups related keywords into topic clusters using TF-IDF.
Gracefully degrades if scikit-learn is not installed.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed — semantic clustering uses fallback mode")


class KeywordClusterer:
    """Group keywords into semantic topic clusters using TF-IDF."""

    def __init__(self, similarity_threshold: float = 0.3):
        self.threshold = similarity_threshold

    def cluster_keywords(self, keywords: list) -> list:
        """
        Group a list of keywords into semantic clusters.

        Returns list of clusters, each with:
            - pillar: the primary/representative keyword
            - related: list of related keywords
            - cluster_size: number of keywords in cluster
        """
        clean = [kw.strip().lower() for kw in keywords if kw and kw.strip()]
        if len(clean) < 2:
            return [{"pillar": kw, "related": [], "cluster_size": 1} for kw in clean]

        if not HAS_SKLEARN:
            return self._fallback_cluster(clean)

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                stop_words="english",
                min_df=1,
                max_df=0.95,
            )
            tfidf_matrix = vectorizer.fit_transform(clean)
            sim = cosine_similarity(tfidf_matrix)

            assigned = set()
            clusters = []

            for i in range(len(clean)):
                if i in assigned:
                    continue
                cluster = [i]
                assigned.add(i)
                for j in range(i + 1, len(clean)):
                    if j not in assigned and sim[i][j] >= self.threshold:
                        cluster.append(j)
                        assigned.add(j)

                # Choose pillar = keyword with highest avg similarity to cluster peers
                if len(cluster) > 1:
                    avg_sims = [
                        (idx, sum(sim[idx][o] for o in cluster if o != idx) / (len(cluster) - 1))
                        for idx in cluster
                    ]
                    pillar_idx = max(avg_sims, key=lambda x: x[1])[0]
                else:
                    pillar_idx = cluster[0]

                related = [clean[idx] for idx in cluster if idx != pillar_idx]
                clusters.append({
                    "pillar": clean[pillar_idx],
                    "related": related,
                    "cluster_size": len(cluster),
                })

            clusters.sort(key=lambda c: c["cluster_size"], reverse=True)
            return clusters

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return self._fallback_cluster(clean)

    def _fallback_cluster(self, keywords: list) -> list:
        """Simple word-overlap fallback when sklearn unavailable."""
        assigned = set()
        clusters = []
        for i, kw in enumerate(keywords):
            if i in assigned:
                continue
            words_i = set(kw.split())
            cluster = [i]
            assigned.add(i)
            for j in range(i + 1, len(keywords)):
                if j in assigned:
                    continue
                words_j = set(keywords[j].split())
                # Share at least 1 non-trivial word
                overlap = words_i & words_j - {"the", "a", "an", "of", "for", "in", "to"}
                if overlap:
                    cluster.append(j)
                    assigned.add(j)
            related = [keywords[idx] for idx in cluster[1:]]
            clusters.append({
                "pillar": keywords[cluster[0]],
                "related": related,
                "cluster_size": len(cluster),
            })
        clusters.sort(key=lambda c: c["cluster_size"], reverse=True)
        return clusters

    def suggest_pillar_content(self, clusters: list) -> list:
        """
        For each cluster, suggest a pillar content piece.

        Returns list of content suggestions with:
            - pillar_keyword, supporting_keywords, content_type, estimated_word_count
        """
        suggestions = []
        for cluster in clusters:
            if cluster["cluster_size"] >= 3:
                content_type = "comprehensive guide"
            elif cluster["cluster_size"] == 2:
                content_type = "in-depth article"
            else:
                content_type = "focused blog post"

            suggestions.append({
                "pillar_keyword": cluster["pillar"],
                "supporting_keywords": cluster["related"][:5],
                "content_type": content_type,
                "estimated_word_count": 500 + 300 * cluster["cluster_size"],
            })
        return suggestions


# Module-level singleton
_clusterer = None


def get_keyword_clusterer(threshold: float = 0.3) -> KeywordClusterer:
    global _clusterer
    if _clusterer is None:
        _clusterer = KeywordClusterer(threshold)
    return _clusterer
