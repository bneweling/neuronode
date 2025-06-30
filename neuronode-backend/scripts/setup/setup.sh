#!/bin/bash
# setup.sh - Angepasst für getrennte Repositories

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# WICHTIG: Pfade ermitteln
BACKEND_DIR=$(pwd)
PLUGIN_DIR="../obsidian-ki-plugin"

echo -e "${BLUE}=== Neuronode Setup ===${NC}"
echo "Backend-Verzeichnis: $BACKEND_DIR"

# Prüfe ob wir im richtigen Verzeichnis sind
if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
    echo -e "${RED}❌ Fehler: Bitte führen Sie dieses Skript im neuronode Hauptverzeichnis aus!${NC}"
    echo "Aktuelles Verzeichnis: $(pwd)"
    echo "Erwartete Dateien: requirements.txt, src/"
    exit 1
fi

# Prüfe ob Plugin-Verzeichnis existiert
if [ ! -d "$PLUGIN_DIR" ]; then
    echo -e "${YELLOW}⚠️  Obsidian Plugin nicht gefunden unter: $PLUGIN_DIR${NC}"
    read -p "Geben Sie den Pfad zum obsidian-ki-plugin Verzeichnis ein (oder Enter für ohne Plugin): " custom_plugin_path
    if [ -n "$custom_plugin_path" ]; then
        PLUGIN_DIR="$custom_plugin_path"
    else
        PLUGIN_DIR=""
    fi
fi

# Log-Datei
LOG_FILE="setup.log"

# Funktion für Fehlermeldungen
handle_error() {
    echo -e "${RED}❌ Fehler: $1${NC}"
    echo "Siehe $LOG_FILE für Details"
    exit 1
}

# Funktion für Erfolsmeldungen
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Funktion für Warnungen
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Voraussetzungen prüfen
check_prerequisites() {
    echo -e "\n${BLUE}1. Prüfe Voraussetzungen...${NC}"
    
    # Homebrew
    if ! command -v brew &> /dev/null; then
        warning "Homebrew nicht gefunden. Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error "Homebrew Installation fehlgeschlagen"
    fi
    success "Homebrew verfügbar"
    
    # Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        warning "Python 3.11 nicht gefunden. Installiere Python..."
        brew install python@3.11 || handle_error "Python Installation fehlgeschlagen"
    fi
    success "Python 3.11 verfügbar"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        warning "Docker nicht gefunden. Bitte Docker Desktop für Mac installieren:"
        echo "https://www.docker.com/products/docker-desktop/"
        read -p "Drücken Sie Enter nachdem Docker installiert wurde..."
    fi
    
    # Docker läuft?
    if ! docker info &> /dev/null; then
        warning "Docker läuft nicht. Starte Docker Desktop..."
        open -a Docker
        echo "Warte auf Docker..."
        while ! docker info &> /dev/null; do
            sleep 2
        done
    fi
    success "Docker läuft"
    
    # Node.js für Obsidian Plugin
    if ! command -v node &> /dev/null; then
        warning "Node.js nicht gefunden. Installiere Node.js..."
        brew install node || handle_error "Node.js Installation fehlgeschlagen"
    fi
    success "Node.js verfügbar"
}

# 2. Repository Setup
setup_repository() {
    echo -e "\n${BLUE}2. Repository Setup...${NC}"
    
    # Arbeitsverzeichnis
    WORK_DIR=$(pwd)
    echo "Arbeitsverzeichnis: $WORK_DIR"
    
    # Struktur prüfen
    if [ ! -f "requirements.txt" ]; then
        handle_error "requirements.txt nicht gefunden. Bitte im richtigen Verzeichnis ausführen!"
    fi
    
    # Erstelle fehlende Verzeichnisse
    mkdir -p data logs
    mkdir -p src/{api/endpoints,document_processing/loaders}
    
    # __init__.py Dateien erstellen
    find src -type d -exec touch {}/__init__.py \;
    
    success "Repository-Struktur vorbereitet"
}

# 3. Python Environment
setup_python_env() {
    echo -e "\n${BLUE}3. Python Virtual Environment einrichten...${NC}"
    
    # Alte venv entfernen falls vorhanden
    [ -d "venv" ] && rm -rf venv
    
    # Neue venv erstellen
    python3.11 -m venv venv || handle_error "Virtual Environment konnte nicht erstellt werden"
    
    # Aktivieren
    source venv/bin/activate || handle_error "Virtual Environment konnte nicht aktiviert werden"
    
    # Pip upgrade
    pip install --upgrade pip
    
    # Requirements installieren
    echo "Installiere Python-Pakete..."
    pip install -r requirements.txt || handle_error "Python-Pakete konnten nicht installiert werden"
    
    # Aktualisiere kritische Abhängigkeiten für Gemini API
    echo "Aktualisiere Gemini API-Abhängigkeiten..."
    pip install --upgrade langchain-google-genai==2.1.5 || warning "LangChain Google GenAI Update fehlgeschlagen"
    pip install --upgrade pydantic-settings>=2.10.0 || warning "Pydantic Settings Update fehlgeschlagen"
    
    # Protobuf-Kompatibilität sicherstellen
    echo "Konfiguriere Protobuf-Kompatibilität..."
    echo 'export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python' >> venv/bin/activate || true
    echo "Protobuf-Workaround zu venv/bin/activate hinzugefügt"
    
    # Auch in Start-Skripte einbauen
    if [ -f "./start-all.sh" ]; then
        sed -i '' '1i\
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
' ./start-all.sh || true
    fi
    
    success "Python Environment eingerichtet"
}

# 4. Environment Variables
setup_env_file() {
    echo -e "\n${BLUE}4. Environment-Variablen konfigurieren...${NC}"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
        else
            # .env.example erstellen
            cat > .env.example << 'EOF'
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CHROMA_HOST=localhost
CHROMA_PORT=8000

# Model Profile Configuration
# Options: premium, balanced, cost_effective, gemini_only, openai_only
# Test modes: gemini_only (only Google API), openai_only (only OpenAI API)
MODEL_PROFILE=premium

# Legacy Model Configuration (Optional - overrides MODEL_PROFILE if all are set)
# CLASSIFIER_MODEL=gemini-2.5-flash
# EXTRACTOR_MODEL=gpt-4.1
# SYNTHESIZER_MODEL=claude-opus-4-20250514
# VALIDATOR_MODEL_1=gpt-4o
# VALIDATOR_MODEL_2=claude-sonnet-4-20250514

# Processing Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIES=3
EOF
            cp .env.example .env
        fi
        
        warning ".env Datei erstellt. Bitte API-Keys eintragen!"
        echo -e "${YELLOW}Bearbeiten Sie die .env Datei und tragen Sie Ihre API-Keys ein.${NC}"
        echo "Öffne .env in Editor..."
        
        # Versuche Editor zu öffnen
        if command -v code &> /dev/null; then
            code .env
        elif command -v nano &> /dev/null; then
            nano .env
        else
            open -e .env
        fi
        
        read -p "Drücken Sie Enter nachdem Sie die API-Keys eingetragen haben..."
    fi
    
    # Prüfen ob Keys gesetzt sind
    source .env
    if [ "$OPENAI_API_KEY" = "your-openai-key" ]; then
        warning "API-Keys noch nicht konfiguriert!"
    else
        success "Environment-Variablen konfiguriert"
    fi
}

# 5. Docker Services
setup_docker() {
    echo -e "\n${BLUE}5. Docker Services starten...${NC}"
    
    # Docker Compose Datei prüfen
    if [ ! -f "docker-compose.yml" ]; then
        warning "docker-compose.yml nicht gefunden. Erstelle Datei..."
        # Hier würde der docker-compose.yml Inhalt eingefügt
        handle_error "Bitte docker-compose.yml manuell erstellen"
    fi
    
    # Services stoppen falls sie laufen
    docker-compose down 2>/dev/null
    
    # Services starten
    echo "Starte Docker Services..."
    docker-compose up -d neo4j chromadb redis || handle_error "Docker Services konnten nicht gestartet werden"
    
    # Warten auf Services
    echo "Warte auf Service-Bereitschaft..."
    
    # Neo4j health check
    echo -n "Warte auf Neo4j"
    for i in {1..30}; do
        if curl -s http://localhost:7474 > /dev/null; then
            echo ""
            success "Neo4j bereit"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # ChromaDB health check
    echo -n "Warte auf ChromaDB"
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
            echo ""
            success "ChromaDB bereit"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    success "Docker Services gestartet"
}

# 6. System testen
test_system() {
    echo -e "\n${BLUE}6. System testen...${NC}"
    
    # Python imports testen
    echo "Teste Python-Imports..."
    python -c "from src.config.settings import settings; print('Settings geladen')" || warning "Import-Fehler"
    
    # CLI testen
    echo "Teste CLI..."
    python -m src.cli --help > /dev/null && success "CLI funktioniert" || warning "CLI-Fehler"
    
    # Gemini API testen
    echo "Teste Gemini API-Integration..."
    python scripts/setup/test-gemini-api.py > /dev/null 2>&1 && success "Gemini API funktioniert" || warning "Gemini API-Fehler - Bitte API-Keys prüfen"
    
    # Verbindungen testen
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

# 7. Obsidian Plugin
setup_obsidian_plugin() {
    echo -e "\n${BLUE}7. Obsidian Plugin einrichten...${NC}"
    
    read -p "Möchten Sie das Obsidian Plugin installieren? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        if [ -d "../obsidian-ki-plugin" ]; then
            cd ../obsidian-ki-plugin
            
            echo "Installiere Node-Dependencies..."
            npm install || warning "npm install fehlgeschlagen"
            
            # Installiere D3-Typen falls nicht vorhanden
            if ! npm list @types/d3 >/dev/null 2>&1; then
                echo "Installiere TypeScript-Typen..."
                npm install --save-dev @types/d3 || warning "TypeScript-Typen Installation fehlgeschlagen"
            fi
            
            echo "Baue Plugin..."
            npm run build || warning "Plugin-Build fehlgeschlagen"
            
            # Obsidian Plugin-Verzeichnis finden
            OBSIDIAN_LOCAL="$HOME/Library/Application Support/obsidian"
            OBSIDIAN_ICLOUD="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
            
            if [ -d "$OBSIDIAN_LOCAL" ]; then
                success "Obsidian Plugin vorbereitet (lokale Installation)"
                echo ""
                echo "🔍 Verwenden Sie diese Skripte:"
                echo -e "  ${BLUE}./setup-obsidian.sh${NC}          - All-in-One Plugin Setup (empfohlen)"
                echo -e "  ${BLUE}./find-obsidian-paths.sh${NC}     - Zeigt Vault-Pfade an + Installation"
                echo -e "  ${BLUE}./install-obsidian-plugin.sh${NC} - Manuelle Plugin-Installation"
                echo ""
                echo "Oder manuell kopieren nach:"
                echo "$OBSIDIAN_LOCAL/IhrVault/.obsidian/plugins/"
            elif [ -d "$OBSIDIAN_ICLOUD" ]; then
                success "Obsidian Plugin vorbereitet (iCloud-Sync)"
                echo "Kopieren Sie den obsidian-ki-plugin Ordner nach:"
                echo "$OBSIDIAN_ICLOUD/IhrVault/.obsidian/plugins/"
            else
                warning "Obsidian-Verzeichnis nicht gefunden"
                echo "Mögliche Pfade:"
                echo "  - Lokal: ~/Library/Application Support/obsidian/IhrVault/.obsidian/plugins/"
                echo "  - iCloud: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/IhrVault/.obsidian/plugins/"
                echo "Bitte kopieren Sie das Plugin manuell nach einem dieser Pfade."
            fi
            
            cd "$WORK_DIR"
        else
            warning "Obsidian Plugin-Verzeichnis nicht gefunden"
        fi
    fi
}

# 8. Startskripte erstellen
create_start_scripts() {
    echo -e "\n${BLUE}8. Erstelle Startskripte...${NC}"
    
    # API Start-Skript
    cat > start-api.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
EOF
    chmod +x start-api.sh
    
    # CLI Wrapper
    cat > ki-cli.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"
python -m src.cli "$@"
EOF
    chmod +x ki-cli.sh
    
    # Docker Start-Skript
    cat > start-services.sh << 'EOF'
#!/bin/bash
docker-compose up -d neo4j chromadb redis
echo "Warte auf Services..."
sleep 10
docker-compose ps
EOF
    chmod +x start-services.sh
    
    success "Startskripte erstellt"
}

# 9. Finale Instruktionen
show_final_instructions() {
    echo -e "\n${GREEN}=== Setup abgeschlossen! ===${NC}"
    echo
    echo "📋 Nächste Schritte:"
    echo
    echo "1. API-Keys in .env eintragen (falls noch nicht geschehen)"
    echo -e "   ${BLUE}nano .env${NC}"
    echo
    echo "2. Services starten:"
    echo -e "   ${BLUE}./start-services.sh${NC}  # Docker Services"
    echo -e "   ${BLUE}./start-api.sh${NC}       # API Server"
    echo
    echo "3. CLI verwenden:"
    echo -e "   ${BLUE}./ki-cli.sh query \"Ihre Frage\"${NC}"
    echo -e "   ${BLUE}./ki-cli.sh process dokument.pdf${NC}"
    echo -e "   ${BLUE}./ki-cli.sh stats${NC}"
    echo
    echo "4. Web-Interface:"
    echo -e "   API Docs: ${BLUE}http://localhost:8080/docs${NC}"
    echo -e "   Neo4j:    ${BLUE}http://localhost:7474${NC} (neo4j/password)"
    echo
    echo "5. Obsidian Plugin:"
    echo -e "   ${BLUE}./setup-obsidian.sh${NC}          # All-in-One Setup (empfohlen)"
    echo "   - Plugin in Obsidian aktivieren"
    echo "   - API URL: http://localhost:8080"
    echo ""
    echo "6. Plugin-Features nutzen:"
    echo "   📤 Dokumentenupload (Ribbon-Icon oder Cmd+P)"
    echo "   💬 Knowledge Chat (Ribbon-Icon oder Cmd+P)"  
    echo "   🕸️ Knowledge Graph (Ribbon-Icon oder Cmd+P)"
    echo
    echo "📚 Dokumentation: siehe README.md"
    echo "❓ Bei Problemen: siehe $LOG_FILE"
}

# Hauptprogramm
main() {
    check_prerequisites
    setup_repository
    setup_python_env
    setup_env_file
    setup_docker
    test_system
    setup_obsidian_plugin
    create_start_scripts
    show_final_instructions
}

# Error handler
trap 'handle_error "Unerwarteter Fehler in Zeile $LINENO"' ERR

# Ausführen
main
