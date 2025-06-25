#!/bin/bash
# start-all.sh - Wrapper für das neue Skript in scripts/system/

exec "$(dirname "$0")/scripts/system/start-all.sh" "$@" 