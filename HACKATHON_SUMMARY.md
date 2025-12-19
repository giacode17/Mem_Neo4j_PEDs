# Hackathon Submission: Pediatric Care Assistant

## Project Overview

**Name:** Pediatric Care Assistant
**Hackathon:** AI Agents Hackathon - Memories That Last
**Category:** Healthcare AI Assistant

## Problem Statement

Parents face critical challenges when caring for sick children:
- **Uncertainty:** When to call the doctor vs. go to ER vs. wait?
- **Medication Safety:** Proper dosing, drug interactions, allergy risks
- **Information Overload:** Hard to remember past symptoms, medications, appointments
- **Stress:** Parents need clear, reliable guidance quickly

## Our Solution

An AI-powered Pediatric Care Assistant that combines:
1. **MemMachine** - Persistent memory of child's medical history and conversations
2. **Neo4j Graph Database** - Structured medical knowledge (medications, symptoms, relationships)
3. **Large Language Models** - Natural language understanding and intelligent responses
4. **Safety-First Design** - Emergency triage, allergy checking, drug interaction detection

## Key Features

### 🚨 Emergency Triage
- Detects critical symptoms requiring immediate medical attention
- Clear guidance: "Call 911", "Go to ER", or "Call doctor"
- Severity assessment based on child's age and symptoms

### 💊 Medication Safety
- Age and weight-based dosing recommendations
- Automatic allergy checking against child's profile
- Drug interaction detection across current medications
- Safety warnings for contraindications

### 🧠 Personalized Memory
- Remembers child's medical history, preferences, past illnesses
- Tracks medication schedules and appointments
- Context-aware responses based on conversation history

### 📊 Graph-Based Knowledge
- Structured medical relationships in Neo4j
- Fast retrieval of relevant medication guides and aftercare procedures
- Symptom-condition mappings with severity thresholds

## Technical Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  (Interactive chat interface with persona selection)         │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Backend Server                      │
│  • Pediatric Query Constructor (Prompt Engineering)          │
│  • Memory Integration (MemMachine connector)                 │
│  • Response Formatting                                       │
└───────────┬──────────────────────────┬───────────────────────┘
            │                          │
            ▼                          ▼
┌─────────────────────┐    ┌──────────────────────────┐
│   Neo4j Graph DB    │    │   MemMachine Backend     │
│                     │    │                          │
│ • Child profiles    │    │ • Episodic memory        │
│ • Medications       │    │ • Profile memory         │
│ • Symptoms          │    │ • Semantic search        │
│ • Aftercare guides  │    │                          │
│ • Appointments      │    │                          │
└─────────────────────┘    └──────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────┐
│                      OpenAI GPT-4o-mini                      │
│  (Natural language understanding and response generation)    │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** FastAPI, Python 3.12
- **Database:** Neo4j Aura (Graph Database)
- **Memory:** MemMachine (Episodic + Profile Memory)
- **LLM:** OpenAI GPT-4o-mini
- **Libraries:** neo4j-driver, openai, requests, pydantic

## Data Model (Neo4j)

### Nodes
- **Child:** name, age, weight_kg, allergies[]
- **Medication:** name, dosage, frequency, warnings
- **Symptom:** name, severity, timestamp
- **Condition:** name, description, risk_level
- **Appointment:** date, time, type, doctor
- **AfterCareGuide:** procedure, instructions

### Relationships
- `(Child)-[:TAKES]->(Medication)`
- `(Child)-[:HAS_SYMPTOM]->(Symptom)`
- `(Symptom)-[:MAY_CAUSE]->(Condition)`
- `(Medication)-[:INTERACTS_WITH]->(Medication)`
- `(Symptom)-[:HAS_RULE]->(SymptomRule)`
- `(Condition)-[:HAS_AFTERCARE]->(AfterCareGuide)`

## Dataset

Located in `dataset/` folder:
- **pediatric_aftercare.jsonl** - 10 post-procedure care guides
- **medication_guides.jsonl** - 3 common pediatric medications
- **symptom_rules.json** - 5 emergency symptom detection rules
- **dialogues.jsonl** - 12 sample parent-assistant conversations
- **synthetic_checkins.csv** - 4 health check-in records

## Innovation Highlights

1. **Multi-Modal Memory Integration**
   - MemMachine for conversational context and user preferences
   - Neo4j graph for structured medical knowledge
   - Seamless integration in query construction

2. **Safety-First Prompt Engineering**
   - Explicit emergency detection rules
   - Medication safety checks before recommendations
   - Clear medical advice boundaries (not a doctor)

3. **Context-Aware Responses**
   - Child's age, weight, allergies automatically considered
   - Recent symptoms and current medications checked
   - Personalized guidance based on medical history

4. **Real-World Applicability**
   - Addresses genuine parental concerns
   - Reduces unnecessary ER visits
   - Helps parents make informed decisions

## Demo Scenarios

### Scenario 1: Fever Management
**Parent:** "My child has a fever of 102°F. When should I call the doctor?"

**Assistant Response:**
- Checks child's age (critical for infants <3 months)
- Reviews current medications and dosing
- Provides age-appropriate fever thresholds
- Recommends when to call doctor vs. monitor at home

### Scenario 2: Medication Safety
**Parent:** "Can I give my child Tylenol and Ibuprofen together?"

**Assistant Response:**
- Checks allergies in child's profile
- Verifies current medications for interactions
- Provides alternating schedule if safe
- Warns about maximum daily doses

### Scenario 3: Emergency Detection
**Parent:** "My child is having trouble breathing and turning blue."

**Assistant Response:**
- 🚨 EMERGENCY: Call 911 immediately
- Explains why this requires immediate attention
- No delay for non-critical information

## Impact & Future Work

### Impact
- Empowers parents with reliable pediatric guidance
- Reduces healthcare anxiety and uncertainty
- Improves medication safety through automation
- Provides 24/7 accessible support

### Future Enhancements
- Voice interface for hands-free use
- Symptom tracking over time with visualizations
- Integration with pediatrician EHR systems
- Multi-language support
- Telemedicine appointment scheduling

## Demo Access

- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **Neo4j Dashboard:** Neo4j Aura Console

## Team

Built for AI Agents Hackathon: Memories That Last

## Resources

- Code Repository: `proj/` folder
- Documentation: `README.md`, `QUICKSTART.md`, `DEMO_GUIDE.md`
- Demo Script: `docs/demo_complete_system.py`
