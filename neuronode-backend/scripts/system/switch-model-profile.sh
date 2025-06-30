#!/bin/bash
# Model Profile Switcher - Bash Wrapper
# Einfaches Umschalten zwischen verschiedenen AI-Modell-Profilen

# Zum Hauptverzeichnis wechseln
cd "$(dirname "$0")/../.."

# Prüfen ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ist nicht installiert oder nicht im PATH"
    exit 1
fi

# Python-Skript ausführen
python3 scripts/system/switch-model-profile.py "$@" 