import sqlite3
import json
import uuid
import re
from datetime import datetime
from db import get_connection


class KnowledgeBase:
    """RAG knowledge store using SQLite FTS5 for fast text search."""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_connection()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_documents (
                id TEXT PRIMARY KEY,
                source_type TEXT,
                source_url TEXT,
                title TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS kb_search
            USING fts5(id, title, content, source_type)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                chunk_index INTEGER,
                content TEXT,
                word_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunk_search
            USING fts5(id, content, document_id)
        """)

        conn.commit()

    def add_document(self, source_type, source_url, title, content, metadata=None):
        """Add a document to the knowledge base and chunk it."""
        conn = get_connection()
        doc_id = str(uuid.uuid4())[:8]

        conn.execute(
            "INSERT OR REPLACE INTO kb_documents (id, source_type, source_url, title, content, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, source_type, source_url, title, content, json.dumps(metadata or {}))
        )

        try:
            conn.execute(
                "INSERT INTO kb_search (id, title, content, source_type) VALUES (?, ?, ?, ?)",
                (doc_id, title, content[:5000], source_type)
            )
        except Exception:
            pass

        chunks = self._chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_c{i}"
            conn.execute(
                "INSERT OR REPLACE INTO kb_chunks (id, document_id, chunk_index, content, word_count) VALUES (?, ?, ?, ?, ?)",
                (chunk_id, doc_id, i, chunk, len(chunk.split()))
            )
            try:
                conn.execute(
                    "INSERT INTO kb_chunk_search (id, content, document_id) VALUES (?, ?, ?)",
                    (chunk_id, chunk, doc_id)
                )
            except Exception:
                pass

        conn.commit()
        return doc_id

    def _chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into overlapping chunks of ~chunk_size words."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        return chunks if chunks else [text[:2000]]

    def search(self, query, limit=5, source_type=None):
        """Search the knowledge base for relevant chunks."""
        conn = get_connection()
        results = []

        clean_query = re.sub(r'[^\w\s]', '', query)
        search_terms = clean_query.split()[:10]

        if not search_terms:
            return results

        fts_query = " OR ".join(search_terms)

        try:
            if source_type:
                cursor = conn.execute("""
                    SELECT cs.id, cs.content, cs.document_id,
                           d.source_url, d.title, d.source_type
                    FROM kb_chunk_search cs
                    JOIN kb_documents d ON cs.document_id = d.id
                    WHERE kb_chunk_search MATCH ? AND d.source_type = ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, source_type, limit))
            else:
                cursor = conn.execute("""
                    SELECT cs.id, cs.content, cs.document_id,
                           d.source_url, d.title, d.source_type
                    FROM kb_chunk_search cs
                    JOIN kb_documents d ON cs.document_id = d.id
                    WHERE kb_chunk_search MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit))

            for row in cursor.fetchall():
                results.append({
                    "chunk_id": row[0],
                    "content": row[1],
                    "document_id": row[2],
                    "source_url": row[3],
                    "title": row[4],
                    "source_type": row[5]
                })
        except Exception:
            like_query = f"%{search_terms[0]}%"
            try:
                cursor = conn.execute("""
                    SELECT id, content, document_id
                    FROM kb_chunks
                    WHERE content LIKE ?
                    LIMIT ?
                """, (like_query, limit))
                for row in cursor.fetchall():
                    results.append({
                        "chunk_id": row[0],
                        "content": row[1],
                        "document_id": row[2],
                        "source_url": "",
                        "title": "",
                        "source_type": "unknown"
                    })
            except Exception:
                pass

        return results

    def get_agent_context(self, query, agent_type, limit=3):
        """Get relevant context for a specific agent type."""
        agent_source_map = {
            "seo": ["website", "seo_data", "competitor"],
            "content": ["website", "blog", "competitor"],
            "ppc": ["website", "ads_data", "competitor"],
            "analytics": ["analytics", "website"],
            "cro": ["website", "analytics"],
            "research": ["competitor", "market_data", "website"],
            "crm": ["website", "analytics"],
            "smm": ["website", "social_data"],
            "brand": ["website", "competitor"],
            "web_ux": ["website"],
        }

        preferred_sources = agent_source_map.get(agent_type, ["website"])

        all_results = []
        for source in preferred_sources:
            results = self.search(query, limit=2, source_type=source)
            all_results.extend(results)

        general = self.search(query, limit=2)
        all_results.extend(general)

        seen = set()
        unique = []
        for r in all_results:
            if r["chunk_id"] not in seen:
                seen.add(r["chunk_id"])
                unique.append(r)

        if not unique:
            return ""

        context_parts = ["RETRIEVED KNOWLEDGE (from crawled data):"]
        for r in unique[:limit]:
            source = f"[{r['source_type']}]" if r['source_type'] else ""
            title = f" - {r['title']}" if r['title'] else ""
            context_parts.append(f"\n{source}{title}:\n{r['content'][:500]}")

        return "\n".join(context_parts)

    def get_stats(self):
        """Return knowledge base statistics."""
        conn = get_connection()
        docs = conn.execute("SELECT COUNT(*) FROM kb_documents").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM kb_chunks").fetchone()[0]
        sources = conn.execute(
            "SELECT source_type, COUNT(*) FROM kb_documents GROUP BY source_type"
        ).fetchall()
        return {
            "total_documents": docs,
            "total_chunks": chunks,
            "sources": {row[0]: row[1] for row in sources}
        }

    def delete_by_source(self, source_url):
        """Delete all documents from a specific source."""
        conn = get_connection()
        cursor = conn.execute(
            "SELECT id FROM kb_documents WHERE source_url = ?", (source_url,)
        )
        doc_ids = [row[0] for row in cursor.fetchall()]

        for doc_id in doc_ids:
            conn.execute("DELETE FROM kb_chunks WHERE document_id = ?", (doc_id,))
            try:
                conn.execute(
                    "DELETE FROM kb_chunk_search WHERE document_id = ?", (doc_id,)
                )
            except Exception:
                pass

        conn.execute("DELETE FROM kb_documents WHERE source_url = ?", (source_url,))
        try:
            for doc_id in doc_ids:
                conn.execute("DELETE FROM kb_search WHERE id = ?", (doc_id,))
        except Exception:
            pass

        conn.commit()


_kb_instance = None


def get_knowledge_base():
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
