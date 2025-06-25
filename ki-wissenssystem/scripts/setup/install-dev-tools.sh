#!/bin/bash
# install-dev-tools.sh - Entwicklungstools installieren

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🛠️ KI-Wissenssystem - Entwicklungstools installieren${NC}"
echo

# Funktionen für farbige Ausgabe
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Prüfe ob Virtual Environment existiert
if [ ! -d "venv" ]; then
    error "Virtual Environment nicht gefunden!"
    echo "Bitte zuerst setup.sh ausführen."
    exit 1
fi

# Virtual Environment aktivieren
info "Aktiviere Virtual Environment..."
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    error "Virtual Environment konnte nicht aktiviert werden!"
    exit 1
fi

success "Virtual Environment aktiviert"

# Entwicklungstools installieren
info "\nInstalliere Entwicklungstools..."
echo "Dies kann einige Minuten dauern..."
echo

if pip install -r requirements-dev.txt; then
    success "Entwicklungstools installiert"
else
    error "Fehler beim Installieren der Entwicklungstools!"
    exit 1
fi

# Verfügbare Tools anzeigen
success "\n=== Entwicklungstools installiert! ==="
echo
info "🧪 Testing:"
echo "  pytest                    # Tests ausführen"
echo "  pytest --cov             # Mit Coverage"
echo "  pytest tests/test_api.py  # Spezifische Tests"
echo
info "🎨 Code Quality:"
echo "  black .                   # Code formatieren"
echo "  isort .                   # Imports sortieren"
echo "  flake8                    # Linting"
echo "  mypy src/                 # Type checking"
echo
info "🐛 Debugging:"
echo "  ipython                   # Bessere REPL"
echo "  jupyter notebook          # Notebooks"
echo "  memory_profiler           # Memory profiling"
echo
info "📊 Performance:"
echo "  locust                    # Load testing"
echo "  line_profiler             # Line profiling"
echo
info "🌐 API Testing:"
echo "  http localhost:8080/docs  # API testen"
echo "  httpie                    # HTTP client"
echo
success "🎉 Bereit für Entwicklung!"
echo
info "💡 Tipp: Verwenden Sie ./dev-mode.sh für Hot Reload" 