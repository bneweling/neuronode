#!/bin/bash
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python -m src.cli "$@"
