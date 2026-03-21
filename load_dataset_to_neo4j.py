"""
Load Pediatric Dataset into Neo4j

This script loads the dataset from the dataset/ folder into your Neo4j graph:
- Medication guides → Medication nodes
- Symptom rules → Symptom + SymptomRule nodes
- Aftercare procedures → Condition + AfterCareGuide nodes
- Dialogues → Sample question-answer pairs for training
"""

import json
import csv
from pathlib import Path
from neo4j_client import get_graph_client

print("=" * 70)
print("Loading Pediatric Dataset into Neo4j")
print("=" * 70)
print()

graph = get_graph_client()

if not graph.verify_connection():
    print("❌ Failed to connect to Neo4j")
    exit(1)

print("✅ Connected to Neo4j\n")

dataset_path = Path(__file__).parent / "dataset"

# ============================================
# 1. Load Medication Guides
# ============================================
print("💊 Loading medication guides...")

med_file = dataset_path / "medication_guides.jsonl"
if med_file.exists():
    count = 0
    with open(med_file, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)

                query = """
                MERGE (m:Medication {name: $drug})
                SET m.forms = $forms,
                    m.use_description = $use,
                    m.safety_info = $safety,
                    m.storage = $storage,
                    m.notes = $notes,
                    m.source = 'dataset'
                """

                with graph.driver.session() as session:
                    session.run(
                        query,
                        drug=data.get("drug"),
                        forms=data.get("forms", []),
                        use=data.get("use", ""),
                        safety=data.get("safety", ""),
                        storage=data.get("storage", ""),
                        notes=data.get("notes", "")
                    )
                count += 1

    print(f"   ✅ Loaded {count} medication guides")
else:
    print(f"   ⚠️  File not found: {med_file}")

# ============================================
# 2. Load Symptom Rules
# ============================================
print("🩺 Loading symptom rules...")

symptom_file = dataset_path / "symptom_rules.json"
if symptom_file.exists():
    with open(symptom_file, "r") as f:
        symptom_rules = json.load(f)

    for rule in symptom_rules:
        symptom_name = rule.get("symptom")

        # Create Symptom node
        symptom_query = """
        MERGE (s:Symptom {name: $symptom_name})
        SET s.source = 'dataset'
        """

        # Create SymptomRule node
        rule_query = """
        MATCH (s:Symptom {name: $symptom_name})
        MERGE (r:SymptomRule {symptom_name: $symptom_name})
        SET r.mild_threshold = $mild_lt,
            r.high_threshold = $high_gte,
            r.spike_threshold = $spike_gte,
            r.threshold_gte = $threshold_gte,
            r.is_boolean = $boolean,
            r.advice_mild = $advice_mild,
            r.advice_high = $advice_high,
            r.advice_spike = $advice_spike,
            r.advice = $advice,
            r.source = 'dataset'
        MERGE (s)-[:HAS_RULE]->(r)
        """

        with graph.driver.session() as session:
            # Create symptom
            session.run(symptom_query, symptom_name=symptom_name)

            # Create rule
            session.run(
                rule_query,
                symptom_name=symptom_name,
                mild_lt=rule.get("mild_lt"),
                high_gte=rule.get("high_gte"),
                spike_gte=rule.get("spike_gte"),
                threshold_gte=rule.get("threshold_gte"),
                boolean=rule.get("boolean"),
                advice_mild=rule.get("advice_mild"),
                advice_high=rule.get("advice_high"),
                advice_spike=rule.get("advice_spike"),
                advice=rule.get("advice")
            )

    print(f"   ✅ Loaded {len(symptom_rules)} symptom rules")
else:
    print(f"   ⚠️  File not found: {symptom_file}")

# ============================================
# 3. Load Pediatric Aftercare
# ============================================
print("📋 Loading aftercare procedures...")

aftercare_file = dataset_path / "pediatric_aftercare.jsonl"
if aftercare_file.exists():
    count = 0
    with open(aftercare_file, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)

                # Create Condition node
                condition_query = """
                MERGE (c:Condition {name: $condition_name})
                SET c.category = $category,
                    c.age_range = $age_range,
                    c.source = 'dataset'
                """

                # Create AfterCareGuide node
                aftercare_query = """
                MATCH (c:Condition {name: $condition_name})
                MERGE (a:AfterCareGuide {condition: $condition_name})
                SET a.overview = $overview,
                    a.pain_management = $pain_mgmt,
                    a.activity_restrictions = $activity,
                    a.diet_instructions = $diet,
                    a.wound_care = $wound_care,
                    a.red_flags = $red_flags,
                    a.follow_up = $follow_up,
                    a.source = 'dataset'
                MERGE (c)-[:HAS_AFTERCARE]->(a)
                """

                with graph.driver.session() as session:
                    # Create condition
                    session.run(
                        condition_query,
                        condition_name=data.get("condition"),
                        category=data.get("category"),
                        age_range=data.get("age_range")
                    )

                    # Create aftercare guide
                    session.run(
                        aftercare_query,
                        condition_name=data.get("condition"),
                        overview=data.get("overview"),
                        pain_mgmt=data.get("pain_management"),
                        activity=data.get("activity"),
                        diet=data.get("diet"),
                        wound_care=data.get("wound_care"),
                        red_flags=data.get("red_flags", []),
                        follow_up=data.get("follow_up")
                    )
                count += 1

    print(f"   ✅ Loaded {count} aftercare procedures")
else:
    print(f"   ⚠️  File not found: {aftercare_file}")

# ============================================
# 4. Load Sample Dialogues
# ============================================
print("💬 Loading sample dialogues...")

dialogue_file = dataset_path / "dialogues.jsonl"
if dialogue_file.exists():
    count = 0
    with open(dialogue_file, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)

                cypher = """
                CREATE (d:SampleDialogue {
                    query: $user_query,
                    expected_answer: $answer,
                    source: 'dataset'
                })
                """

                with graph.driver.session() as session:
                    session.run(
                        cypher,
                        user_query=data.get("query"),
                        answer=data.get("expected_answer")
                    )
                count += 1

    print(f"   ✅ Loaded {count} sample dialogues")
else:
    print(f"   ⚠️  File not found: {dialogue_file}")

# ============================================
# 5. Load Synthetic Check-ins (Optional)
# ============================================
print("📊 Loading synthetic check-ins...")

checkin_file = dataset_path / "synthetic_checkins.csv"
if checkin_file.exists():
    count = 0
    with open(checkin_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cypher = """
            CREATE (c:CheckIn {
                timestamp: $timestamp,
                child_id: $child_id,
                symptom: $symptom,
                severity: $severity,
                action: $action,
                source: 'dataset'
            })
            """

            with graph.driver.session() as session:
                session.run(
                    cypher,
                    timestamp=row.get("timestamp"),
                    child_id=row.get("child_id"),
                    symptom=row.get("symptom"),
                    severity=row.get("severity"),
                    action=row.get("action")
                )
            count += 1

    print(f"   ✅ Loaded {count} check-in records")
else:
    print(f"   ⚠️  File not found: {checkin_file}")

# ============================================
# 6. Create Useful Relationships
# ============================================
print("\n🔗 Creating knowledge graph relationships...")

# Link symptoms mentioned in aftercare to conditions
with graph.driver.session() as session:
    # Link fever symptom to relevant conditions
    session.run("""
        MATCH (s:Symptom {name: 'fever_c'})
        MATCH (c:Condition)
        WHERE c.name CONTAINS 'tonsillectomy'
           OR c.name CONTAINS 'RSV'
           OR c.name CONTAINS 'pneumonia'
        MERGE (c)-[:MAY_CAUSE]->(s)
    """)

    # Link pain to surgical conditions
    session.run("""
        MATCH (s:Symptom {name: 'pain_0_10'})
        MATCH (c:Condition)
        WHERE c.name CONTAINS 'tonsillectomy'
           OR c.name CONTAINS 'appendectomy'
        MERGE (c)-[:MAY_CAUSE]->(s)
    """)

    # Link breathing difficulties to respiratory conditions
    session.run("""
        MATCH (s:Symptom {name: 'breathing_difficulty'})
        MATCH (c:Condition)
        WHERE c.name CONTAINS 'RSV'
           OR c.name CONTAINS 'pneumonia'
           OR c.name CONTAINS 'flu'
        MERGE (c)-[:MAY_CAUSE]->(s)
    """)

print("   ✅ Created symptom-condition relationships")

# ============================================
# Summary
# ============================================
print()
print("=" * 70)
print("✅ Dataset Loading Complete!")
print("=" * 70)
print()

# Count nodes
with graph.driver.session() as session:
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        ORDER BY count DESC
    """)

    print("Node Summary:")
    for record in result:
        print(f"  {record['label']}: {record['count']}")

print()
print("Try these queries in Neo4j Browser:")
print()
print("1. View all medication information:")
print("   MATCH (m:Medication)")
print("   RETURN m.name, m.safety_info, m.forms")
print()
print("2. See symptom rules and advice:")
print("   MATCH (s:Symptom)-[:HAS_RULE]->(r:SymptomRule)")
print("   RETURN s.name, r.advice_high, r.high_threshold")
print()
print("3. View aftercare procedures:")
print("   MATCH (c:Condition)-[:HAS_AFTERCARE]->(a:AfterCareGuide)")
print("   RETURN c.name, a.overview, a.red_flags")
print()
print("4. Find conditions that cause breathing difficulty:")
print("   MATCH (c:Condition)-[:MAY_CAUSE]->(s:Symptom {name: 'breathing_difficulty'})")
print("   RETURN c.name, c.age_range")
print()
print("5. Get sample dialogues for training:")
print("   MATCH (d:SampleDialogue)")
print("   RETURN d.query, d.expected_answer")
print("   LIMIT 5")
print()

graph.close()
