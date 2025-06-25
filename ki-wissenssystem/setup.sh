#!/bin/bash
# setup.sh - Wrapper für das neue Skript in scripts/setup/

exec "$(dirname "$0")/scripts/setup/setup.sh" "$@"
