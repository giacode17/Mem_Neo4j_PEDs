import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_store
from query_constructor import HealthAssistantQueryConstructor

# ── Structured JSON logging (GCP Cloud Logging compatible) ──────────────────
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory_store.init_db()
    yield


app = FastAPI(title="Health Server", description="Pediatric care middleware", lifespan=lifespan)


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


@app.post("/memory")
async def store_data(user_id: str, query: str):
    try:
        metadata = {
            "speaker": user_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "type": "message",
        }
        result = memory_store.store_episode(user_id, query, metadata)
        logger.info(json.dumps({"type": "store", "user_id": user_id, "episode_id": result["id"]}))
        return {"status": "success", "data": result}
    except Exception:
        logger.exception("Error occurred in /memory store_data")
        return {"status": "error", "message": "Internal error in /memory store_data"}


@app.get("/memory")
async def get_data(query: str, user_id: str, timestamp: str):
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
        logger.exception("Error occurred in /memory get_data")
        return {"status": "error", "message": "Internal error in /memory get_data"}


@app.post("/memory/store-and-search")
async def store_and_search_data(user_id: str, query: str):
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
        logger.exception("Error occurred in store_and_search_data")
        return {"status": "error", "message": "Internal error in store_and_search"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=HEALTH_PORT)
