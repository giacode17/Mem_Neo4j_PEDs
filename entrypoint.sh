#!/bin/bash
set -e

# Only seed if knowledge_base is empty — skips on every restart after first run
ROW_COUNT=$(python -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM knowledge_base')
print(cur.fetchone()[0])
conn.close()
" 2>/dev/null || echo "0")

if [ "$ROW_COUNT" -eq "0" ]; then
  echo "Knowledge base empty — seeding..."
  python /app/load_dataset.py
else
  echo "Knowledge base already seeded ($ROW_COUNT rows) — skipping."
fi

echo "Starting health server..."
exec python health_server.py
