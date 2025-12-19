# Quick Start Guide

Get your Pediatric Care Assistant up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Neo4j Aura cloud instance (free tier)
- OpenAI API key

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the template and add your credentials:

```bash
cp docs/.env.template .env
```

Edit `.env` with your credentials:
```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=sk-your-api-key
```

### 3. Load Dataset into Neo4j

```bash
python load_dataset_to_neo4j.py
```

Expected output:
```
✅ Loaded 10 aftercare procedures
✅ Loaded 3 medication guides
✅ Loaded 5 symptom rules
✅ Loaded 12 sample dialogues
✅ Loaded 4 check-in records
```

### 4. Test the Setup

```bash
python test_setup.py
```

You should see: `✅ Neo4j connection successful!`

### 5. Start the Backend Server

```bash
cd health_assistant
python health_server.py
```

Server runs on: `http://localhost:8000`

### 6. Start the Streamlit Frontend

In a new terminal:

```bash
cd frontend
python -m streamlit run app.py
```

Frontend runs on: `http://localhost:8501`

## Using the App

1. Open your browser to `http://localhost:8501`
2. Select a persona (Charlie, Jing, Charles, or create your own)
3. Choose "Skip Rewrite" if MemMachine backend is not running
4. Start chatting with pediatric health questions!

## Demo Queries to Try

- "My child has a fever of 102°F. When should I call the doctor?"
- "Can I give my 5-year-old ibuprofen?"
- "What are the signs of an emergency?"
- "How should I care for my child after a tonsillectomy?"

## Troubleshooting

**Connection refused on port 8080?**
- Enable "Skip Rewrite" checkbox in sidebar (MemMachine not required for demo)

**Neo4j authentication failed?**
- Check your password in `.env` file
- Verify credentials in Neo4j Aura console

**Module not found errors?**
- Make sure you're using the correct Python environment
- Run: `pip install -r requirements.txt`

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌──────────┐
│  Streamlit  │─────▶│  Health Server   │─────▶│  Neo4j   │
│  Frontend   │      │   (FastAPI)      │      │  Graph   │
└─────────────┘      └──────────────────┘      └──────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  OpenAI  │
                        │  GPT-4   │
                        └──────────┘
```

## Next Steps

- Check out `DEMO_GUIDE.md` for presentation tips
- Review `HACKATHON_SUMMARY.md` for project overview
- Explore `docs/demo_complete_system.py` for code examples

---

**Need help?** Check the README.md for detailed documentation.
