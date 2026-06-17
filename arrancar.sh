#!/usr/bin/env bash
set -e
python3 -m venv venv 2>/dev/null || python -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -q -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
