
Pediatric Agent Sample Dataset
==============================

This bundle provides **synthetic, non‑diagnostic** pediatric content for a Watsonx
RAG pipeline (embeddings → vector DB → LLM). Use for demos and internal testing only.

Folders & Files
---------------
- pediatric_aftercare.jsonl
  Ten short, plain‑language after‑care records (conditions like tonsillectomy, RSV, etc.).
  Chunk per record or further split into ~500‑token chunks before embedding.

- medication_guides.jsonl
  Parent‑facing safety snippets (no dosing). Use for general medicine questions.

- symptom_rules.json
  Conservative, non‑diagnostic thresholds for simple triage wording.

- dialogues.jsonl
  Guardian → AI sample questions with expected safe responses for evaluation,
  prompt‑tuning, or few‑shot examples.

- evaluation_queries.jsonl
  Retrieval test set mapping queries to the after‑care record IDs that should be
  retrieved (Top‑k relevance checks).

- synthetic_checkins.csv
  Optional log to test metrics (e.g., alert rate) with MLflow.

Suggested Ingestion
-------------------
1. Clean/normalize text (lowercase, strip HTML).
2. Chunk into <= 500 tokens with 20–50 token overlap.
3. Generate embeddings via IBM watsonx.ai Embeddings.
4. Upsert into your Vector DB with metadata:
   - source: 'aftercare' | 'med_guide' | 'dialogue'
   - condition, age_range, chunk_id
5. At query time, retrieve Top‑k and compose a prompt to the LLM with:
   - Retrieved chunks
   - Relevant symptom_rules (if numeric inputs are present)
   - System message: non‑diagnostic, guardian‑facing, safety‑first tone.

Disclaimer
----------
This dataset is **synthetic and educational**. It does **not** provide medical advice.
Always direct guardians to their clinician for concerns, emergencies, or specific dosing.
Generated: 2025-10-30
