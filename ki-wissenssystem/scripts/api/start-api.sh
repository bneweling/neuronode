#!/bin/bash
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
