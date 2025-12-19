# Demo Guide - Pediatric Care Assistant

Complete guide for presenting your Pediatric Care Assistant at the hackathon.

## Pre-Demo Checklist

### Before You Start
- [ ] Backend server running (`cd health_assistant && python health_server.py`)
- [ ] Frontend running (`cd frontend && python -m streamlit run app.py`)
- [ ] Browser open to `http://localhost:8501`
- [ ] "Skip Rewrite" checkbox enabled (if MemMachine not running)
- [ ] Neo4j Aura connection verified
- [ ] Demo scenarios prepared

### Browser Setup
- [ ] Clear chat history (click "Clear chat" button)
- [ ] Full screen or enlarged window for visibility
- [ ] Zoom browser to 125% for better readability (Cmd/Ctrl + +)

## Demo Script (5 minutes)

### Introduction (30 seconds)

**Say:**
> "I built a Pediatric Care Assistant that helps parents make informed decisions about their child's health. It combines Neo4j graph database for medical knowledge with MemMachine for personalized memory, and uses AI to provide safe, context-aware guidance."

**Show:** Streamlit interface with persona selector

---

### Demo 1: Emergency Triage (60 seconds)

**Setup:**
- Select persona: "Emma" (or custom child name)
- Enable "Skip Rewrite" if needed

**Type:**
```
My 2-year-old is having trouble breathing and making wheezing sounds. Should I call the doctor?
```

**Expected Response:**
- Emergency detection based on "trouble breathing"
- Age-appropriate guidance (2 years old)
- Clear action: Call 911 or go to ER immediately

**Say:**
> "Notice how it immediately recognized this as an emergency and gave clear action steps. The system knows the child's age and considers that in the urgency assessment."

---

### Demo 2: Medication Safety (90 seconds)

**Type:**
```
Can I give my child Tylenol? She weighs 18 kg.
```

**Expected Response:**
- Age/weight-based dosing calculation
- Checks allergies from child profile (if loaded in Neo4j)
- Warnings about maximum daily dose
- Instructions on frequency

**Say:**
> "The assistant pulls the child's weight and allergies from the Neo4j graph database, then calculates safe dosing. It also checks for drug interactions with any current medications."

**Show Neo4j Evidence:**
- Open Neo4j Aura Console (optional)
- Run query: `MATCH (c:Child {name: "Emma"}) RETURN c`
- Show child profile with weight, allergies

---

### Demo 3: Personalized Memory (60 seconds)

**Type (First message):**
```
My daughter Emma had a fever yesterday of 102°F.
```

**Then type (Second message):**
```
Is her fever still concerning?
```

**Expected Response:**
- References previous conversation about fever
- Contextual response based on "yesterday"
- Personalized using child's name

**Say:**
> "This demonstrates the memory integration. The system remembers Emma's fever from the previous message and provides context-aware follow-up advice."

---

### Demo 4: Knowledge Graph Integration (60 seconds)

**Type:**
```
My child just had a tonsillectomy. What should I do for aftercare?
```

**Expected Response:**
- Retrieves tonsillectomy aftercare guide from Neo4j
- Specific instructions (soft foods, pain management, signs of complications)
- When to call doctor

**Say:**
> "This pulls structured medical knowledge from the Neo4j graph database. We loaded pediatric aftercare guides, medication information, and symptom rules. The graph structure allows fast retrieval of relevant medical knowledge."

**Show Architecture Diagram** (if presenting slides):
```
Frontend → Backend → Neo4j Graph + MemMachine → OpenAI LLM
```

---

### Demo 5: Safety Boundaries (30 seconds)

**Type:**
```
Can you diagnose what's wrong with my child?
```

**Expected Response:**
- Politely declines to diagnose
- Explains it's not a doctor
- Recommends seeing a pediatrician

**Say:**
> "Safety is critical. The system is designed with clear boundaries - it won't diagnose conditions or replace professional medical advice, but helps parents make informed decisions about when to seek care."

---

## Technical Deep Dive (Optional - if time permits)

### Show the Code

**1. Query Constructor (`health_assistant/pediatric_query_constructor.py`)**
```python
# Show the prompt template with safety rules
# Highlight emergency detection logic
# Point out how graph data is formatted
```

**2. Neo4j Client (`neo4j_client.py`)**
```python
# Show medication safety check function
# Demonstrate graph queries
# Point out relationship modeling
```

**3. Dataset (`dataset/` folder)**
- Show sample aftercare guide
- Display medication guide structure
- Explain symptom rules JSON

### Architecture Highlights

**Multi-Modal Memory:**
- MemMachine: Episodic + Profile memory (conversations, preferences)
- Neo4j: Structured medical knowledge (medications, symptoms, relationships)
- Combined in query construction for context-aware responses

**Safety Features:**
1. Emergency detection with critical symptom list
2. Allergy checking before medication recommendations
3. Drug interaction detection
4. Age/weight-based dosing calculations
5. Clear medical advice boundaries

## Q&A Preparation

### Expected Questions & Answers

**Q: How does it detect emergencies?**
A: We have explicit rules in the prompt checking for critical symptoms like difficulty breathing, severe bleeding, or loss of consciousness. If detected, it immediately advises calling 911.

**Q: How accurate is the medical information?**
A: The structured knowledge in Neo4j comes from reliable pediatric sources. The LLM provides natural language understanding, but all medical facts are grounded in the graph database. The system is designed to assist, not replace, professional medical advice.

**Q: What happens if MemMachine isn't running?**
A: The app has a "Skip Rewrite" mode that works with just Neo4j and OpenAI. MemMachine adds personalization, but the core functionality works independently.

**Q: Can it handle multiple children in one family?**
A: Yes! Each child gets their own profile in Neo4j with separate medication lists, appointments, and health history. Parents can switch between personas in the UI.

**Q: What about data privacy?**
A: All data stays in your Neo4j Aura instance and MemMachine backend. No patient data is stored by OpenAI (we don't use fine-tuning). For production, you'd add encryption, access controls, and HIPAA compliance.

**Q: How do you prevent hallucinations?**
A: We use structured data from Neo4j as ground truth, explicit prompt instructions to only use provided context, and clearly defined boundaries (e.g., "don't diagnose" rule). The graph database ensures factual consistency.

## Backup Demos (If something breaks)

### If Streamlit Crashes:
Use `docs/demo_complete_system.py`:
```bash
python docs/demo_complete_system.py
```
Shows the same functionality via command line.

### If Neo4j Connection Fails:
- Show the dataset files in `dataset/` folder
- Explain the data model with a diagram
- Walk through the code showing how graph queries work

### If Everything Fails:
- Show the code architecture
- Walk through `README.md`
- Explain the prompt engineering approach
- Discuss safety features and design decisions

## Presentation Tips

1. **Start with the Problem:** Parents' pain points (fear, uncertainty, medication confusion)
2. **Show Impact:** "Helps reduce unnecessary ER visits" vs. "Uses Neo4j and MemMachine"
3. **Demo Live:** Nothing beats seeing it work in real-time
4. **Emphasize Safety:** Critical for healthcare applications
5. **Tell a Story:** "Imagine you're a parent at 2am..." scenario
6. **Be Honest:** "This is a prototype" - discuss production requirements
7. **Highlight Innovation:** Multi-modal memory integration is unique

## Time Management

**For 3-minute demo:**
- 30s: Introduction
- 90s: Emergency + Medication demos
- 60s: Memory or Knowledge demo (pick one)

**For 5-minute demo:**
- 30s: Introduction
- 3m: All 5 demos (emergency, medication, memory, knowledge, safety)
- 90s: Architecture explanation + Q&A

**For 10-minute demo:**
- 1m: Introduction + Problem statement
- 5m: All 5 demos with detailed explanations
- 2m: Code walkthrough
- 2m: Q&A

## Post-Demo

### What to Share
- GitHub repo link (if public)
- Architecture diagram
- Contact info for follow-up

### Follow-Up Questions to Encourage
- "Would you like to see the Neo4j query performance?"
- "Want to see how the graph schema handles medication interactions?"
- "Interested in the prompt engineering approach?"

## Success Metrics

You'll know your demo went well if:
- ✅ Judges understand the problem you're solving
- ✅ Emergency detection impresses them
- ✅ Graph database integration is clear
- ✅ Safety features are highlighted
- ✅ Questions focus on scaling/production (not "does it work?")

---

## Final Checklist

Before you present:
- [ ] Test all 5 demos once
- [ ] Clear chat history
- [ ] Close unnecessary browser tabs
- [ ] Turn off notifications
- [ ] Have backup plan ready
- [ ] Breathe and smile! 😊

**Good luck with your demo!**
