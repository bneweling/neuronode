#!/bin/bash
cd "$(dirname "$0")/../.."
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python -m src.cli "$@"
