## CareMyKids

A memory-powered pediatric care assistant that helps parents get personalized, context-aware answers about their child's health.

## **Live: https://carekids.dev **

---

## What It Does

Parents can ask natural language questions and get answers grounded in:
- Their child's conversation history (remembered across sessions)
- A pediatric knowledge base (aftercare guides, medication safety, symptom rules)
- Live web search (Tavily) for location-based and up-to-date queries

Example queries:
- *"My child has a fever after tonsil surgery, is that normal?"*
- *"Where is the closest emergency center in Austin TX?"*
- *"Can I give ibuprofen with amoxicillin?"*

---

## Architecture

```
User (Browser)
    │
    ▼
Streamlit Frontend          ← https://carekids.dev
    │
    ▼
FastAPI Backend (RAG pipeline)
    ├── pgvector search     ← semantic search over knowledge base
    ├── Tavily web search   ← live web results
    └── memory search       ← conversation history + profile summary
    │
    ▼
PostgreSQL + pgvector       ← single database for everything
```

**Deployed on:** GKE (Google Kubernetes Engine) `us-central1-a`
**CI/CD:** GitHub Actions → Artifact Registry → `kubectl rollout restart`
**HTTPS:** GCP Managed Certificate + GKE Ingress (carekids.dev, www.carekids.dev)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Database | PostgreSQL 17 + pgvector |
| LLM | OpenAI (gpt-4.1-mini, gpt-4o) / Anthropic (Claude Haiku, Sonnet) |
| Web Search | Tavily |
| Container | Docker (linux/amd64) |
| Orchestration | Kubernetes / GKE |
| Ingress / TLS | GKE Ingress + GCP Managed Certificate |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus metrics + GCP Cloud Logging |

---

## Database Schema

```
episodes        — conversation history with embeddings
profiles        — auto-generated user summaries (updated every 5 messages)
knowledge_base  — 25 embedded docs (aftercare, medication guides, dialogues)
symptom_rules   — 5 pediatric triage rules
checkins        — synthetic patient check-in records
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/health` | Health check (DB connectivity) |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/memory` | Store a conversation turn |
| `GET` | `/memory` | Search memory + RAG pipeline |
| `POST` | `/memory/store-and-search` | Store then search (combined) |

---

## Quick Start (Local)

**Prerequisites:** Docker, Python 3.11+, OpenAI API key

```bash
# 1. Clone and configure
git clone https://github.com/giacode17/Mem_Neo4j_PEDs
cd Mem_Neo4j_PEDs

cp docs/.env.template .env
# Fill in: OPENAI_API_KEY, ANTHROPIC_API_KEY, TAVILY_API_KEY

# 2. Start the full stack
docker compose up

# 3. Load the knowledge base (first time only — runs automatically on first start)
docker compose run --rm backend python /app/load_dataset.py
```

- Frontend: `http://localhost:8501`
- Backend API: `http://localhost:8000/docs`

---

## Local Development (without Docker)

```bash
conda activate caremykids   # or: python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start backend
cd health_assistant/
python health_server.py     # runs on :8000

# Start frontend (new terminal)
cd frontend/
streamlit run app.py        # runs on :8501
```

Requires PostgreSQL 17 with pgvector extension running locally.

---

## Kubernetes Deployment

Manifests are in `k8s/`:

```bash
# Apply secrets first
kubectl create secret generic caremykids-secrets \
  --from-literal=OPENAI_API_KEY=... \
  --from-literal=ANTHROPIC_API_KEY=... \
  --from-literal=TAVILY_API_KEY=... \
  --from-literal=DATABASE_URL=postgresql://postgres@postgres/caremykids

# Deploy
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

The ingress uses a GCP global static IP (`caremykids-ip`) and a GCP Managed Certificate for automatic TLS.

---

## Project Structure

```
proj/
├── memory_store.py              # PostgreSQL + pgvector memory layer
├── load_dataset.py              # Dataset loader (idempotent)
├── base_query_constructor.py    # Base prompt builder
├── entrypoint.sh                # Backend startup (seeds DB on first run)
├── health_assistant/
│   ├── health_server.py         # FastAPI app + RAG pipeline + metrics
│   └── query_constructor.py     # Prompt assembly (profile + context + knowledge + web)
├── frontend/
│   ├── app.py                   # Streamlit chat UI
│   ├── llm.py                   # OpenAI + Anthropic clients
│   ├── gateway_client.py        # Backend API client
│   └── model_config.py          # Model list
├── dataset/                     # Pediatric knowledge base source files
├── k8s/                         # Kubernetes manifests
│   ├── postgres.yaml            # StatefulSet + PVC
│   ├── backend.yaml             # Deployment + Service
│   ├── frontend.yaml            # Deployment + NodePort Service
│   └── ingress.yaml             # GKE Ingress + ManagedCertificate
├── .github/workflows/           # GitHub Actions CI/CD
├── Dockerfile.backend
├── Dockerfile.frontend
└── docker-compose.yml
```

---

## License

MIT — Built for the AI Agents Hackathon: *Memories That Last*
