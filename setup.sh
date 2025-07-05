#!/bin/bash

# =============================================================================
# NEURONODE SETUP SCRIPT
# Modernisiertes Setup für Backend + Frontend Integration
# =============================================================================

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Pfade
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/neuronode-backend"
FRONTEND_DIR="$PROJECT_ROOT/neuronode-webapp"
LOG_FILE="$PROJECT_ROOT/setup.log"

# Banner
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🚀 NEURONODE SETUP                        ║${NC}"
echo -e "${BLUE}║               Enterprise Knowledge System                      ║${NC}"
echo -e "${BLUE}║                Backend + Frontend Integration                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📂 Projekt-Root: $PROJECT_ROOT${NC}"
echo -e "${CYAN}📂 Backend: $BACKEND_DIR${NC}"
echo -e "${CYAN}📂 Frontend: $FRONTEND_DIR${NC}"
echo ""

# Funktionen
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    echo "Siehe $LOG_FILE für Details"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Prüfe Projektstruktur
check_project_structure() {
    echo -e "\n${PURPLE}1. Prüfe Projektstruktur...${NC}"
    
    if [ ! -d "$BACKEND_DIR" ]; then
        handle_error "Backend-Verzeichnis nicht gefunden: $BACKEND_DIR"
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        handle_error "Frontend-Verzeichnis nicht gefunden: $FRONTEND_DIR"
    fi
    
    if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
        handle_error "Backend requirements.txt nicht gefunden"
    fi
    
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        handle_error "Frontend package.json nicht gefunden"
    fi
    
    success "Projektstruktur validiert"
}

# Prüfe Systemvoraussetzungen
check_system_requirements() {
    echo -e "\n${PURPLE}2. Prüfe Systemvoraussetzungen...${NC}"
    
    # Homebrew
    if ! command -v brew &> /dev/null; then
        warning "Homebrew nicht gefunden. Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Homebrew Installation fehlgeschlagen"
    fi
    success "Homebrew verfügbar"
    
    # Python 3.11+
    if ! command -v python3.11 &> /dev/null && ! command -v python3.12 &> /dev/null; then
        warning "Python 3.11+ nicht gefunden. Installiere Python..."
        brew install python@3.11 || handle_error "Python Installation fehlgeschlagen"
    fi
    success "Python 3.11+ verfügbar"
    
    # Node.js 18+
    if ! command -v node &> /dev/null; then
        warning "Node.js nicht gefunden. Installiere Node.js..."
        brew install node || handle_error "Node.js Installation fehlgeschlagen"
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        warning "Node.js Version zu alt (benötigt: 18+, gefunden: $NODE_VERSION)"
        brew upgrade node || handle_error "Node.js Update fehlgeschlagen"
    fi
    success "Node.js 18+ verfügbar"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        warning "Docker nicht gefunden. Bitte Docker Desktop installieren:"
        echo "https://www.docker.com/products/docker-desktop/"
        read -p "Drücken Sie Enter nachdem Docker installiert wurde..."
    fi
    
    if ! docker info &> /dev/null; then
        warning "Docker läuft nicht. Starte Docker Desktop..."
        open -a Docker
        echo "Warte auf Docker..."
        for i in {1..30}; do
            if docker info &> /dev/null; then
                break
            fi
            sleep 2
            echo -n "."
        done
        echo ""
    fi
    success "Docker verfügbar und läuft"
}

# Backend Setup
setup_backend() {
    echo -e "\n${PURPLE}3. Backend Setup...${NC}"
    
    cd "$BACKEND_DIR" || handle_error "Kann nicht in Backend-Verzeichnis wechseln"
    
    # Virtual Environment
    if [ -d "venv" ]; then
        warning "Entferne alte Virtual Environment..."
        rm -rf venv
    fi
    
    info "Erstelle neue Virtual Environment..."
    python3.11 -m venv venv || python3.12 -m venv venv || handle_error "Virtual Environment konnte nicht erstellt werden"
    
    source venv/bin/activate || handle_error "Virtual Environment konnte nicht aktiviert werden"
    
    # Pip upgrade
    pip install --upgrade pip setuptools wheel
    
    # Requirements installieren
    info "Installiere Python-Pakete..."
    pip install -r requirements.txt || handle_error "Python-Pakete konnten nicht installiert werden"
    
    # Environment-Datei
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            warning ".env Datei erstellt. Bitte API-Keys konfigurieren!"
        else
            warning ".env Datei nicht gefunden. Bitte manuell erstellen."
        fi
    fi
    
    success "Backend-Setup abgeschlossen"
    cd "$PROJECT_ROOT"
}

# Frontend Setup
setup_frontend() {
    echo -e "\n${PURPLE}4. Frontend Setup...${NC}"
    
    cd "$FRONTEND_DIR" || handle_error "Kann nicht in Frontend-Verzeichnis wechseln"
    
    # Node modules installieren
    info "Installiere Node.js Dependencies..."
    npm install || handle_error "npm install fehlgeschlagen"
    
    # Playwright installieren
    info "Installiere Playwright Browser..."
    npx playwright install --with-deps || warning "Playwright Installation fehlgeschlagen"
    
    success "Frontend-Setup abgeschlossen"
    cd "$PROJECT_ROOT"
}

# Docker Services Setup
setup_docker_services() {
    echo -e "\n${PURPLE}5. Docker Services Setup...${NC}"
    
    cd "$BACKEND_DIR" || handle_error "Kann nicht in Backend-Verzeichnis wechseln"
    
    # Prüfe docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        handle_error "docker-compose.yml nicht gefunden im Backend-Verzeichnis"
    fi
    
    # Stoppe laufende Services
    docker-compose down 2>/dev/null || true
    
    # Starte Services
    info "Starte Docker Services..."
    docker-compose up -d || handle_error "Docker Services konnten nicht gestartet werden"
    
    # Health Checks
    info "Warte auf Service-Bereitschaft..."
    
    # Neo4j
    echo -n "Neo4j"
    for i in {1..60}; do
        if curl -s http://localhost:7474 > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # ChromaDB
    echo -n "ChromaDB"
    for i in {1..60}; do
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    success "Docker Services gestartet"
    cd "$PROJECT_ROOT"
}

# Datenbankschema initialisieren
initialize_database() {
    echo -e "\n${PURPLE}6. Datenbankschema initialisieren...${NC}"
    
    cd "$BACKEND_DIR" || handle_error "Kann nicht in Backend-Verzeichnis wechseln"
    
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
    
    # Schema-Migration
    if [ -f "scripts/setup/migrate_schema.py" ]; then
        info "Führe Schema-Migration aus..."
        python scripts/setup/migrate_schema.py || warning "Schema-Migration fehlgeschlagen"
    fi
    
    success "Datenbankschema initialisiert"
    cd "$PROJECT_ROOT"
}

# Startskripte erstellen
create_start_scripts() {
    echo -e "\n${PURPLE}7. Erstelle Startskripte...${NC}"
    
    # Hauptstartskript
    cat > start-all.sh << 'EOF'
#!/bin/bash

# =============================================================================
# NEURONODE START SCRIPT
# Startet alle Services: Backend API + Frontend + Docker Services
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/neuronode-backend"
FRONTEND_DIR="$PROJECT_ROOT/neuronode-webapp"

echo -e "${BLUE}🚀 Starte Neuronode Services...${NC}"

# Prüfe Verzeichnisse
if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Projekt-Verzeichnisse nicht gefunden${NC}"
    exit 1
fi

# Stoppe laufende Prozesse
echo -e "${YELLOW}🛑 Stoppe laufende Services...${NC}"
pkill -f "uvicorn src.api.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

# Starte Docker Services
echo -e "${PURPLE}🐳 Starte Docker Services...${NC}"
cd "$BACKEND_DIR"
docker-compose up -d
sleep 5

# Starte Backend API
echo -e "${PURPLE}🔧 Starte Backend API...${NC}"
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!

# Warte auf Backend
echo -e "${YELLOW}⏳ Warte auf Backend-Start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend bereit${NC}"
        break
    fi
    sleep 1
done

# Generiere API-Typen
echo -e "${PURPLE}📝 Generiere API-Typen...${NC}"
cd "$FRONTEND_DIR"
npm run generate:api-types || echo -e "${YELLOW}⚠️ API-Typen Generation fehlgeschlagen${NC}"

# Starte Frontend
echo -e "${PURPLE}🎨 Starte Frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

# Status anzeigen
echo -e "\n${GREEN}🎉 Alle Services gestartet!${NC}"
echo -e "${BLUE}📊 Status:${NC}"
echo -e "  Backend API:  http://localhost:8080"
echo -e "  Frontend:     http://localhost:3000"
echo -e "  API Docs:     http://localhost:8080/docs"
echo -e "  Neo4j:        http://localhost:7474"
echo -e "  ChromaDB:     http://localhost:8000"
echo ""
echo -e "${YELLOW}Drücken Sie Ctrl+C zum Beenden${NC}"

# Warte auf Interrupt
cleanup() {
    echo -e "\n${YELLOW}🛑 Stoppe Services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    cd "$BACKEND_DIR"
    docker-compose down
    echo -e "${GREEN}✅ Services gestoppt${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Warte auf Benutzer-Interrupt
wait
EOF

    chmod +x start-all.sh

    # Backend-Only Startskript
    cat > start-backend.sh << 'EOF'
#!/bin/bash

BACKEND_DIR="$(pwd)/neuronode-backend"
cd "$BACKEND_DIR"

echo "🚀 Starte Backend Services..."

# Docker Services
docker-compose up -d
sleep 5

# Backend API
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
EOF

    chmod +x start-backend.sh

    # Frontend-Only Startskript
    cat > start-frontend.sh << 'EOF'
#!/bin/bash

FRONTEND_DIR="$(pwd)/neuronode-webapp"
cd "$FRONTEND_DIR"

echo "🎨 Starte Frontend..."

# API-Typen generieren (falls Backend läuft)
npm run generate:api-types 2>/dev/null || echo "⚠️ Backend nicht verfügbar - API-Typen werden nicht aktualisiert"

# Frontend starten
npm run dev
EOF

    chmod +x start-frontend.sh

    # Services-Only Startskript
    cat > start-services.sh << 'EOF'
#!/bin/bash

BACKEND_DIR="$(pwd)/neuronode-backend"
cd "$BACKEND_DIR"

echo "🐳 Starte Docker Services..."
docker-compose up -d

echo "📊 Service Status:"
docker-compose ps
EOF

    chmod +x start-services.sh

    # Stop-Skript
    cat > stop-all.sh << 'EOF'
#!/bin/bash

echo "🛑 Stoppe alle Neuronode Services..."

# Stoppe Prozesse
pkill -f "uvicorn src.api.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

# Stoppe Docker Services
BACKEND_DIR="$(pwd)/neuronode-backend"
cd "$BACKEND_DIR"
docker-compose down

echo "✅ Alle Services gestoppt"
EOF

    chmod +x stop-all.sh

    success "Startskripte erstellt"
}

# System testen
test_system() {
    echo -e "\n${PURPLE}8. System testen...${NC}"
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
    
    # Python-Imports testen
    info "Teste Python-Imports..."
    python -c "from src.config.settings import settings; print('✅ Settings geladen')" || warning "Import-Fehler"
    
    # Frontend Dependencies testen
    cd "$FRONTEND_DIR"
    info "Teste Frontend Dependencies..."
    npm list --depth=0 > /dev/null 2>&1 && success "Frontend Dependencies OK" || warning "Frontend Dependencies-Fehler"
    
    cd "$PROJECT_ROOT"
}

# Finale Instruktionen
show_final_instructions() {
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   🎉 SETUP ABGESCHLOSSEN!                    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Verfügbare Startskripte:${NC}"
    echo ""
    echo -e "${CYAN}  ./start-all.sh${NC}      - Startet alle Services (Backend + Frontend)"
    echo -e "${CYAN}  ./start-backend.sh${NC}  - Nur Backend + Docker Services"
    echo -e "${CYAN}  ./start-frontend.sh${NC} - Nur Frontend"
    echo -e "${CYAN}  ./start-services.sh${NC} - Nur Docker Services"
    echo -e "${CYAN}  ./stop-all.sh${NC}       - Stoppt alle Services"
    echo ""
    echo -e "${BLUE}🌐 Service-URLs:${NC}"
    echo ""
    echo -e "${CYAN}  Frontend:     http://localhost:3000${NC}"
    echo -e "${CYAN}  Backend API:  http://localhost:8080${NC}"
    echo -e "${CYAN}  API Docs:     http://localhost:8080/docs${NC}"
    echo -e "${CYAN}  Neo4j:        http://localhost:7474${NC} (neo4j/password)"
    echo -e "${CYAN}  ChromaDB:     http://localhost:8000${NC}"
    echo ""
    echo -e "${BLUE}🚀 Schnellstart:${NC}"
    echo ""
    echo -e "${GREEN}  1. API-Keys konfigurieren:${NC}"
    echo -e "     ${YELLOW}nano neuronode-backend/.env${NC}"
    echo ""
    echo -e "${GREEN}  2. Alle Services starten:${NC}"
    echo -e "     ${YELLOW}./start-all.sh${NC}"
    echo ""
    echo -e "${GREEN}  3. Frontend öffnen:${NC}"
    echo -e "     ${YELLOW}http://localhost:3000${NC}"
    echo ""
    echo -e "${BLUE}📚 Weitere Informationen:${NC}"
    echo -e "  - Backend-Logs: $LOG_FILE"
    echo -e "  - API-Dokumentation: http://localhost:8080/docs"
    echo -e "  - Frontend-Tests: cd neuronode-webapp && npm test"
    echo ""
}

# Hauptprogramm
main() {
    # Leere Log-Datei
    > "$LOG_FILE"
    
    check_project_structure
    check_system_requirements
    setup_backend
    setup_frontend
    setup_docker_services
    initialize_database
    create_start_scripts
    test_system
    show_final_instructions
    
    echo -e "${GREEN}🎉 Setup erfolgreich abgeschlossen!${NC}"
    echo -e "${YELLOW}Führen Sie './start-all.sh' aus, um alle Services zu starten.${NC}"
}

# Skript ausführen
main "$@" 