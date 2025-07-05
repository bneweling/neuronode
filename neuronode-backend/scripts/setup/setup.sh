#!/bin/bash

# =============================================================================
# NEURONODE BACKEND SETUP SCRIPT
# Modernisiertes Backend-Setup ohne veraltete Dependencies
# =============================================================================

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Pfade ermitteln
BACKEND_DIR=$(pwd)
LOG_FILE="$BACKEND_DIR/setup.log"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                🔧 NEURONODE BACKEND SETUP                    ║${NC}"
echo -e "${BLUE}║           Enterprise Knowledge System Backend                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📂 Backend-Verzeichnis: $BACKEND_DIR${NC}"
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

# Prüfe ob wir im richtigen Verzeichnis sind
check_directory() {
    echo -e "\n${PURPLE}1. Prüfe Verzeichnisstruktur...${NC}"
    
    if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
        handle_error "Bitte führen Sie dieses Skript im neuronode-backend Verzeichnis aus!"
    fi
    
    if [ ! -f "docker-compose.yml" ]; then
        handle_error "docker-compose.yml nicht gefunden"
    fi
    
    success "Verzeichnisstruktur validiert"
}

# Prüfe Systemvoraussetzungen
check_prerequisites() {
    echo -e "\n${PURPLE}2. Prüfe Systemvoraussetzungen...${NC}"
    
    # Homebrew
    if ! command -v brew &> /dev/null; then
        warning "Homebrew nicht gefunden. Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Homebrew Installation fehlgeschlagen"
    fi
    success "Homebrew verfügbar"
    
    # Python 3.11+
    PYTHON_CMD=""
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    else
        warning "Python 3.11+ nicht gefunden. Installiere Python..."
        brew install python@3.11 || handle_error "Python Installation fehlgeschlagen"
        PYTHON_CMD="python3.11"
    fi
    success "Python 3.11+ verfügbar ($PYTHON_CMD)"
    
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

# Python Environment Setup
setup_python_env() {
    echo -e "\n${PURPLE}3. Python Virtual Environment einrichten...${NC}"
    
    # Alte venv entfernen falls vorhanden
    if [ -d "venv" ]; then
        warning "Entferne alte Virtual Environment..."
        rm -rf venv
    fi
    
    # Neue venv erstellen
    info "Erstelle neue Virtual Environment..."
    $PYTHON_CMD -m venv venv || handle_error "Virtual Environment konnte nicht erstellt werden"
    
    # Aktivieren
    source venv/bin/activate || handle_error "Virtual Environment konnte nicht aktiviert werden"
    
    # Pip upgrade
    info "Aktualisiere pip..."
    pip install --upgrade pip setuptools wheel
    
    # Requirements installieren
    info "Installiere Python-Pakete..."
    pip install -r requirements.txt || handle_error "Python-Pakete konnten nicht installiert werden"
    
    success "Python Environment eingerichtet"
}

# Environment Variables Setup
setup_env_file() {
    echo -e "\n${PURPLE}4. Environment-Variablen konfigurieren...${NC}"
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            warning ".env Datei erstellt. Bitte API-Keys eintragen!"
        else
            # Erstelle minimale .env Datei
            cat > .env << 'EOF'
# API Keys - Bitte eintragen
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CHROMA_HOST=localhost
CHROMA_PORT=8000

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Model Profile Configuration
MODEL_PROFILE=premium

# Processing Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIES=3
EOF
            warning ".env Datei erstellt. Bitte API-Keys konfigurieren!"
        fi
        
        echo -e "${YELLOW}Bearbeiten Sie die .env Datei und tragen Sie Ihre API-Keys ein.${NC}"
        
        # Versuche Editor zu öffnen
        if command -v code &> /dev/null; then
            code .env
        elif command -v nano &> /dev/null; then
            read -p "Möchten Sie die .env Datei jetzt bearbeiten? (j/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Jj]$ ]]; then
                nano .env
            fi
        else
            open -e .env
        fi
    else
        success "Environment-Variablen bereits konfiguriert"
    fi
}

# Docker Services Setup
setup_docker() {
    echo -e "\n${PURPLE}5. Docker Services starten...${NC}"
    
    # Services stoppen falls sie laufen
    docker-compose down 2>/dev/null || true
    
    # Services starten
    info "Starte Docker Services..."
    docker-compose up -d || handle_error "Docker Services konnten nicht gestartet werden"
    
    # Warten auf Services
    info "Warte auf Service-Bereitschaft..."
    
    # Neo4j health check
    echo -n "Neo4j"
    for i in {1..60}; do
        if curl -s http://localhost:7474 > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # ChromaDB health check
    echo -n "ChromaDB"
    for i in {1..60}; do
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Redis health check
    echo -n "Redis"
    for i in {1..30}; do
        if redis-cli ping > /dev/null 2>&1; then
            echo " ✅"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    success "Docker Services gestartet"
}

# Datenbankschema initialisieren
initialize_database() {
    echo -e "\n${PURPLE}6. Datenbankschema initialisieren...${NC}"
    
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
    
    # Schema-Migration
    if [ -f "scripts/setup/migrate_schema.py" ]; then
        info "Führe Schema-Migration aus..."
        python scripts/setup/migrate_schema.py || warning "Schema-Migration fehlgeschlagen"
        success "Datenbankschema initialisiert"
    else
        warning "Schema-Migration-Skript nicht gefunden"
    fi
}

# System testen
test_system() {
    echo -e "\n${PURPLE}7. System testen...${NC}"
    
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
    
    # Python imports testen
    info "Teste Python-Imports..."
    python -c "from src.config.settings import settings; print('✅ Settings geladen')" || warning "Import-Fehler"
    
    # CLI testen (falls vorhanden)
    if [ -f "src/cli/__init__.py" ] || [ -f "src/cli.py" ]; then
        info "Teste CLI..."
        python -m src.cli --help > /dev/null 2>&1 && success "CLI funktioniert" || warning "CLI-Fehler"
    fi
    
    # Datenbankverbindungen testen
    info "Teste Datenbankverbindungen..."
    python << 'EOF'
try:
    from src.storage.neo4j_client import Neo4jClient
    neo4j = Neo4jClient()
    neo4j.close()
    print("✅ Neo4j-Verbindung OK")
except Exception as e:
    print(f"❌ Neo4j-Fehler: {e}")

try:
    from src.storage.chroma_client import ChromaClient
    chroma = ChromaClient()
    print("✅ ChromaDB-Verbindung OK")
except Exception as e:
    print(f"❌ ChromaDB-Fehler: {e}")
EOF
}

# Startskripte erstellen
create_start_scripts() {
    echo -e "\n${PURPLE}8. Erstelle Startskripte...${NC}"
    
    # API Start-Skript
    cat > start-api.sh << 'EOF'
#!/bin/bash

# Starte Neuronode Backend API
echo "🚀 Starte Neuronode Backend API..."

# Aktiviere Virtual Environment
source venv/bin/activate

# Setze Python Path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Starte API Server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
EOF
    chmod +x start-api.sh
    
    # Services Start-Skript
    cat > start-services.sh << 'EOF'
#!/bin/bash

# Starte Docker Services
echo "🐳 Starte Docker Services..."
docker-compose up -d

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Service URLs:"
echo "  Neo4j:    http://localhost:7474"
echo "  ChromaDB: http://localhost:8000"
echo "  Redis:    localhost:6379"
EOF
    chmod +x start-services.sh
    
    # CLI Wrapper
    cat > ki-cli.sh << 'EOF'
#!/bin/bash

# Neuronode CLI Wrapper
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python -m src.cli "$@"
EOF
    chmod +x ki-cli.sh
    
    success "Startskripte erstellt"
}

# Finale Instruktionen
show_final_instructions() {
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║               🎉 BACKEND SETUP ABGESCHLOSSEN!                ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Nächste Schritte:${NC}"
    echo ""
    echo -e "${CYAN}1. API-Keys konfigurieren (falls noch nicht geschehen):${NC}"
    echo -e "   ${YELLOW}nano .env${NC}"
    echo ""
    echo -e "${CYAN}2. Services starten:${NC}"
    echo -e "   ${YELLOW}./start-services.sh${NC}  # Docker Services"
    echo -e "   ${YELLOW}./start-api.sh${NC}       # API Server"
    echo ""
    echo -e "${CYAN}3. CLI verwenden (falls verfügbar):${NC}"
    echo -e "   ${YELLOW}./ki-cli.sh --help${NC}"
    echo ""
    echo -e "${BLUE}🌐 Service-URLs:${NC}"
    echo ""
    echo -e "${CYAN}  API Server:  http://localhost:8080${NC}"
    echo -e "${CYAN}  API Docs:    http://localhost:8080/docs${NC}"
    echo -e "${CYAN}  Neo4j:       http://localhost:7474${NC} (neo4j/password)"
    echo -e "${CYAN}  ChromaDB:    http://localhost:8000${NC}"
    echo ""
    echo -e "${BLUE}📚 Weitere Informationen:${NC}"
    echo -e "  - Logs: $LOG_FILE"
    echo -e "  - API-Dokumentation: http://localhost:8080/docs"
    echo -e "  - OpenAPI Schema: http://localhost:8080/openapi.json"
    echo ""
}

# Hauptprogramm
main() {
    # Leere Log-Datei
    > "$LOG_FILE"
    
    check_directory
    check_prerequisites
    setup_python_env
    setup_env_file
    setup_docker
    initialize_database
    test_system
    create_start_scripts
    show_final_instructions
    
    echo -e "${GREEN}🎉 Backend-Setup erfolgreich abgeschlossen!${NC}"
    echo -e "${YELLOW}Führen Sie './start-api.sh' aus, um den API-Server zu starten.${NC}"
}

# Skript ausführen
main "$@"
