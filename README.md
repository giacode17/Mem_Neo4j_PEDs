# CareMyKids 🏥

**AI Agents Hackathon: Memories That Last**

A memory-powered pediatric care assistant that combines:
- **MemMachine** - Persistent long-term memory for tracking conversations and child history
- **Neo4j** - Graph database for medical relationships (medications, symptoms, appointments)
- **LLMs** - Intelligent reasoning and natural language interaction

## 🎯 What This Does

This assistant helps parents care for their children by:
- ✅ **Medication Management** - Track medications, check interactions, verify safety
- ✅ **Symptom Tracking** - Log symptoms and detect emergency situations
- ✅ **Appointment Scheduling** - Manage doctor appointments and reminders
- ✅ **Emergency Triage** - Assess severity and provide guidance on when to seek help
- ✅ **Memory-Powered Conversations** - Remembers your child's complete history


## 🚀 Video Demo
You can check this demo on Youtube([ Go ](https://www.youtube.com/watch?v=p1g2aGqNopU))


## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │ (Streamlit Chat UI)
│   (User)        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Pediatric Care Server          │ (FastAPI)
│  - Integrates MemMachine + Neo4j│
│  - Constructs context-aware     │
│    queries with graph data      │
└────┬──────────────────────┬─────┘
     │                      │
     ▼                      ▼
┌──────────────┐    ┌──────────────┐
│  MemMachine  │    │    Neo4j     │
│  - Episodic  │    │  - Children  │
│  - Profile   │    │  - Meds      │
│  - Memory    │    │  - Symptoms  │
└──────────────┘    └──────────────┘
```

## Quick Start

### Step 1: Set Up Neo4j (5 minutes)

1. Go to https://neo4j.com/cloud/aura/
2. Create a **free AuraDB** instance
3. **SAVE YOUR CREDENTIALS** when shown:
   - URI: `neo4j+s://xxxxx.databases.neo4j.io`
   - Username: `neo4j`
   - Password: `(generated password)`

### Step 2: Configure Environment

```bash
cd proj/

# Copy the template
cp .env.template .env

# Edit .env and add your credentials
nano .env  # or use your favorite editor
```

Fill in:
- Neo4j credentials from Step 1
- Your OpenAI or Anthropic API key

### Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Test Neo4j Connection

```bash
cd proj/
python neo4j_client.py
```

You should see:
```
✅ Successfully connected to Neo4j!
✅ Knowledge graph initialized!
```

### Step 5: Run the Server

```bash
# Option 1: Run health server (basic)
cd proj/health_assistant/
python health_server.py

# Option 2: Run pediatric server (with Neo4j integration)
# Coming soon - integrate with your own implementation
```

### Step 6: Run the Frontend

```bash
# In a new terminal
cd proj/frontend/
streamlit run app.py
```

Open http://localhost:8501 in your browser!

## 📚 Key Components

### 1. Neo4j Client (`neo4j_client.py`)

Handles all graph database operations:

```python
from neo4j_client import get_graph_client

graph = get_graph_client()

# Create child profile
graph.create_or_update_child(
    child_id="emma_001",
    name="Emma",
    age=5,
    weight_kg=18.5,
    allergies=["penicillin"]
)

# Check medication safety
safety = graph.check_medication_safety("emma_001", "Amoxicillin")
if not safety["safe"]:
    print(f"⚠️ Warning: {safety}")
```

### 2. Query Constructor (`pediatric_query_constructor.py`)

Combines MemMachine memory + Neo4j graph data into intelligent prompts:

```python
from health_assistant.pediatric_query_constructor import PediatricCareQueryConstructor

constructor = PediatricCareQueryConstructor()

# This creates a comprehensive prompt with:
# - Child's profile (from MemMachine)
# - Conversation history (from MemMachine)
# - Current medications, symptoms, appointments (from Neo4j)
query = constructor.create_query(
    profile=profile_memory,
    context=episodic_memory,
    query="Should I give Emma more fever medicine?",
    graph_data=neo4j_data
)
```

### 3. Health Server (`health_server.py`)

FastAPI middleware that orchestrates everything:
- Stores messages in MemMachine
- Queries Neo4j for graph relationships
- Formats context-aware queries for the LLM

## 🧪 Testing with Sample Data

Create a test child and add some data:

```python
from neo4j_client import get_graph_client

graph = get_graph_client()

# Create child
graph.create_or_update_child(
    child_id="test_child",
    name="Test Child",
    age=5,
    weight_kg=20.0,
    allergies=["peanuts"]
)

# Add medication
graph.add_medication(
    child_id="test_child",
    medication_name="Ibuprofen",
    dosage="100mg",
    frequency="every 6 hours as needed"
)

# Log a symptom
graph.log_symptom(
    child_id="test_child",
    symptom_name="fever",
    severity=6,
    notes="Started this morning"
)

# Check emergency status
emergency = graph.check_emergency_status("test_child")
print(emergency)
```

## 📊 Neo4j Graph Schema

**Nodes:**
- `Child` - Child profiles
- `Medication` - Medicines
- `Symptom` - Symptoms
- `Condition` - Medical conditions
- `Appointment` - Doctor appointments
- `Pharmacy` - Pharmacies

**Relationships:**
- `(Child)-[:TAKES]->(Medication)`
- `(Child)-[:HAS_SYMPTOM]->(Symptom)`
- `(Child)-[:SCHEDULED_FOR]->(Appointment)`
- `(Medication)-[:INTERACTS_WITH]->(Medication)`

View in Neo4j Browser:
```cypher
// See all children and their medications
MATCH (c:Child)-[:TAKES]->(m:Medication)
RETURN c, m
```





## 📝 License

MIT License - Built for AI Agents Hackathon


