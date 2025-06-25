#!/bin/bash
# KI-Wissenssystem Model Profile Switcher - Main Wrapper
# Einfaches Umschalten zwischen verschiedenen AI-Modell-Profilen mit automatischem Restart

set -e

# Zum Hauptverzeichnis wechseln
cd "$(dirname "$0")"

# Farben für bessere Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktion für farbige Ausgabe
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    print_colored $RED "❌ Python3 ist nicht installiert oder nicht im PATH"
    exit 1
fi

# Prüfe ob psutil verfügbar ist
if ! python3 -c "import psutil" &> /dev/null; then
    print_colored $YELLOW "⚠️  psutil Modul nicht gefunden - installiere es..."
    pip3 install psutil
fi

# Hilfe anzeigen wenn keine Parameter
if [ $# -eq 0 ]; then
    print_colored $BLUE "🎛️  KI-Wissenssystem Model Profile Switcher"
    echo
    print_colored $GREEN "Verwendung:"
    echo "  $0 [PROFIL] [OPTIONEN]"
    echo
    print_colored $GREEN "Profile:"
    echo "  premium        - Neueste Top-Modelle (OpenAI + Anthropic + Google)"
    echo "  balanced       - Ausgewogene Performance und Kosten"
    echo "  cost_effective - Kostenoptimiert"
    echo "  gemini_only    - Nur Google Gemini Modelle"
    echo "  openai_only    - Nur OpenAI Modelle"
    echo
    print_colored $GREEN "Optionen:"
    echo "  --show, -s     - Aktuelles Profil anzeigen"
    echo "  --list, -l     - Alle Profile auflisten"
    echo "  --restart, -r  - Automatischen Restart durchführen"
    echo "  --fg           - Im Vordergrund starten"
    echo "  --stop         - System stoppen"
    echo "  --start        - System starten"
    echo "  --interactive  - Interaktiver Modus"
    echo
    print_colored $GREEN "Beispiele:"
    echo "  $0 --show                 # Aktuelles Profil anzeigen"
    echo "  $0 gemini_only --restart  # Zu Gemini wechseln mit Restart"
    echo "  $0 --restart              # Nur System neustarten"
    echo "  $0 --interactive          # Interaktiver Modus"
    echo
fi

# Das eigentliche Python-Skript ausführen
print_colored $BLUE "🔄 Führe Modell-Profil-Wechsel aus..."
python3 scripts/system/switch-model-profile.py "$@"

# Exit-Code weiterleiten
exit_code=$?

if [ $exit_code -eq 0 ]; then
    print_colored $GREEN "✅ Vorgang erfolgreich abgeschlossen!"
else
    print_colored $RED "❌ Fehler beim Ausführen (Exit-Code: $exit_code)"
fi

exit $exit_code 