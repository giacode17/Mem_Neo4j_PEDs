# RFC-001: CareMyKids — Memory-Powered Pediatric Care Assistant

**Status:** Draft
**Date:** 2026-03-21
**Author:** Portfolio Project
**Context:** AI Agents Hackathon — "Memories That Last"

---

## 1. Overview

CareMyKids is a conversational pediatric care assistant that helps parents manage their children's health. It differentiates itself from generic LLM chatbots by combining two persistent data stores — a vector-based memory layer (MemMachine) and a graph database (Neo4j) — to produce context-aware, personalized, and safety-conscious responses.

The core insight: a parent asking "can I give Emma more Tylenol?" deserves an answer that knows Emma's age, weight, current medications, allergies, and the conversation from last week — not a generic FAQ response.

---

## 2. Problem Statement

Existing AI health chatbots face several compounding problems:

1. **Statelessness** — each conversation starts fresh; the LLM has no memory of prior interactions, child history, or previous symptoms
2. **No structured medical data** — freeform chat cannot reliably track medications, dosing schedules, or drug interactions
3. **Safety gaps** — without access to a child's allergy profile or current medications, the LLM may give dangerous advice
4. **Generic responses** — answers are not personalized to the specific child's age, weight, or medical context

CareMyKids addresses all four by pairing episodic/profile memory with a typed knowledge graph.

---

## 3. Goals

- Maintain a persistent, per-child health record across all conversations
- Detect and warn about medication allergies and drug-drug interactions at query time
- Identify emergency situations from symptom severity data and escalate immediately
- Provide context-aware responses grounded in actual child data, not LLM assumptions
- Support multiple child profiles per user

### Non-Goals

- Clinical diagnosis or prescription generation
- Integration with EHR/EMR systems or insurance providers
- Real-time pharmacy inventory or scheduling with external calendar systems

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│  - Chat interface                                    │
│  - Persona selection (named users)                   │
│  - Compare mode (persona vs. control)                │
│  - Model selector (OpenAI / Anthropic)               │
└──────────────────────────┬──────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────┐
│              Health Server  (FastAPI)                │
│  POST /memory          — ingest episode              │
│  GET  /memory          — retrieve + format query     │
│  POST /memory/store-and-search — combined flow       │
└──────────┬────────────────────────┬─────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────┐     ┌──────────────────────────┐
│   MemMachine     │     │         Neo4j             │
│  (episodic +     │     │  (knowledge graph)        │
│   profile memory)│     │                          │
│                  │     │  Child ──TAKES──► Medication│
│  - Conversation  │     │  Child ──HAS_SYMPTOM──►   │
│    history       │     │    Symptom               │
│  - User profile  │     │  Child ──SCHEDULED_FOR──► │
│  - Preferences   │     │    Appointment           │
└──────────────────┘     │  Medication ──INTERACTS── │
                         │    ──WITH──► Medication   │
                         └──────────────────────────┘
                                    │
                    Both sources fed into
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  PediatricQueryConstructor │
                    │  (builds structured prompt)│
                    └───────────┬───────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │         LLM               │
                    │  (OpenAI or Anthropic)    │
                    └───────────────────────────┘
```

---

## 5. Key Components

### 5.1 Neo4j Knowledge Graph (`neo4j_client.py`)

Manages all structured pediatric data as a typed property graph.

**Node types:**

| Node | Key Properties |
|------|---------------|
| `Child` | `child_id`, `name`, `age`, `weight_kg`, `allergies[]` |
| `Medication` | `name`, `dosage`, `frequency` |
| `Symptom` | `name` |
| `Appointment` | `type`, `date`, `time`, `doctor`, `location`, `status` |
| `Pharmacy` | `name`, `location`, `phone`, `hours` |

**Relationships:**

| Relationship | From → To | Key Properties |
|-------------|-----------|----------------|
| `TAKES` | Child → Medication | `dosage`, `start_date`, `active` |
| `HAS_SYMPTOM` | Child → Symptom | `reported_date`, `severity` (1–10), `notes` |
| `SCHEDULED_FOR` | Child → Appointment | — |
| `INTERACTS_WITH` | Medication ↔ Medication | `severity`, `description` |

**Safety logic at query time:**
- Allergy check: scans `Child.allergies[]` against proposed medication name
- Interaction check: traverses `INTERACTS_WITH` edges between current and proposed medications
- Emergency triage: queries `HAS_SYMPTOM` edges from the last 24 hours; any `severity >= 8` triggers emergency escalation

### 5.2 MemMachine Memory Layer

Provides two memory stores per user:

- **Episodic memory** — timestamped conversation episodes, enabling retrieval of relevant past conversations given the current query
- **Profile memory** — distilled long-term traits about the user (child preferences, parent communication style, recurring concerns)

Accessed via the MemMachine REST API (`/v1/memories`, `/v1/memories/search`).

### 5.3 Query Constructor (`pediatric_query_constructor.py`)

Inherits from `BaseQueryConstructor`. Merges all data sources into a single structured prompt before sending to the LLM:

```
[Current Date]
[Child Profile]          ← from MemMachine profile_memory
[Conversation Context]   ← from MemMachine episodic_memory
[Graph Data]             ← formatted Neo4j data (meds, symptoms, appointments, alerts)
[User Query]
[Role + Safety Instructions]
[Response Format Template]
```

The constructor formats Neo4j data into human-readable sections (child info, active medications, recent symptoms, emergency status, appointments) before injection into the prompt.

### 5.4 Health Server (`health_server.py`)

FastAPI middleware with three endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/memory` | POST | Ingest a new user message into MemMachine |
| `/memory` | GET | Retrieve memory context + format into LLM prompt |
| `/memory/store-and-search` | POST | Ingest and immediately retrieve in one round-trip |

The server wraps the MemMachine client, handles session scoping by `user_id`, and delegates prompt assembly to the query constructor.

### 5.5 Streamlit Frontend (`frontend/app.py`)

Chat UI with features designed for hackathon demonstration:

- **Model selector** — switch between OpenAI and Anthropic models at runtime
- **Persona selection** — named user personas (Charlie, Jing, Charles) or custom name; each gets independent memory
- **Compare mode** — renders persona-personalized response side-by-side with a "Control" (no memory) response to demonstrate memory value
- **Persona rationale** — appends an inline explanation of how the persona influenced the response
- **Profile management** — delete a persona's memory profile

---

## 6. Data Flow

**Typical request:**

```
1. User types message in Streamlit
2. Frontend calls POST /memory/store-and-search with (user_id, query)
3. Health server ingests episode into MemMachine
4. Health server searches MemMachine for relevant episodic + profile memory
5. Health server queries Neo4j for child profile, active medications,
   recent symptoms, upcoming appointments
6. PediatricQueryConstructor assembles structured prompt
7. Formatted prompt returned to frontend
8. Frontend sends prompt to LLM (via llm.py)
9. LLM response displayed in chat
```

---

## 7. Safety Design

Safety is treated as a first-class concern, not an afterthought:

1. **Hard-coded emergency triggers** — the system prompt enumerates specific pediatric emergency conditions (difficulty breathing, infant fever, seizures, severe allergic reaction) and mandates an immediate 911 advisory regardless of other context

2. **Medication safety at query time** — every medication-related query passes through `check_medication_safety()` which runs both allergy and interaction checks against live graph data before the prompt reaches the LLM

3. **Scope boundary** — the system prompt explicitly instructs the LLM that it is not a doctor, cannot diagnose, and must recommend professional care for persistent or uncertain symptoms

4. **Severity threshold** — any symptom logged with severity ≥ 8 within the past 24 hours is surfaced as a `CRITICAL` flag in the graph data section of the prompt

---

## 8. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph DB | Neo4j AuraDB (free tier) | Native relationship traversal for drug interactions and child-medication links; free tier sufficient for hackathon |
| Memory layer | MemMachine | Hackathon theme requirement; provides both episodic and profile memory via a single API |
| Backend | FastAPI | Lightweight, async-capable, minimal boilerplate for a middleware layer |
| Frontend | Streamlit | Rapid UI development; built-in chat primitives; suitable for demo/prototype |
| LLM | Configurable (OpenAI / Anthropic) | Provider-agnostic design; hackathon judges may prefer different models |
| Prompt strategy | Structured template injection | Predictable, auditable prompt structure; easier to debug safety issues than freeform chain-of-thought |

---

## 9. Limitations & Known Issues

1. **No real-time Neo4j sync with health server** — `health_server.py` currently uses the base `HealthAssistantQueryConstructor` (without Neo4j), not the `PediatricCareQueryConstructor`. The pediatric server with full Neo4j integration was marked "Coming Soon" at demo time.

2. **Global singleton graph client** — `get_graph_client()` returns a module-level singleton, which is not safe for concurrent multi-user scenarios

3. **Medication interaction data is sparse** — the knowledge graph is initialized with only two hardcoded interactions (Ibuprofen/Aspirin, Amoxicillin/Warfarin); production use would require a real drug interaction database

4. **Session scoping is user-id only** — a single `user_id` maps to one MemMachine session; multiple children per parent require per-child `user_id` conventions

5. **No authentication** — all API endpoints are unauthenticated; unsuitable for production with real health data

---

## 10. Future Work

- **Full Neo4j + MemMachine integration** in the live server path (connect `PediatricCareQueryConstructor` to `/memory/store-and-search`)
- **Medication database integration** (e.g., RxNorm, OpenFDA) for comprehensive drug interaction data
- **Multi-child support** with a structured `parent_id` → `child_id[]` relationship
- **Appointment reminder notifications** via email/SMS
- **Authentication and data encryption** before any real-world deployment
- **Pediatrician-reviewed safety rules** — replace the LLM-enforced safety guidelines with a deterministic rule engine for critical decisions

---

## 11. Running the System

```bash
# 1. Configure credentials
cp .env.template .env
# Fill in: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, ANTHROPIC_API_KEY / OPENAI_API_KEY

# 2. Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Verify Neo4j connection
python neo4j_client.py

# 4. Start health server
cd health_assistant/
python health_server.py   # runs on :8000

# 5. Start frontend (new terminal)
cd frontend/
streamlit run app.py      # runs on :8501
```

MemMachine backend must be running separately on `MEMORY_BACKEND_URL` (default: `http://localhost:8080`).

---

*Built for the AI Agents Hackathon: "Memories That Last"*
