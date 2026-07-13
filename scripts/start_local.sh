#!/bin/bash
# ==============================================================================
# ARGUS — Local Dev Build and Integrated Start Script
# ==============================================================================
set -e

echo "=== Building React Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Starting Integrated FastAPI Server on http://localhost:8000 ==="
export PYTHONPATH=src
python -m uvicorn argus.api.main:app --host 0.0.0.0 --port 8000 --reload
