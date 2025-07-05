#!/bin/bash

# =============================================================================
# NEURONODE STOP-ALL SCRIPT
# Beendet alle Neuronode-bezogenen Prozesse und Services
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
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/neuronode-backend"
FRONTEND_DIR="$PROJECT_ROOT/neuronode-webapp"

echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                    🛑 NEURONODE STOP-ALL                     ║${NC}"
echo -e "${RED}║              Beendet alle Services und Prozesse              ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Funktionen
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Prozesse nach Pattern finden und beenden
kill_processes_by_pattern() {
    local pattern="$1"
    local description="$2"
    
    info "Suche nach $description Prozessen..."
    
    # Finde PIDs mit pgrep
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "${CYAN}Gefundene PIDs: $pids${NC}"
        
        # Versuche graceful shutdown (SIGTERM)
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Beende Prozess $pid gracefully...${NC}"
                kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Warte kurz auf graceful shutdown
        sleep 3
        
        # Prüfe ob Prozesse noch laufen und force kill
        local remaining_pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            warning "Erzwinge Beendigung von: $remaining_pids"
            for pid in $remaining_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null
                fi
            done
        fi
        
        success "$description Prozesse beendet"
    else
        echo -e "${CYAN}Keine $description Prozesse gefunden${NC}"
    fi
}

# Prozesse auf bestimmten Ports finden und beenden
kill_processes_by_port() {
    local port="$1"
    local description="$2"
    
    info "Suche nach Prozessen auf Port $port ($description)..."
    
    # Finde Prozesse auf dem Port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "${CYAN}Gefundene PIDs auf Port $port: $pids${NC}"
        
        # Graceful shutdown
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Beende Prozess $pid auf Port $port...${NC}"
                kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Warte und prüfe
        sleep 2
        
        # Force kill falls nötig
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            warning "Erzwinge Beendigung auf Port $port: $remaining_pids"
            for pid in $remaining_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null
                fi
            done
        fi
        
        success "Prozesse auf Port $port beendet"
    else
        echo -e "${CYAN}Keine Prozesse auf Port $port gefunden${NC}"
    fi
}

# Alle Neuronode-bezogenen Ports finden
find_neuronode_ports() {
    info "Suche nach allen Neuronode-bezogenen Prozessen auf beliebigen Ports..."
    
    # Sammle alle PIDs von Neuronode-Prozessen
    local all_pids=""
    
    # Backend-Prozesse
    local backend_pids=$(pgrep -f "uvicorn.*src\.api\.main" 2>/dev/null)
    [ -n "$backend_pids" ] && all_pids="$all_pids $backend_pids"
    
    # Frontend-Prozesse
    local frontend_pids=$(pgrep -f "next.*dev\|next.*start" 2>/dev/null)
    [ -n "$frontend_pids" ] && all_pids="$all_pids $frontend_pids"
    
    # Node.js Prozesse im neuronode-webapp Verzeichnis
    local node_pids=$(pgrep -f "node.*neuronode-webapp" 2>/dev/null)
    [ -n "$node_pids" ] && all_pids="$all_pids $node_pids"
    
    # Python Prozesse mit neuronode
    local python_pids=$(pgrep -f "python.*neuronode" 2>/dev/null)
    [ -n "$python_pids" ] && all_pids="$all_pids $python_pids"
    
    if [ -n "$all_pids" ]; then
        echo -e "${CYAN}Alle gefundenen Neuronode PIDs: $all_pids${NC}"
        
        # Finde Ports für diese PIDs
        for pid in $all_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                local ports=$(lsof -Pan -p $pid -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | sort -u)
                if [ -n "$ports" ]; then
                    echo -e "${YELLOW}PID $pid lauscht auf Ports: $ports${NC}"
                fi
            fi
        done
    fi
}

# Docker Services stoppen
stop_docker_services() {
    echo -e "\n${PURPLE}🐳 Stoppe Docker Services...${NC}"
    
    if [ -d "$BACKEND_DIR" ]; then
        cd "$BACKEND_DIR"
        
        if [ -f "docker-compose.yml" ]; then
            info "Stoppe Docker Compose Services..."
            docker-compose down 2>/dev/null && success "Docker Compose Services gestoppt" || warning "Docker Compose Fehler"
        fi
        
        # Prüfe spezifische Container
        local containers="neuronode-neo4j neuronode-chromadb neuronode-redis neo4j chromadb redis"
        for container in $containers; do
            if docker ps -q -f name="$container" 2>/dev/null | grep -q .; then
                info "Stoppe Container: $container"
                docker stop "$container" 2>/dev/null && success "Container $container gestoppt" || warning "Container $container Fehler"
            fi
        done
        
        cd "$PROJECT_ROOT"
    else
        warning "Backend-Verzeichnis nicht gefunden"
    fi
}

# Backend-Prozesse stoppen
stop_backend_processes() {
    echo -e "\n${PURPLE}🔧 Stoppe Backend-Prozesse...${NC}"
    
    # Uvicorn/FastAPI Prozesse
    kill_processes_by_pattern "uvicorn.*src\.api\.main" "Backend API (uvicorn)"
    
    # Python CLI Prozesse
    kill_processes_by_pattern "python.*src\.cli" "Backend CLI"
    
    # Allgemeine Python Prozesse mit neuronode
    kill_processes_by_pattern "python.*neuronode-backend" "Backend Python"
    
    # Standard Backend Ports
    kill_processes_by_port 8080 "Backend API"
    kill_processes_by_port 8000 "Alternative Backend"
    kill_processes_by_port 5000 "Flask/Alternative Backend"
}

# Frontend-Prozesse stoppen
stop_frontend_processes() {
    echo -e "\n${PURPLE}🎨 Stoppe Frontend-Prozesse...${NC}"
    
    # Next.js Development Server
    kill_processes_by_pattern "next.*dev" "Next.js Development Server"
    
    # Next.js Production Server
    kill_processes_by_pattern "next.*start" "Next.js Production Server"
    
    # Node.js Prozesse im Frontend-Verzeichnis
    kill_processes_by_pattern "node.*neuronode-webapp" "Frontend Node.js"
    
    # npm/npx Prozesse
    kill_processes_by_pattern "npm.*run.*dev\|npx.*next" "npm/npx Frontend"
    
    # Standard Frontend Ports
    kill_processes_by_port 3000 "Frontend Development"
    kill_processes_by_port 3001 "Alternative Frontend"
    kill_processes_by_port 4000 "Alternative Frontend"
}

# Database-Prozesse stoppen
stop_database_processes() {
    echo -e "\n${PURPLE}🗄️ Stoppe Database-Prozesse...${NC}"
    
    # Standard Database Ports
    kill_processes_by_port 7687 "Neo4j Bolt"
    kill_processes_by_port 7474 "Neo4j HTTP"
    kill_processes_by_port 7473 "Neo4j HTTPS"
    kill_processes_by_port 8000 "ChromaDB"
    kill_processes_by_port 6379 "Redis"
}

# Alle Ports scannen
scan_all_ports() {
    echo -e "\n${PURPLE}🔍 Scanne alle Ports nach Neuronode-Prozessen...${NC}"
    
    info "Suche nach Prozessen mit 'neuronode' im Namen oder Pfad..."
    
    # Finde alle Prozesse mit neuronode im Namen/Pfad
    local neuronode_processes=$(ps aux | grep -i neuronode | grep -v grep | awk '{print $2}')
    
    if [ -n "$neuronode_processes" ]; then
        echo -e "${CYAN}Gefundene Neuronode-Prozesse:${NC}"
        ps aux | grep -i neuronode | grep -v grep | while read line; do
            echo -e "${YELLOW}  $line${NC}"
        done
        
        # Beende diese Prozesse
        for pid in $neuronode_processes; do
            if kill -0 "$pid" 2>/dev/null; then
                # Finde Port falls vorhanden
                local port=$(lsof -Pan -p $pid -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
                if [ -n "$port" ]; then
                    echo -e "${YELLOW}Beende PID $pid (Port: $port)${NC}"
                else
                    echo -e "${YELLOW}Beende PID $pid${NC}"
                fi
                kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Warte und force kill falls nötig
        sleep 3
        for pid in $neuronode_processes; do
            if kill -0 "$pid" 2>/dev/null; then
                warning "Erzwinge Beendigung von PID $pid"
                kill -KILL "$pid" 2>/dev/null
            fi
        done
    else
        echo -e "${CYAN}Keine weiteren Neuronode-Prozesse gefunden${NC}"
    fi
}

# Aufräumen von temporären Dateien
cleanup_temp_files() {
    echo -e "\n${PURPLE}🧹 Räume temporäre Dateien auf...${NC}"
    
    # PID-Dateien
    local pid_files="$PROJECT_ROOT/*.pid $BACKEND_DIR/*.pid $FRONTEND_DIR/*.pid"
    for pid_file in $pid_files; do
        if [ -f "$pid_file" ]; then
            info "Entferne PID-Datei: $pid_file"
            rm -f "$pid_file"
        fi
    done
    
    # Lock-Dateien
    local lock_files="$PROJECT_ROOT/*.lock $BACKEND_DIR/*.lock $FRONTEND_DIR/*.lock"
    for lock_file in $lock_files; do
        if [ -f "$lock_file" ]; then
            info "Entferne Lock-Datei: $lock_file"
            rm -f "$lock_file"
        fi
    done
    
    # Next.js Cache (falls gewünscht)
    if [ -d "$FRONTEND_DIR/.next" ]; then
        read -p "Möchten Sie den Next.js Cache (.next) löschen? (j/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Jj]$ ]]; then
            info "Entferne Next.js Cache..."
            rm -rf "$FRONTEND_DIR/.next"
            success "Next.js Cache entfernt"
        fi
    fi
    
    success "Temporäre Dateien aufgeräumt"
}

# Status-Report
show_status_report() {
    echo -e "\n${BLUE}📊 Status-Report nach dem Stoppen:${NC}"
    echo ""
    
    # Prüfe Standard-Ports
    local ports="3000 3001 4000 5000 6379 7474 7687 8000 8080"
    local active_ports=""
    
    for port in $ports; do
        if lsof -ti :$port >/dev/null 2>&1; then
            active_ports="$active_ports $port"
        fi
    done
    
    if [ -n "$active_ports" ]; then
        warning "Noch aktive Ports: $active_ports"
        echo ""
        for port in $active_ports; do
            echo -e "${YELLOW}Port $port:${NC}"
            lsof -i :$port 2>/dev/null | head -5
            echo ""
        done
    else
        success "Alle Standard-Ports sind frei"
    fi
    
    # Prüfe Docker Container
    local running_containers=$(docker ps -q 2>/dev/null)
    if [ -n "$running_containers" ]; then
        warning "Noch laufende Docker Container:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        success "Keine Docker Container laufen"
    fi
    
    # Prüfe Neuronode-Prozesse
    local remaining_processes=$(ps aux | grep -i neuronode | grep -v grep | grep -v "stop-all.sh")
    if [ -n "$remaining_processes" ]; then
        warning "Noch laufende Neuronode-Prozesse:"
        echo "$remaining_processes"
    else
        success "Keine Neuronode-Prozesse mehr aktiv"
    fi
}

# Hauptprogramm
main() {
    # Bestätigung einholen
    echo -e "${YELLOW}Dies wird alle Neuronode-bezogenen Prozesse und Services beenden.${NC}"
    read -p "Möchten Sie fortfahren? (j/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        echo -e "${CYAN}Abgebrochen.${NC}"
        exit 0
    fi
    
    echo -e "${RED}🛑 Beginne mit dem Stoppen aller Services...${NC}"
    echo ""
    
    # Ports vor dem Stoppen anzeigen
    find_neuronode_ports
    
    # Services stoppen
    stop_docker_services
    stop_backend_processes
    stop_frontend_processes
    stop_database_processes
    
    # Alle verbleibenden Prozesse finden und stoppen
    scan_all_ports
    
    # Aufräumen
    cleanup_temp_files
    
    # Status-Report
    show_status_report
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   🎉 STOP-ALL ABGESCHLOSSEN                  ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Alle Neuronode-Services wurden gestoppt.${NC}"
    echo -e "${CYAN}Sie können das System jetzt neu starten mit: ./start-all.sh${NC}"
    echo ""
}

# Skript ausführen
main "$@" 