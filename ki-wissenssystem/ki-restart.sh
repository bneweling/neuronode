#!/bin/bash
# KI-Wissenssystem Quick Restart Script
# Schnelle Restart-Operationen für das KI-Wissenssystem

set -e

# Zum Hauptverzeichnis wechseln
cd "$(dirname "$0")"

# Farben für bessere Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funktion für farbige Ausgabe
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Header
print_colored $CYAN "🚀 KI-Wissenssystem Quick Restart"
print_colored $CYAN "=================================="
echo

# Prüfe Parameter
case "${1:-help}" in
    "stop")
        print_colored $YELLOW "🛑 Stoppe KI-Wissenssystem..."
        python3 scripts/system/switch-model-profile.py --stop
        ;;
    "start")
        print_colored $GREEN "🚀 Starte KI-Wissenssystem..."
        python3 scripts/system/switch-model-profile.py --start
        ;;
    "restart"|"r")
        print_colored $BLUE "🔄 Starte KI-Wissenssystem neu..."
        python3 scripts/system/switch-model-profile.py --restart
        ;;
    "status"|"s")
        print_colored $CYAN "📊 Aktueller Status:"
        python3 scripts/system/switch-model-profile.py --show
        ;;
    "gemini")
        print_colored $GREEN "🤖 Wechsle zu Gemini-Only Profil mit Restart..."
        python3 scripts/system/switch-model-profile.py gemini_only --restart
        ;;
    "openai")
        print_colored $GREEN "🤖 Wechsle zu OpenAI-Only Profil mit Restart..."
        python3 scripts/system/switch-model-profile.py openai_only --restart
        ;;
    "premium")
        print_colored $GREEN "🤖 Wechsle zu Premium Profil mit Restart..."
        python3 scripts/system/switch-model-profile.py premium --restart
        ;;
    "balanced")
        print_colored $GREEN "🤖 Wechsle zu Balanced Profil mit Restart..."
        python3 scripts/system/switch-model-profile.py balanced --restart
        ;;
    "cost")
        print_colored $GREEN "🤖 Wechsle zu Cost-Effective Profil mit Restart..."
        python3 scripts/system/switch-model-profile.py cost_effective --restart
        ;;
    "help"|"-h"|"--help"|*)
        print_colored $BLUE "Verwendung: $0 [KOMMANDO]"
        echo
        print_colored $GREEN "System-Kommandos:"
        echo "  stop       - System stoppen"
        echo "  start      - System starten"
        echo "  restart, r - System neustarten"
        echo "  status, s  - Aktuellen Status anzeigen"
        echo
        print_colored $GREEN "Profil-Wechsel mit Restart:"
        echo "  gemini     - Zu Gemini-Only wechseln"
        echo "  openai     - Zu OpenAI-Only wechseln"
        echo "  premium    - Zu Premium wechseln"
        echo "  balanced   - Zu Balanced wechseln"
        echo "  cost       - Zu Cost-Effective wechseln"
        echo
        print_colored $YELLOW "Beispiele:"
        echo "  $0 restart         # Einfacher Neustart"
        echo "  $0 gemini          # Wechsel zu Gemini + Restart"
        echo "  $0 status          # Status anzeigen"
        echo
        print_colored $CYAN "Für erweiterte Optionen verwende:"
        echo "  ./switch-model-profile.sh --help"
        ;;
esac

echo
print_colored $GREEN "✅ Fertig!" 