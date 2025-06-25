#!/bin/bash
# dev-mode.sh - Wrapper für das neue Skript in scripts/dev/

exec "$(dirname "$0")/scripts/dev/dev-mode.sh" "$@"
