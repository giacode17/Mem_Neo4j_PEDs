"""
Neo4j Client for Pediatric Care Assistant
Handles all graph database operations for tracking children's health data,
medications, appointments, and emergency situations.
"""

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

logger = logging.getLogger(__name__)


class PediatricCareGraph:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "neo4j+s://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")

        if not password:
            logger.warning("NEO4J_PASSWORD not set in environment variables")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()

    def verify_connection(self) -> bool:
        """Test the Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False

    # ============================================
    # Child Profile Management
    # ============================================

    def create_or_update_child(
        self,
        child_id: str,
        name: str,
        age: int,
        weight_kg: float,
        allergies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a child's profile"""
        query = """
        MERGE (c:Child {child_id: $child_id})
        SET c.name = $name,
            c.age = $age,
            c.weight_kg = $weight_kg,
            c.allergies = $allergies,
            c.updated_at = datetime()
        RETURN c
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                child_id=child_id,
                name=name,
                age=age,
                weight_kg=weight_kg,
                allergies=allergies or [],
            )
            return dict(result.single()["c"])

    def get_child_profile(self, child_id: str) -> dict[str, Any] | None:
        """Retrieve a child's complete profile"""
        query = """
        MATCH (c:Child {child_id: $child_id})
        RETURN c
        """
        with self.driver.session() as session:
            result = session.run(query, child_id=child_id)
            record = result.single()
            return dict(record["c"]) if record else None

    # ============================================
    # Medication Management
    # ============================================

    def add_medication(
        self,
        child_id: str,
        medication_name: str,
        dosage: str,
        frequency: str,
        start_date: str | None = None,
        pharmacy_name: str | None = None,
    ) -> dict[str, Any]:
        """Add a medication for a child"""
        query = """
        MATCH (c:Child {child_id: $child_id})
        MERGE (m:Medication {name: $medication_name})
        SET m.dosage = $dosage, m.frequency = $frequency
        MERGE (c)-[t:TAKES {
            start_date: $start_date,
            dosage: $dosage,
            active: true
        }]->(m)
        RETURN c, m, t
        """
        start = start_date or datetime.now().isoformat()

        with self.driver.session() as session:
            result = session.run(
                query,
                child_id=child_id,
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                start_date=start,
            )
            record = result.single()
            return {
                "child": dict(record["c"]),
                "medication": dict(record["m"]),
                "relationship": dict(record["t"]),
            }

    def check_medication_safety(
        self, child_id: str, medication_name: str
    ) -> dict[str, Any]:
        """Check if medication is safe for child (allergies + interactions)"""
        # Check allergies
        allergy_query = """
        MATCH (c:Child {child_id: $child_id})
        WHERE any(allergy IN c.allergies WHERE toLower($medication_name) CONTAINS toLower(allergy))
        RETURN c.allergies as allergies, true as has_allergy
        """

        # Check interactions with current medications
        interaction_query = """
        MATCH (c:Child {child_id: $child_id})-[:TAKES]->(current:Medication)
        MATCH (new:Medication {name: $medication_name})
        MATCH (current)-[i:INTERACTS_WITH]-(new)
        RETURN current.name as current_med, i.severity as severity, i.description as description
        """

        with self.driver.session() as session:
            # Check allergies
            allergy_result = session.run(
                allergy_query, child_id=child_id, medication_name=medication_name
            )
            allergy_record = allergy_result.single()

            # Check interactions
            interaction_result = session.run(
                interaction_query, child_id=child_id, medication_name=medication_name
            )
            interactions = [dict(record) for record in interaction_result]

            return {
                "safe": not allergy_record and len(interactions) == 0,
                "has_allergy": bool(allergy_record),
                "allergies": allergy_record["allergies"] if allergy_record else [],
                "interactions": interactions,
            }

    def get_active_medications(self, child_id: str) -> list[dict[str, Any]]:
        """Get all active medications for a child"""
        query = """
        MATCH (c:Child {child_id: $child_id})-[t:TAKES]->(m:Medication)
        WHERE t.active = true
        RETURN m.name as medication, t.dosage as dosage, t.frequency as frequency, t.start_date as start_date
        ORDER BY t.start_date DESC
        """
        with self.driver.session() as session:
            result = session.run(query, child_id=child_id)
            return [dict(record) for record in result]

    # ============================================
    # Symptom & Condition Tracking
    # ============================================

    def log_symptom(
        self, child_id: str, symptom_name: str, severity: int, notes: str = ""
    ) -> dict[str, Any]:
        """Log a symptom for a child (severity: 1-10)"""
        query = """
        MATCH (c:Child {child_id: $child_id})
        MERGE (s:Symptom {name: $symptom_name})
        CREATE (c)-[h:HAS_SYMPTOM {
            reported_date: datetime(),
            severity: $severity,
            notes: $notes
        }]->(s)
        RETURN c, s, h
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                child_id=child_id,
                symptom_name=symptom_name,
                severity=severity,
                notes=notes,
            )
            record = result.single()
            return {
                "child": dict(record["c"]),
                "symptom": dict(record["s"]),
                "relationship": dict(record["h"]),
            }

    def check_emergency_status(self, child_id: str) -> dict[str, Any]:
        """Check if current symptoms indicate an emergency"""
        query = """
        MATCH (c:Child {child_id: $child_id})-[h:HAS_SYMPTOM]->(s:Symptom)
        WHERE h.reported_date > datetime() - duration('PT24H')
        WITH c, collect({name: s.name, severity: h.severity}) as recent_symptoms

        // Check for high severity symptoms
        WITH c, recent_symptoms,
             [sx IN recent_symptoms WHERE sx.severity >= 8] as critical_symptoms

        RETURN
            size(critical_symptoms) > 0 as is_emergency,
            critical_symptoms,
            recent_symptoms
        """
        with self.driver.session() as session:
            result = session.run(query, child_id=child_id)
            record = result.single()
            if not record:
                return {"is_emergency": False, "critical_symptoms": [], "recent_symptoms": []}
            return dict(record)

    # ============================================
    # Appointment Scheduling
    # ============================================

    def create_appointment(
        self,
        child_id: str,
        appointment_type: str,
        date: str,
        time: str,
        doctor: str,
        location: str,
        notes: str = "",
    ) -> dict[str, Any]:
        """Schedule an appointment for a child"""
        query = """
        MATCH (c:Child {child_id: $child_id})
        CREATE (a:Appointment {
            type: $appointment_type,
            date: $date,
            time: $time,
            doctor: $doctor,
            location: $location,
            notes: $notes,
            created_at: datetime(),
            status: 'scheduled'
        })
        CREATE (c)-[:SCHEDULED_FOR]->(a)
        RETURN c, a
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                child_id=child_id,
                appointment_type=appointment_type,
                date=date,
                time=time,
                doctor=doctor,
                location=location,
                notes=notes,
            )
            record = result.single()
            return {"child": dict(record["c"]), "appointment": dict(record["a"])}

    def get_upcoming_appointments(
        self, child_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get upcoming appointments for a child"""
        query = """
        MATCH (c:Child {child_id: $child_id})-[:SCHEDULED_FOR]->(a:Appointment)
        WHERE a.date >= date()
        RETURN a
        ORDER BY a.date, a.time
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, child_id=child_id, limit=limit)
            return [dict(record["a"]) for record in result]

    # ============================================
    # Pharmacy Management
    # ============================================

    def add_pharmacy(
        self, name: str, location: str, phone: str, hours: str
    ) -> dict[str, Any]:
        """Add a pharmacy to the system"""
        query = """
        MERGE (p:Pharmacy {name: $name})
        SET p.location = $location,
            p.phone = $phone,
            p.hours = $hours
        RETURN p
        """
        with self.driver.session() as session:
            result = session.run(
                query, name=name, location=location, phone=phone, hours=hours
            )
            return dict(result.single()["p"])

    def find_nearby_pharmacies(self, location: str | None = None) -> list[dict[str, Any]]:
        """Find pharmacies (optionally filter by location)"""
        if location:
            query = """
            MATCH (p:Pharmacy)
            WHERE toLower(p.location) CONTAINS toLower($location)
            RETURN p
            """
            with self.driver.session() as session:
                result = session.run(query, location=location)
                return [dict(record["p"]) for record in result]
        else:
            query = """
            MATCH (p:Pharmacy)
            RETURN p
            LIMIT 10
            """
            with self.driver.session() as session:
                result = session.run(query)
                return [dict(record["p"]) for record in result]

    # ============================================
    # Utility Functions
    # ============================================

    def initialize_knowledge_graph(self):
        """Initialize the graph with common medical knowledge"""
        # Add common medication interactions
        interactions = [
            ("Ibuprofen", "Aspirin", "moderate", "Increased bleeding risk"),
            ("Amoxicillin", "Warfarin", "high", "May increase bleeding"),
        ]

        query = """
        UNWIND $interactions as interaction
        MERGE (m1:Medication {name: interaction[0]})
        MERGE (m2:Medication {name: interaction[1]})
        MERGE (m1)-[:INTERACTS_WITH {
            severity: interaction[2],
            description: interaction[3]
        }]->(m2)
        """

        with self.driver.session() as session:
            session.run(query, interactions=interactions)
            logger.info("Knowledge graph initialized with common interactions")


# Global instance
_graph_client = None


def get_graph_client() -> PediatricCareGraph:
    """Get or create the global graph client instance"""
    global _graph_client
    if _graph_client is None:
        _graph_client = PediatricCareGraph()
    return _graph_client


if __name__ == "__main__":
    # Test the connection
    logging.basicConfig(level=logging.INFO)
    client = PediatricCareGraph()

    if client.verify_connection():
        print("✅ Successfully connected to Neo4j!")
        client.initialize_knowledge_graph()
        print("✅ Knowledge graph initialized!")
    else:
        print("❌ Failed to connect to Neo4j. Check your credentials in .env file")

    client.close()
