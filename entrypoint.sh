#!/bin/bash
set -e

echo "Seeding knowledge base..."
python /app/load_dataset.py

echo "Starting health server..."
exec python health_server.py
