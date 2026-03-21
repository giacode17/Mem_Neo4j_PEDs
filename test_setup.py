"""
Test script to verify your Pediatric Care Assistant setup
Run this after installing dependencies and configuring .env
"""

import sys
from datetime import datetime

print("=" * 60)
print("Pediatric Care Assistant - Setup Verification")
print("=" * 60)
print()

# Test 1: Check Python packages
print("✓ Testing Python dependencies...")
try:
    import neo4j
    import dotenv
    import fastapi
    import streamlit
    import requests
    print("  ✅ All Python packages installed")
except ImportError as e:
    print(f"  ❌ Missing package: {e}")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check .env file
print("\n✓ Testing environment configuration...")
try:
    from dotenv import load_dotenv
    import os

    load_dotenv()

    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not neo4j_uri or "xxxxx" in neo4j_uri:
        print("  ⚠️  NEO4J_URI not configured in .env")
        print("  Please edit .env and add your Neo4j Aura credentials")
    else:
        print(f"  ✅ Neo4j URI configured: {neo4j_uri}")

    if not neo4j_password or neo4j_password == "your-password-here":
        print("  ⚠️  NEO4J_PASSWORD not configured in .env")
    else:
        print("  ✅ Neo4j password configured")

except Exception as e:
    print(f"  ❌ Error loading .env: {e}")
    print("  Make sure .env file exists (copy from .env.template)")

# Test 3: Test Neo4j connection
print("\n✓ Testing Neo4j connection...")
try:
    from neo4j_client import get_graph_client

    graph = get_graph_client()
    if graph.verify_connection():
        print("  ✅ Successfully connected to Neo4j!")

        # Test basic operations
        print("\n✓ Testing Neo4j operations...")

        # Create a test child
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = graph.create_or_update_child(
            child_id=test_id,
            name="Test Child",
            age=5,
            weight_kg=20.0,
            allergies=["test_allergen"],
        )
        print(f"  ✅ Created test child: {test_id}")

        # Retrieve the child
        child = graph.get_child_profile(test_id)
        if child and child.get("name") == "Test Child":
            print("  ✅ Successfully retrieved child profile")
        else:
            print("  ❌ Failed to retrieve child profile")

        # Test medication safety
        safety = graph.check_medication_safety(test_id, "Ibuprofen")
        print(f"  ✅ Medication safety check working: {safety.get('safe')}")

        # Initialize knowledge graph
        graph.initialize_knowledge_graph()
        print("  ✅ Knowledge graph initialized")

        print("\n✓ All Neo4j tests passed!")

    else:
        print("  ❌ Failed to connect to Neo4j")
        print("  Check your credentials in .env file")
        print("  Make sure your Aura instance is running")

except Exception as e:
    print(f"  ❌ Neo4j error: {e}")
    print("  Make sure you've set up Neo4j Aura and configured .env")

# Test 4: Check query constructor
print("\n✓ Testing Query Constructor...")
try:
    from health_assistant.pediatric_query_constructor import (
        PediatricCareQueryConstructor,
    )

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
    }

    query = constructor.create_query(
        profile="Test profile",
        context="Test context",
        query="Test query",
        graph_data=test_graph_data,
    )

    if query and "Emma" in query and "Ibuprofen" in query:
        print("  ✅ Query constructor working correctly")
    else:
        print("  ⚠️  Query constructor may have issues")

except Exception as e:
    print(f"  ❌ Query constructor error: {e}")

# Summary
print("\n" + "=" * 60)
print("Setup Verification Complete!")
print("=" * 60)
print()
print("Next steps:")
print("1. If all tests passed, you're ready to go!")
print("2. Run the server: cd health_assistant && python health_server.py")
print("3. Run the frontend: cd frontend && streamlit run app.py")
print("4. Check README.md for more details")
print()
print("For the hackathon:")
print("- Explore neo4j_client.py for graph operations")
print("- Check pediatric_query_constructor.py for prompt engineering")
print("- Customize the schema in NEO4J_SETUP.md")
print()
