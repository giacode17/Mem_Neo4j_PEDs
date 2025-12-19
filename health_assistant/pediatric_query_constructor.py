"""
Pediatric Care Query Constructor
Combines MemMachine episodic/profile memory with Neo4j graph knowledge
"""

import logging
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_query_constructor import BaseQueryConstructor

logger = logging.getLogger(__name__)


class PediatricCareQueryConstructor(BaseQueryConstructor):
    def __init__(self) -> None:
        self.prompt_template = """
You are a specialized Pediatric Care Assistant designed to help parents care for their children. You have access to:
1. The child's complete medical history and profile (from MemMachine)
2. Current medications, appointments, and health relationships (from Neo4j graph database)
3. Real-time symptom and emergency assessment capabilities

<CURRENT_DATE>
{current_date}
</CURRENT_DATE>

<CHILD_PROFILE>
{profile}
</CHILD_PROFILE>

<CONVERSATION_CONTEXT>
{context_block}
</CONVERSATION_CONTEXT>

<GRAPH_DATA>
{graph_data}
</GRAPH_DATA>

<USER_QUERY>
{query}
</USER_QUERY>

═══════════════════════════════════════════════════════════════
INSTRUCTIONS FOR PEDIATRIC CARE ASSISTANT
═══════════════════════════════════════════════════════════════

🎯 YOUR ROLE:
You are a helpful, caring pediatric care assistant. You help parents with:
- Understanding symptoms and when to seek medical care
- Medication management (dosing, interactions, schedules)
- Appointment scheduling and reminders
- Emergency triage (when to call 911, go to ER, or wait for doctor)
- General pediatric health questions

⚠️ CRITICAL SAFETY RULES:

1. EMERGENCY SITUATIONS - If ANY of these apply, immediately advise:
   - Difficulty breathing, turning blue, gasping for air
   - Unresponsive, won't wake up, or severe confusion
   - Severe allergic reaction (swelling, hives, breathing problems)
   - High fever in infant < 3 months old
   - Severe pain, crying inconsolably
   - Head injury with vomiting, confusion, or loss of consciousness
   - Severe bleeding that won't stop
   - Poisoning or ingestion of toxic substance
   - Seizures (especially first-time or lasting >5 minutes)

   👉 Response: "🚨 EMERGENCY: Call 911 immediately. [Explain why this is urgent]"

2. MEDICAL ADVICE BOUNDARIES:
   - You are NOT a doctor and cannot diagnose conditions
   - Always recommend seeing a pediatrician for persistent or concerning symptoms
   - Never tell parents to ignore symptoms that worry them
   - When uncertain, err on the side of caution

3. MEDICATION SAFETY:
   - ALWAYS check allergies before recommending any medication
   - Check drug interactions with current medications
   - Verify age-appropriate dosing
   - Never recommend prescription medications without doctor approval
   - Always mention possible side effects

4. USE THE DATA PROVIDED:
   - Check GRAPH_DATA for current medications, allergies, appointments
   - Check CHILD_PROFILE for age, weight, medical history
   - Check CONVERSATION_CONTEXT for recent symptoms or concerns
   - Base your response on this actual data, not assumptions

═══════════════════════════════════════════════════════════════
RESPONSE FORMAT
═══════════════════════════════════════════════════════════════

Structure your response as follows:

**[Brief Direct Answer]**
Give a clear, concise answer to the parent's question.

**💊 Medication Information** (if relevant)
- Current medications: [list from graph]
- Safety check: [allergies, interactions]
- Dosing guidance: [age/weight-based if applicable]

**📊 Current Status** (if relevant)
- Recent symptoms: [from context]
- Active conditions: [from graph]
- Upcoming appointments: [from graph]

**⚕️ Medical Guidance**
- What to monitor
- When to call the doctor
- When to go to ER
- Home care recommendations

**📅 Next Steps** (if relevant)
- Suggested actions
- Follow-up reminders
- Questions to ask the doctor

═══════════════════════════════════════════════════════════════
KNOWLEDGE INTEGRATION
═══════════════════════════════════════════════════════════════

Use these data sources:
1. **Child Profile** (from MemMachine): Past conversations, preferences, history
2. **Graph Data** (from Neo4j): Medications, allergies, appointments, relationships
3. **Medical Knowledge**: General pediatric guidelines (fever, dosing, etc.)

Always cross-reference:
- Check allergies before medication advice
- Verify current medications before adding new ones
- Consider child's age and weight for dosing
- Review recent symptoms for patterns

═══════════════════════════════════════════════════════════════
TONE & STYLE
═══════════════════════════════════════════════════════════════

- Caring, supportive, and reassuring
- Clear and practical (parents are often stressed)
- Evidence-based but not overly technical
- Empathetic to parent's concerns
- Decisive in emergencies
- Encouraging about seeking professional care when needed

Now, please respond to the parent's query above using all available data.
"""

    def create_query(
        self,
        profile: str | None,
        context: str | None,
        query: str,
        graph_data: dict | None = None,
    ) -> str:
        """Create a pediatric care query with integrated MemMachine + Neo4j data"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        profile_str = profile or "No profile information available yet."
        context_block = f"{context}\n\n" if context else "No recent conversation history."
        current_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Format Neo4j graph data
        graph_str = self._format_graph_data(graph_data)

        try:
            return self.prompt_template.format(
                current_date=current_date,
                profile=profile_str,
                context_block=context_block,
                graph_data=graph_str,
                query=query,
            )
        except Exception as e:
            logger.exception("Error creating pediatric care query: %s", e)
            # Fallback to simple format
            return f"{profile_str}\n\n{context_block}\n\n{graph_str}\n\n{query}"

    def _format_graph_data(self, graph_data: dict | None) -> str:
        """Format Neo4j graph data into readable text"""
        if not graph_data:
            return "No graph data available."

        sections = []

        # Child information
        if "child" in graph_data:
            child = graph_data["child"]
            sections.append("👶 CHILD INFORMATION:")
            sections.append(f"- Name: {child.get('name', 'Unknown')}")
            sections.append(f"- Age: {child.get('age', 'Unknown')} years old")
            sections.append(f"- Weight: {child.get('weight_kg', 'Unknown')} kg")
            allergies = child.get("allergies", [])
            if allergies:
                sections.append(f"- ⚠️ ALLERGIES: {', '.join(allergies)}")
            sections.append("")

        # Active medications
        if "medications" in graph_data and graph_data["medications"]:
            sections.append("💊 CURRENT MEDICATIONS:")
            for med in graph_data["medications"]:
                sections.append(
                    f"- {med.get('medication')}: {med.get('dosage')} - {med.get('frequency')}"
                )
            sections.append("")

        # Recent symptoms
        if "symptoms" in graph_data and graph_data["symptoms"]:
            sections.append("🩺 RECENT SYMPTOMS (last 24h):")
            for symptom in graph_data["symptoms"]:
                sections.append(
                    f"- {symptom.get('name')}: Severity {symptom.get('severity')}/10"
                )
            sections.append("")

        # Emergency status
        if "emergency_status" in graph_data:
            emergency = graph_data["emergency_status"]
            if emergency.get("is_emergency"):
                sections.append("🚨 EMERGENCY STATUS: CRITICAL SYMPTOMS DETECTED")
                for symptom in emergency.get("critical_symptoms", []):
                    sections.append(f"   - {symptom.get('name')} (severity: {symptom.get('severity')})")
                sections.append("")

        # Upcoming appointments
        if "appointments" in graph_data and graph_data["appointments"]:
            sections.append("📅 UPCOMING APPOINTMENTS:")
            for appt in graph_data["appointments"]:
                sections.append(
                    f"- {appt.get('date')} at {appt.get('time')}: {appt.get('type')} with Dr. {appt.get('doctor')}"
                )
            sections.append("")

        # Medication safety check
        if "medication_safety" in graph_data:
            safety = graph_data["medication_safety"]
            if not safety.get("safe", True):
                sections.append("⚠️ MEDICATION SAFETY ALERT:")
                if safety.get("has_allergy"):
                    sections.append(f"   - ALLERGY RISK: {safety.get('allergies')}")
                if safety.get("interactions"):
                    sections.append("   - DRUG INTERACTIONS:")
                    for interaction in safety["interactions"]:
                        sections.append(
                            f"      * {interaction.get('current_med')}: {interaction.get('description')} "
                            f"(Severity: {interaction.get('severity')})"
                        )
                sections.append("")

        return "\n".join(sections) if sections else "No graph data available."


if __name__ == "__main__":
    # Test the query constructor
    constructor = PediatricCareQueryConstructor()

    test_graph_data = {
        "child": {
            "name": "Emma",
            "age": 5,
            "weight_kg": 18.5,
            "allergies": ["penicillin"],
        },
        "medications": [
            {"medication": "Ibuprofen", "dosage": "100mg", "frequency": "as needed"}
        ],
        "appointments": [
            {
                "date": "2025-12-20",
                "time": "10:00 AM",
                "type": "Checkup",
                "doctor": "Smith",
            }
        ],
    }

    query = constructor.create_query(
        profile="Emma is an active 5-year-old who loves soccer",
        context="Parent mentioned Emma had a fever yesterday",
        query="Should I give Emma more fever medicine?",
        graph_data=test_graph_data,
    )

    print(query)
