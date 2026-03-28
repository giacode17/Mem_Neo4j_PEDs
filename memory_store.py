"""
Memory Store - PostgreSQL + pgvector replacement for MemMachine.
Handles episodic memory (conversation history), profile memory (user summaries),
and the pediatric knowledge base (aftercare docs, medication guides, symptom rules).
"""

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# Load .env from the project root (same directory as memory_store.py)
load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/caremykids")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
PROFILE_UPDATE_EVERY = 5  # update profile summary every N stored episodes

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
    return _pool


@contextmanager
def _get_conn():
    conn = _get_pool().getconn()
    try:
        yield conn
    finally:
        _get_pool().putconn(conn)


def init_db():
    """Create tables and indexes if they don't exist."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS episodes (
                    id          SERIAL PRIMARY KEY,
                    user_id     VARCHAR(255) NOT NULL,
                    content     TEXT NOT NULL,
                    embedding   vector({EMBEDDING_DIM}),
                    metadata    JSONB DEFAULT '{{}}',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id     VARCHAR(255) PRIMARY KEY,
                    content     TEXT NOT NULL,
                    updated_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS episodes_user_id_idx
                ON episodes (user_id);
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id          SERIAL PRIMARY KEY,
                    source      VARCHAR(50) NOT NULL,
                    doc_id      VARCHAR(100),
                    title       TEXT,
                    content     TEXT NOT NULL,
                    embedding   vector({EMBEDDING_DIM}),
                    metadata    JSONB DEFAULT '{{}}',
                    created_at  TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS knowledge_base_source_idx
                ON knowledge_base (source);
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS symptom_rules (
                    id          SERIAL PRIMARY KEY,
                    symptom     VARCHAR(100) NOT NULL UNIQUE,
                    rule        JSONB NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkins (
                    id                      SERIAL PRIMARY KEY,
                    patient_id              VARCHAR(50) NOT NULL,
                    checkin_date            DATE NOT NULL,
                    fever_c                 NUMERIC(4,1),
                    pain_0_10               INTEGER,
                    vomiting_events_6h      INTEGER,
                    breathing_difficulty    BOOLEAN,
                    missed_med_doses_24h    INTEGER,
                    alert_triggered         BOOLEAN,
                    created_at              TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
    logger.info("Database initialized successfully")


def _get_embedding(text: str) -> list[float]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def store_episode(user_id: str, content: str, metadata: dict | None = None) -> dict:
    """Store a conversation message with its embedding."""
    embedding = _get_embedding(content)
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO episodes (user_id, content, embedding, metadata)
                VALUES (%s, %s, %s::vector, %s)
                RETURNING id, created_at
            """, (user_id, content, embedding, json.dumps(metadata or {})))
            result = cur.fetchone()

            # Count episodes for this user to decide if profile needs updating
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM episodes WHERE user_id = %s",
                (user_id,)
            )
            count = cur.fetchone()["cnt"]
        conn.commit()

    if count % PROFILE_UPDATE_EVERY == 0:
        _update_profile(user_id)

    return {"id": result["id"], "created_at": str(result["created_at"])}


def search_memory(user_id: str, query: str, limit: int = 5) -> dict:
    """
    Semantic search over episodes + fetch profile.
    Returns the same shape the old MemMachine /v1/memories/search did:
      { "content": { "episodic_memory": [...], "profile_memory": [...] } }
    """
    query_embedding = _get_embedding(query)
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT content, metadata, created_at,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM episodes
                WHERE user_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (query_embedding, user_id, query_embedding, limit))
            episodes = cur.fetchall()

            cur.execute(
                "SELECT content FROM profiles WHERE user_id = %s",
                (user_id,)
            )
            profile_row = cur.fetchone()

    episodic_memory = [
        {
            "content": ep["content"],
            "timestamp": str(ep["created_at"]),
            "similarity": float(ep["similarity"]),
        }
        for ep in episodes
    ]
    profile_memory = [profile_row["content"]] if profile_row else []

    return {
        "content": {
            "episodic_memory": episodic_memory,
            "profile_memory": profile_memory,
        }
    }


def search_knowledge(query: str, limit: int = 3, source: str | None = None) -> list[dict]:
    """
    Semantic search over the knowledge base (aftercare docs, medication guides, dialogues).
    Optionally filter by source: 'aftercare' | 'med_guide' | 'dialogue'
    """
    query_embedding = _get_embedding(query)
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if source:
                cur.execute("""
                    SELECT doc_id, title, content, source, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM knowledge_base
                    WHERE source = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, source, query_embedding, limit))
            else:
                cur.execute("""
                    SELECT doc_id, title, content, source, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM knowledge_base
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
            rows = cur.fetchall()

    return [
        {
            "doc_id": r["doc_id"],
            "title": r["title"],
            "content": r["content"],
            "source": r["source"],
            "similarity": float(r["similarity"]),
        }
        for r in rows
    ]


def get_symptom_rules() -> list[dict]:
    """Return all symptom triage rules."""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT symptom, rule FROM symptom_rules ORDER BY id")
            rows = cur.fetchall()
    return [{"symptom": r["symptom"], "rule": r["rule"]} for r in rows]


def search_web(query: str, max_results: int = 3) -> list[dict]:
    """
    Web search via Tavily. Returns clean text snippets ready for RAG injection.
    Falls back to empty list if Tavily key is missing or request fails.
    """
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set — skipping web search")
        return []
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )
        results = []
        if response.get("answer"):
            results.append({
                "title": "Web Summary",
                "content": response["answer"],
                "url": "",
            })
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "url": r.get("url", ""),
            })
        return results[:max_results]
    except Exception:
        logger.exception("Tavily web search failed for query: %s", query)
        return []


def _update_profile(user_id: str) -> None:
    """Summarize the most recent episodes into a profile using GPT."""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT content FROM episodes
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,))
            rows = cur.fetchall()

    if not rows:
        return

    messages_text = "\n".join(r["content"] for r in reversed(rows))
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize the key facts about this child from the conversation history. "
                        "Be concise. Focus on: name, age, weight, allergies, medical conditions, "
                        "medications, and important health history."
                    ),
                },
                {"role": "user", "content": messages_text},
            ],
        )
        summary = response.choices[0].message.content

        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO profiles (user_id, content, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE
                        SET content = EXCLUDED.content,
                            updated_at = NOW()
                """, (user_id, summary))
            conn.commit()
        logger.info("Profile updated for user %s", user_id)
    except Exception:
        logger.exception("Failed to update profile for user %s", user_id)
