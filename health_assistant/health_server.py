import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import memory_store
from query_constructor import HealthAssistantQueryConstructor

logger = logging.getLogger(__name__)

HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8000"))

query_constructor = HealthAssistantQueryConstructor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory_store.init_db()
    yield


app = FastAPI(title="Health Server", description="Pediatric care middleware", lifespan=lifespan)


@app.post("/memory")
async def store_data(user_id: str, query: str):
    try:
        metadata = {
            "speaker": user_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "type": "message",
        }
        result = memory_store.store_episode(user_id, query, metadata)
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
