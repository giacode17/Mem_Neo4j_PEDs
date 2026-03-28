"""
Load the contents of proj/dataset/ into PostgreSQL.

Tables populated:
  knowledge_base  — pediatric_aftercare.jsonl, medication_guides.jsonl, dialogues.jsonl
  symptom_rules   — symptom_rules.json
  checkins        — synthetic_checkins.csv

Run once (idempotent — skips rows that already exist by doc_id / symptom / patient+date).

Usage:
    conda activate caremykids
    cd proj/
    python load_dataset.py
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
import memory_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DATASET_DIR = Path(__file__).parent / "dataset"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _embed(text: str) -> list[float]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def _upsert_knowledge(conn, doc_id: str, source: str, title: str, content: str, metadata: dict):
    """Insert only if doc_id doesn't already exist."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM knowledge_base WHERE doc_id = %s", (doc_id,))
        if cur.fetchone():
            logger.info("  skip (exists): %s", doc_id)
            return
    embedding = _embed(content)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO knowledge_base (doc_id, source, title, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s::vector, %s)
        """, (doc_id, source, title, content, embedding, json.dumps(metadata)))
    conn.commit()
    logger.info("  loaded: %s", doc_id)


def load_aftercare(conn):
    path = DATASET_DIR / "pediatric_aftercare.jsonl"
    logger.info("Loading aftercare records from %s", path)
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            doc_id = rec["id"]
            title = rec.get("title", "")
            # Combine all fields into a single searchable text blob
            parts = [title]
            if rec.get("normal_symptoms"):
                parts.append("Normal symptoms: " + "; ".join(rec["normal_symptoms"]))
            if rec.get("care_tips"):
                parts.append("Care tips: " + "; ".join(rec["care_tips"]))
            if rec.get("red_flags"):
                parts.append("Red flags: " + "; ".join(rec["red_flags"]))
            content = "\n".join(parts)
            metadata = {
                "condition": rec.get("condition"),
                "age_range": rec.get("age_range"),
                "audience": rec.get("audience"),
            }
            _upsert_knowledge(conn, doc_id, "aftercare", title, content, metadata)


def load_medication_guides(conn):
    path = DATASET_DIR / "medication_guides.jsonl"
    logger.info("Loading medication guides from %s", path)
    with open(path) as f:
        for i, line in enumerate(f):
            rec = json.loads(line)
            drug = rec.get("drug", f"drug_{i}")
            doc_id = f"med_{drug.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
            title = drug
            content = (
                f"{drug}\n"
                f"Use: {rec.get('use', '')}\n"
                f"Safety: {rec.get('safety', '')}\n"
                f"Notes: {rec.get('notes', '')}\n"
                f"Storage: {rec.get('storage', '')}"
            )
            metadata = {"forms": rec.get("forms", [])}
            _upsert_knowledge(conn, doc_id, "med_guide", title, content, metadata)


def load_dialogues(conn):
    path = DATASET_DIR / "dialogues.jsonl"
    logger.info("Loading dialogues from %s", path)
    with open(path) as f:
        for i, line in enumerate(f):
            rec = json.loads(line)
            doc_id = f"dlg_{i:03d}"
            query = rec.get("query", "")
            answer = rec.get("expected_answer", "")
            content = f"Q: {query}\nA: {answer}"
            _upsert_knowledge(conn, doc_id, "dialogue", query[:80], content, {})


def load_symptom_rules(conn):
    path = DATASET_DIR / "symptom_rules.json"
    logger.info("Loading symptom rules from %s", path)
    with open(path) as f:
        rules = json.load(f)
    with conn.cursor() as cur:
        for rule in rules:
            symptom = rule["symptom"]
            cur.execute("SELECT id FROM symptom_rules WHERE symptom = %s", (symptom,))
            if cur.fetchone():
                logger.info("  skip (exists): %s", symptom)
                continue
            cur.execute(
                "INSERT INTO symptom_rules (symptom, rule) VALUES (%s, %s)",
                (symptom, json.dumps(rule)),
            )
            logger.info("  loaded: %s", symptom)
    conn.commit()


def load_checkins(conn):
    path = DATASET_DIR / "synthetic_checkins.csv"
    logger.info("Loading checkins from %s", path)
    with open(path) as f:
        reader = csv.DictReader(f)
        with conn.cursor() as cur:
            for row in reader:
                cur.execute("""
                    SELECT id FROM checkins
                    WHERE patient_id = %s AND checkin_date = %s
                """, (row["patient_id"], row["date"]))
                if cur.fetchone():
                    logger.info("  skip (exists): %s %s", row["patient_id"], row["date"])
                    continue
                cur.execute("""
                    INSERT INTO checkins
                        (patient_id, checkin_date, fever_c, pain_0_10,
                         vomiting_events_6h, breathing_difficulty,
                         missed_med_doses_24h, alert_triggered)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row["patient_id"],
                    row["date"],
                    float(row["fever_c"]) if row["fever_c"] else None,
                    int(row["pain_0_10"]) if row["pain_0_10"] else None,
                    int(row["vomiting_events_6h"]) if row["vomiting_events_6h"] else None,
                    row["breathing_difficulty"] == "1",
                    int(row["missed_med_doses_24h"]) if row["missed_med_doses_24h"] else None,
                    row["alert_triggered"] == "1",
                ))
                logger.info("  loaded: %s %s", row["patient_id"], row["date"])
    conn.commit()


if __name__ == "__main__":
    logger.info("Initializing database tables...")
    memory_store.init_db()

    # Get a raw connection for the loaders (they manage their own commits)
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://localhost/caremykids"))

    try:
        load_aftercare(conn)
        load_medication_guides(conn)
        load_dialogues(conn)
        load_symptom_rules(conn)
        load_checkins(conn)
    finally:
        conn.close()

    logger.info("Done. Verifying row counts...")
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://localhost/caremykids"))
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for table in ("knowledge_base", "symptom_rules", "checkins"):
            cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
            n = cur.fetchone()["n"]
            logger.info("  %-20s %d rows", table, n)
    conn.close()
