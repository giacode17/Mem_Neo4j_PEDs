import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg2
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_store
from query_constructor import HealthAssistantQueryConstructor

# ── Structured JSON logging ──────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.now(tz=timezone.utc).isoformat(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
# ────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8000"))

query_constructor = HealthAssistantQueryConstructor()

# ── Prometheus metrics ───────────────────────────────────────────────────────
queries_total = Counter(
    "caremykids_queries_total",
    "Total number of queries processed",
    ["endpoint"],
)
query_latency = Histogram(
    "caremykids_query_latency_seconds",
    "Query latency in seconds",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)
errors_total = Counter(
    "caremykids_errors_total",
    "Total number of errors",
    ["endpoint"],
)
# ────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    memory_store.init_db()
    yield


app = FastAPI(title="CareMyKids API", description="Pediatric care middleware", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    t0 = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - t0) * 1000)
    logger.info(json.dumps({
        "type": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
    }))
    return response


# ── Landing page ─────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CareMyKids API</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 680px; margin: 80px auto; padding: 0 24px; color: #1a1a1a; }
    h1   { font-size: 2rem; margin-bottom: 4px; }
    p    { color: #555; line-height: 1.6; }
    .badge { display: inline-block; background: #e8f5e9; color: #2e7d32;
             padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; margin-bottom: 24px; }
    a    { color: #1976d2; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .links { margin-top: 32px; display: flex; gap: 16px; flex-wrap: wrap; }
    .btn { padding: 10px 20px; border-radius: 6px; font-size: 0.95rem;
           background: #1976d2; color: white; }
    .btn.secondary { background: #f5f5f5; color: #1a1a1a; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>CareMyKids API</h1>
  <span class="badge">● Live</span>
  <p>
    Memory-powered pediatric care assistant. Combines conversation memory,
    a pediatric knowledge base, and live web search to give parents
    personalized, context-aware answers.
  </p>
  <p>
    Built with <code>FastAPI</code> · <code>PostgreSQL + pgvector</code> ·
    <code>OpenAI</code> · <code>Tavily</code> · deployed on <code>GKE</code>.
  </p>
  <div class="links">
    <a class="btn" href="/docs">API Docs</a>
    <a class="btn secondary" href="/health">Health Check</a>
    <a class="btn secondary" href="/metrics">Metrics</a>
  </div>
</body>
</html>
"""


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    db_ok = False
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://localhost/caremykids"))
        conn.cursor().execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "checks": {
            "database": "ok" if db_ok else "error",
        },
        "version": "1.0.0",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


# ── Prometheus metrics endpoint ───────────────────────────────────────────────
@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── API endpoints ─────────────────────────────────────────────────────────────
@app.post("/memory")
async def store_data(user_id: str, query: str):
    with query_latency.labels("store").time():
        try:
            metadata = {
                "speaker": user_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "type": "message",
            }
            result = memory_store.store_episode(user_id, query, metadata)
            queries_total.labels("store").inc()
            logger.info(json.dumps({"type": "store", "user_id": user_id, "episode_id": result["id"]}))
            return {"status": "success", "data": result}
        except Exception:
            errors_total.labels("store").inc()
            logger.exception("Error occurred in /memory store_data")
            return {"status": "error", "message": "Internal error in /memory store_data"}


@app.get("/memory")
async def get_data(query: str, user_id: str, timestamp: str):
    with query_latency.labels("search").time():
        try:
            results = memory_store.search_memory(user_id, query)
            content = results.get("content", {})
            episodic_memory = content.get("episodic_memory", [])
            profile_memory = content.get("profile_memory", [])

            profile_str = "\n".join(str(p) for p in profile_memory) if profile_memory else ""
            context_str = "\n".join(str(c) for c in episodic_memory) if episodic_memory else ""

            knowledge_results = memory_store.search_knowledge(query, limit=3)
            knowledge_str = "\n\n".join(
                f"[{r['source']}] {r['title']}\n{r['content']}" for r in knowledge_results
            ) if knowledge_results else ""

            web_results = memory_store.search_web(query)
            web_str = "\n\n".join(
                f"[web] {r['title']}\n{r['content']}" for r in web_results
            ) if web_results else ""

            formatted_query = query_constructor.create_query(
                profile=profile_str,
                context=context_str,
                knowledge=knowledge_str,
                web=web_str,
                query=query,
            )

            queries_total.labels("search").inc()
            logger.info(json.dumps({
                "type": "search",
                "user_id": user_id,
                "episodes": len(episodic_memory),
                "knowledge_hits": len(knowledge_results),
                "web_hits": len(web_results),
            }))

            return {
                "status": "success",
                "data": {"profile": profile_memory, "context": episodic_memory},
                "formatted_query": formatted_query,
                "query_type": "pgvector",
            }
        except Exception:
            errors_total.labels("search").inc()
            logger.exception("Error occurred in /memory get_data")
            return {"status": "error", "message": "Internal error in /memory get_data"}


@app.post("/memory/store-and-search")
async def store_and_search_data(user_id: str, query: str):
    with query_latency.labels("store_and_search").time():
        try:
            metadata = {
                "speaker": user_id,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "type": "message",
            }
            memory_store.store_episode(user_id, query, metadata)

            results = memory_store.search_memory(user_id, query)
            content = results.get("content", {})
            episodic_memory = content.get("episodic_memory", [])
            profile_memory = content.get("profile_memory", [])

            profile_str = "\n".join(str(p) for p in profile_memory) if profile_memory else ""
            context_str = "\n".join(str(c) for c in episodic_memory) if episodic_memory else ""

            knowledge_results = memory_store.search_knowledge(query, limit=3)
            knowledge_str = "\n\n".join(
                f"[{r['source']}] {r['title']}\n{r['content']}" for r in knowledge_results
            ) if knowledge_results else ""

            web_results = memory_store.search_web(query)
            web_str = "\n\n".join(
                f"[web] {r['title']}\n{r['content']}" for r in web_results
            ) if web_results else ""

            formatted_response = query_constructor.create_query(
                profile=profile_str,
                context=context_str,
                knowledge=knowledge_str,
                web=web_str,
                query=query,
            )

            queries_total.labels("store_and_search").inc()
            logger.info(json.dumps({
                "type": "store_and_search",
                "user_id": user_id,
                "episodes": len(episodic_memory),
                "knowledge_hits": len(knowledge_results),
                "web_hits": len(web_results),
            }))

            if profile_memory and episodic_memory:
                return f"Profile: {profile_memory}\n\nContext: {episodic_memory}\n\nFormatted Response:\n{formatted_response}"
            if profile_memory:
                return f"Profile: {profile_memory}\n\nFormatted Response:\n{formatted_response}"
            if episodic_memory:
                return f"Context: {episodic_memory}\n\nFormatted Response:\n{formatted_response}"
            return f"Message ingested successfully. No relevant context found yet.\n\nFormatted Response:\n{formatted_response}"

        except Exception:
            errors_total.labels("store_and_search").inc()
            logger.exception("Error occurred in store_and_search_data")
            return {"status": "error", "message": "Internal error in store_and_search"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=HEALTH_PORT)
