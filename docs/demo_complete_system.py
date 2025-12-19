"""
Complete System Demo - Pediatric Care Assistant

This demonstrates the full integration:
1. Neo4j graph database (medical knowledge)
2. MemMachine (conversation memory) - optional
3. OpenAI LLM (intelligent responses)
"""

import os
from dotenv import load_dotenv
from neo4j_client import get_graph_client
from health_assistant.pediatric_query_constructor import PediatricCareQueryConstructor

# Load environment variables
load_dotenv()

print("=" * 70)
print("Pediatric Care Assistant - Complete System Demo")
print("=" * 70)
print()

# Initialize components
graph = get_graph_client()
constructor = PediatricCareQueryConstructor()

# Check OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("⚠️  Warning: OPENAI_API_KEY not set in .env")
    print("   The demo will work but won't call the LLM")
    use_llm = False
    client = None
else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        use_llm = True
        print("✅ OpenAI API key configured")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize OpenAI client: {e}")
        print("   The demo will continue without LLM calls")
        use_llm = False
        client = None

print()

# ============================================
# Demo Scenario: Emma with Fever
# ============================================
print("📋 DEMO SCENARIO: Parent asking about child's fever")
print("-" * 70)
print()

# Step 1: Create child profile
print("Step 1: Creating Emma's profile in Neo4j...")
child = graph.create_or_update_child(
    child_id="emma_demo",
    name="Emma",
    age=5,
    weight_kg=18.5,
    allergies=["penicillin", "peanuts"]
)
print(f"✅ Created: {child['name']}, {child['age']} years old")
print(f"   Allergies: {', '.join(child['allergies'])}")
print()

# Step 2: Add current medication
print("Step 2: Adding Emma's current medication...")
med = graph.add_medication(
    child_id="emma_demo",
    medication_name="Ibuprofen",
    dosage="100mg",
    frequency="every 6 hours as needed"
)
print(f"✅ Added: {med['medication']['name']} - {med['medication']['dosage']}")
print()

# Step 3: Log symptom
print("Step 3: Parent reports Emma has a fever...")
symptom = graph.log_symptom(
    child_id="emma_demo",
    symptom_name="fever_c",
    severity=7,  # Moderate severity
    notes="Temperature 38.8°C (101.8°F)"
)
print(f"✅ Logged: Fever with severity 7/10")
print()

# Step 4: Check emergency status
print("Step 4: Checking if this is an emergency...")
emergency = graph.check_emergency_status("emma_demo")
if emergency["is_emergency"]:
    print("🚨 EMERGENCY DETECTED!")
    for s in emergency["critical_symptoms"]:
        print(f"   - {s['name']}: severity {s['severity']}/10")
else:
    print("✅ Not an emergency (severity < 8)")
print()

# Step 5: Get graph data
print("Step 5: Gathering all relevant data from Neo4j...")
graph_data = {
    "child": graph.get_child_profile("emma_demo"),
    "medications": graph.get_active_medications("emma_demo"),
    "emergency_status": emergency
}
print(f"✅ Retrieved:")
print(f"   - Child profile")
print(f"   - {len(graph_data['medications'])} active medication(s)")
print(f"   - Emergency status")
print()

# Step 6: Create intelligent query
print("Step 6: Creating context-aware prompt...")
parent_question = "Emma has had a fever of 101.8°F for the past 3 hours. Can I give her more Ibuprofen?"

formatted_query = constructor.create_query(
    profile="Emma is an active 5-year-old who loves playing soccer. She has seasonal allergies.",
    context="Parent mentioned Emma was playing outside earlier today. Last dose of Ibuprofen was given 4 hours ago.",
    query=parent_question,
    graph_data=graph_data
)

print("✅ Prompt created with:")
print("   - Child's profile from MemMachine (simulated)")
print("   - Conversation context from MemMachine (simulated)")
print("   - Current medications from Neo4j")
print("   - Allergy information from Neo4j")
print("   - Emergency assessment from Neo4j")
print()

# Step 7: Get LLM response
if use_llm:
    print("Step 7: Getting response from OpenAI...")
    print()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": formatted_query}
            ],
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        print("🤖 AI RESPONSE:")
        print("=" * 70)
        print(answer)
        print("=" * 70)
        print()

    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        print()
else:
    print("Step 7: Skipped (no API key)")
    print()
    print("📝 The formatted query would be sent to the LLM:")
    print("-" * 70)
    print(formatted_query[:500] + "...")
    print("-" * 70)
    print()

# ============================================
# Summary
# ============================================
print()
print("=" * 70)
print("✅ Demo Complete!")
print("=" * 70)
print()
print("What just happened:")
print("1. Created child profile in Neo4j graph database")
print("2. Added medication with safety tracking")
print("3. Logged symptom with severity assessment")
print("4. Checked for emergency conditions automatically")
print("5. Retrieved all relevant context from Neo4j")
print("6. Combined with MemMachine memory (simulated)")
print("7. Generated intelligent, context-aware response")
print()
print("🎯 This demonstrates the full power of:")
print("   • Neo4j - for medical relationships & safety checks")
print("   • MemMachine - for conversation & profile memory")
print("   • OpenAI - for intelligent, personalized responses")
print()

# Cleanup
graph.close()
print("✅ Neo4j connection closed")
print()
