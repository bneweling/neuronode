#!/bin/bash
# ki-cli.sh - Wrapper für das neue Skript in scripts/cli/

exec "$(dirname "$0")/scripts/cli/ki-cli.sh" "$@"
