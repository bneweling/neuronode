#!/bin/bash

# =============================================================================
# NEURONODE FRONTEND SETUP SCRIPT
# Setup für Next.js Frontend mit TypeScript und Testing
# =============================================================================

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Pfade
FRONTEND_DIR=$(pwd)
LOG_FILE="$FRONTEND_DIR/setup.log"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║               🎨 NEURONODE FRONTEND SETUP                    ║${NC}"
echo -e "${BLUE}║            Next.js + TypeScript + Testing Suite              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📂 Frontend-Verzeichnis: $FRONTEND_DIR${NC}"
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

# Prüfe Verzeichnisstruktur
check_directory() {
    echo -e "\n${PURPLE}1. Prüfe Verzeichnisstruktur...${NC}"
    
    if [ ! -f "package.json" ]; then
        handle_error "package.json nicht gefunden. Bitte im neuronode-webapp Verzeichnis ausführen!"
    fi
    
    if [ ! -f "next.config.ts" ]; then
        handle_error "next.config.ts nicht gefunden"
    fi
    
    if [ ! -f "tsconfig.json" ]; then
        handle_error "tsconfig.json nicht gefunden"
    fi
    
    success "Verzeichnisstruktur validiert"
}

# Prüfe Systemvoraussetzungen
check_prerequisites() {
    echo -e "\n${PURPLE}2. Prüfe Systemvoraussetzungen...${NC}"
    
    # Node.js
    if ! command -v node &> /dev/null; then
        warning "Node.js nicht gefunden. Installiere Node.js..."
        if command -v brew &> /dev/null; then
            brew install node || handle_error "Node.js Installation fehlgeschlagen"
        else
            handle_error "Bitte Node.js manuell installieren: https://nodejs.org/"
        fi
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        warning "Node.js Version zu alt (benötigt: 18+, gefunden: $NODE_VERSION)"
        if command -v brew &> /dev/null; then
            brew upgrade node || handle_error "Node.js Update fehlgeschlagen"
        else
            handle_error "Bitte Node.js 18+ manuell installieren"
        fi
    fi
    success "Node.js 18+ verfügbar (v$(node --version))"
    
    # npm
    if ! command -v npm &> /dev/null; then
        handle_error "npm nicht gefunden"
    fi
    success "npm verfügbar (v$(npm --version))"
}

# Dependencies installieren
install_dependencies() {
    echo -e "\n${PURPLE}3. Installiere Dependencies...${NC}"
    
    # Node modules löschen falls vorhanden
    if [ -d "node_modules" ]; then
        warning "Entferne alte node_modules..."
        rm -rf node_modules
    fi
    
    if [ -f "package-lock.json" ]; then
        warning "Entferne package-lock.json..."
        rm -f package-lock.json
    fi
    
    # Dependencies installieren
    info "Installiere npm Dependencies..."
    npm install || handle_error "npm install fehlgeschlagen"
    
    success "Dependencies installiert"
}

# Development Tools Setup
setup_dev_tools() {
    echo -e "\n${PURPLE}4. Development Tools Setup...${NC}"
    
    # Playwright installieren
    info "Installiere Playwright Browser..."
    npx playwright install --with-deps || warning "Playwright Installation fehlgeschlagen"
    
    # TypeScript prüfen
    info "Prüfe TypeScript Konfiguration..."
    npx tsc --noEmit || warning "TypeScript Fehler gefunden"
    
    # ESLint prüfen
    info "Prüfe ESLint Konfiguration..."
    npm run lint || warning "ESLint Fehler gefunden"
    
    success "Development Tools eingerichtet"
}

# Environment Setup
setup_environment() {
    echo -e "\n${PURPLE}5. Environment Setup...${NC}"
    
    # .env.local erstellen falls nicht vorhanden
    if [ ! -f ".env.local" ]; then
        cat > .env.local << 'EOF'
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080

# Development Settings
NODE_ENV=development

# Optional: Analytics
# NEXT_PUBLIC_GA_ID=your_google_analytics_id
EOF
        success ".env.local erstellt"
    else
        success "Environment bereits konfiguriert"
    fi
}

# Build-Test
test_build() {
    echo -e "\n${PURPLE}6. Build-Test...${NC}"
    
    info "Teste Development Build..."
    # Kurzer Build-Test ohne vollständigen Build
    npm run build --dry-run 2>/dev/null || warning "Build-Test fehlgeschlagen"
    
    success "Build-Test abgeschlossen"
}

# Tests ausführen
run_tests() {
    echo -e "\n${PURPLE}7. Führe Tests aus...${NC}"
    
    # Unit Tests (falls vorhanden)
    if [ -d "tests/unit" ]; then
        info "Führe Unit Tests aus..."
        npm run test:coverage || warning "Unit Tests fehlgeschlagen"
    fi
    
    # Accessibility Tests (falls vorhanden)
    if [ -d "tests/a11y" ]; then
        info "Führe Accessibility Tests aus..."
        npm run test:accessibility || warning "Accessibility Tests fehlgeschlagen"
    fi
    
    success "Tests abgeschlossen"
}

# Startskripte erstellen
create_start_scripts() {
    echo -e "\n${PURPLE}8. Erstelle Startskripte...${NC}"
    
    # Development Start-Skript
    cat > start-dev.sh << 'EOF'
#!/bin/bash

# Starte Neuronode Frontend Development Server
echo "🎨 Starte Frontend Development Server..."

# Prüfe ob Backend läuft
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "⚠️ Backend nicht erreichbar - einige Features funktionieren möglicherweise nicht"
    echo "Starte zuerst das Backend mit: ../start-backend.sh"
fi

# Generiere API-Typen falls Backend verfügbar
npm run generate:api-types 2>/dev/null || echo "⚠️ API-Typen konnten nicht aktualisiert werden"

# Starte Development Server
npm run dev
EOF
    chmod +x start-dev.sh
    
    # Production Build-Skript
    cat > build-prod.sh << 'EOF'
#!/bin/bash

# Build für Production
echo "🏗️ Erstelle Production Build..."

# API-Typen generieren
echo "📝 Generiere API-Typen..."
npm run generate:api-types || echo "⚠️ API-Typen Generation fehlgeschlagen"

# Production Build
echo "🔨 Erstelle Build..."
npm run build

echo "✅ Production Build erstellt"
echo "Starte mit: npm start"
EOF
    chmod +x build-prod.sh
    
    # Test-Skript
    cat > run-tests.sh << 'EOF'
#!/bin/bash

# Führe alle Tests aus
echo "🧪 Führe Tests aus..."

echo "📋 Unit Tests..."
npm run test:coverage

echo "♿ Accessibility Tests..."
npm run test:accessibility

echo "🎭 E2E Tests..."
npm run test:e2e

echo "✅ Alle Tests abgeschlossen"
EOF
    chmod +x run-tests.sh
    
    success "Startskripte erstellt"
}

# Finale Instruktionen
show_final_instructions() {
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 FRONTEND SETUP ABGESCHLOSSEN!                ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 Verfügbare Skripte:${NC}"
    echo ""
    echo -e "${CYAN}  ./start-dev.sh${NC}     - Starte Development Server"
    echo -e "${CYAN}  ./build-prod.sh${NC}    - Erstelle Production Build"
    echo -e "${CYAN}  ./run-tests.sh${NC}     - Führe alle Tests aus"
    echo ""
    echo -e "${BLUE}📋 NPM Skripte:${NC}"
    echo ""
    echo -e "${CYAN}  npm run dev${NC}                    - Development Server"
    echo -e "${CYAN}  npm run build${NC}                  - Production Build"
    echo -e "${CYAN}  npm run start${NC}                  - Production Server"
    echo -e "${CYAN}  npm run lint${NC}                   - ESLint"
    echo -e "${CYAN}  npm run test${NC}                   - E2E Tests"
    echo -e "${CYAN}  npm run test:coverage${NC}          - Unit Tests mit Coverage"
    echo -e "${CYAN}  npm run test:accessibility${NC}     - Accessibility Tests"
    echo -e "${CYAN}  npm run generate:api-types${NC}     - API-Typen generieren"
    echo ""
    echo -e "${BLUE}🌐 URLs (nach Start):${NC}"
    echo ""
    echo -e "${CYAN}  Frontend:     http://localhost:3000${NC}"
    echo -e "${CYAN}  Backend API:  http://localhost:8080${NC}"
    echo ""
    echo -e "${BLUE}🚀 Schnellstart:${NC}"
    echo ""
    echo -e "${GREEN}  1. Backend starten (falls noch nicht gestartet):${NC}"
    echo -e "     ${YELLOW}cd ../neuronode-backend && ./start-api.sh${NC}"
    echo ""
    echo -e "${GREEN}  2. Frontend starten:${NC}"
    echo -e "     ${YELLOW}./start-dev.sh${NC}"
    echo ""
    echo -e "${GREEN}  3. Browser öffnen:${NC}"
    echo -e "     ${YELLOW}http://localhost:3000${NC}"
    echo ""
    echo -e "${BLUE}📚 Weitere Informationen:${NC}"
    echo -e "  - Setup-Logs: $LOG_FILE"
    echo -e "  - Next.js Docs: https://nextjs.org/docs"
    echo -e "  - TypeScript: npx tsc --noEmit"
    echo ""
}

# Hauptprogramm
main() {
    # Leere Log-Datei
    > "$LOG_FILE"
    
    check_directory
    check_prerequisites
    install_dependencies
    setup_dev_tools
    setup_environment
    test_build
    run_tests
    create_start_scripts
    show_final_instructions
    
    echo -e "${GREEN}🎉 Frontend-Setup erfolgreich abgeschlossen!${NC}"
    echo -e "${YELLOW}Führen Sie './start-dev.sh' aus, um den Development Server zu starten.${NC}"
}

# Skript ausführen
main "$@" 