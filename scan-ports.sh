#!/bin/bash

# =============================================================================
# NEURONODE PORT SCANNER
# Findet alle Neuronode-bezogenen Prozesse und ihre Ports
# =============================================================================

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 🔍 NEURONODE PORT SCANNER                    ║${NC}"
echo -e "${BLUE}║          Findet alle Prozesse und verwendete Ports           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Standard-Ports prüfen
check_standard_ports() {
    echo -e "${PURPLE}📊 Standard-Ports prüfen:${NC}"
    echo ""
    
    local ports=(
        "3000:Frontend Development"
        "3001:Frontend Alternative"
        "4000:Frontend Alternative"
        "5000:Flask/Alternative Backend"
        "6379:Redis"
        "7474:Neo4j HTTP"
        "7687:Neo4j Bolt"
        "8000:ChromaDB/Alternative Backend"
        "8080:Backend API"
    )
    
    local active_found=false
    
    for port_info in "${ports[@]}"; do
        local port=$(echo $port_info | cut -d: -f1)
        local description=$(echo $port_info | cut -d: -f2)
        
        local pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$pids" ]; then
            active_found=true
            echo -e "${GREEN}Port $port ($description):${NC}"
            lsof -i :$port 2>/dev/null | while read line; do
                echo -e "  ${CYAN}$line${NC}"
            done
            echo ""
        fi
    done
    
    if [ "$active_found" = false ]; then
        echo -e "${CYAN}Keine Prozesse auf Standard-Ports gefunden${NC}"
    fi
    echo ""
}

# Neuronode-Prozesse finden
find_neuronode_processes() {
    echo -e "${PURPLE}🔍 Neuronode-Prozesse suchen:${NC}"
    echo ""
    
    # Verschiedene Suchpatterns
    local patterns=(
        "uvicorn.*src\.api\.main"
        "next.*dev"
        "next.*start"
        "python.*neuronode"
        "node.*neuronode"
        "npm.*neuronode"
        "neuronode"
    )
    
    local found_processes=false
    
    for pattern in "${patterns[@]}"; do
        local pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ -n "$pids" ]; then
            found_processes=true
            echo -e "${GREEN}Pattern: $pattern${NC}"
            
            for pid in $pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    # Prozess-Info
                    local process_info=$(ps -p $pid -o pid,ppid,user,command --no-headers 2>/dev/null)
                    echo -e "  ${YELLOW}PID $pid:${NC} $process_info"
                    
                    # Ports für diesen Prozess
                    local ports=$(lsof -Pan -p $pid -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | sort -u)
                    if [ -n "$ports" ]; then
                        echo -e "    ${CYAN}Ports: $ports${NC}"
                    else
                        echo -e "    ${CYAN}Keine Ports${NC}"
                    fi
                    
                    # Working Directory
                    local cwd=$(lsof -p $pid | grep cwd | awk '{print $9}' 2>/dev/null)
                    if [ -n "$cwd" ]; then
                        echo -e "    ${CYAN}CWD: $cwd${NC}"
                    fi
                    echo ""
                fi
            done
        fi
    done
    
    if [ "$found_processes" = false ]; then
        echo -e "${CYAN}Keine Neuronode-Prozesse gefunden${NC}"
    fi
    echo ""
}

# Docker Container prüfen
check_docker_containers() {
    echo -e "${PURPLE}🐳 Docker Container prüfen:${NC}"
    echo ""
    
    # Alle Container
    local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
    if [ -n "$containers" ]; then
        echo -e "${GREEN}Laufende Container:${NC}"
        echo "$containers"
        echo ""
        
        # Neuronode-spezifische Container
        local neuronode_containers=$(docker ps --filter "name=neuronode" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
        if [ -n "$neuronode_containers" ]; then
            echo -e "${GREEN}Neuronode Container:${NC}"
            echo "$neuronode_containers"
            echo ""
        fi
        
        # Standard Database Container
        local db_containers=$(docker ps --filter "name=neo4j" --filter "name=chromadb" --filter "name=redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
        if [ -n "$db_containers" ]; then
            echo -e "${GREEN}Database Container:${NC}"
            echo "$db_containers"
            echo ""
        fi
    else
        echo -e "${CYAN}Keine Docker Container laufen${NC}"
        echo ""
    fi
}

# Alle Ports scannen (erweitert)
scan_all_ports() {
    echo -e "${PURPLE}🌐 Erweiterte Port-Suche:${NC}"
    echo ""
    
    # Finde alle Prozesse mit neuronode im Pfad oder Namen
    local all_neuronode=$(ps aux | grep -i neuronode | grep -v grep | grep -v scan-ports)
    
    if [ -n "$all_neuronode" ]; then
        echo -e "${GREEN}Alle Neuronode-bezogenen Prozesse:${NC}"
        echo ""
        echo "$all_neuronode" | while read line; do
            local pid=$(echo $line | awk '{print $2}')
            echo -e "${YELLOW}$line${NC}"
            
            # Finde alle Ports für diesen Prozess
            local all_ports=$(lsof -Pan -p $pid -i 2>/dev/null | grep -E 'LISTEN|ESTABLISHED' | awk '{print $9}' | sort -u)
            if [ -n "$all_ports" ]; then
                echo -e "  ${CYAN}Netzwerk-Verbindungen: $all_ports${NC}"
            fi
            echo ""
        done
    else
        echo -e "${CYAN}Keine Neuronode-Prozesse gefunden${NC}"
    fi
    echo ""
}

# Port-Range scannen
scan_port_range() {
    echo -e "${PURPLE}🔢 Port-Range Scan (3000-8080):${NC}"
    echo ""
    
    local active_ports=""
    for port in {3000..3010} {4000..4010} {5000..5010} {6379..6379} {7470..7690} {8000..8090}; do
        if lsof -ti :$port >/dev/null 2>&1; then
            active_ports="$active_ports $port"
        fi
    done
    
    if [ -n "$active_ports" ]; then
        echo -e "${GREEN}Aktive Ports in relevanten Bereichen:${NC}"
        for port in $active_ports; do
            echo -e "${YELLOW}Port $port:${NC}"
            lsof -i :$port 2>/dev/null | head -3
            echo ""
        done
    else
        echo -e "${CYAN}Keine aktiven Ports in den relevanten Bereichen gefunden${NC}"
    fi
    echo ""
}

# Zusammenfassung
show_summary() {
    echo -e "${BLUE}📋 Zusammenfassung:${NC}"
    echo ""
    
    # Zähle Prozesse
    local backend_count=$(pgrep -f "uvicorn.*src\.api\.main" | wc -l)
    local frontend_count=$(pgrep -f "next.*dev\|next.*start" | wc -l)
    local docker_count=$(docker ps -q | wc -l)
    local total_neuronode=$(ps aux | grep -i neuronode | grep -v grep | grep -v scan-ports | wc -l)
    
    echo -e "${CYAN}Backend-Prozesse: $backend_count${NC}"
    echo -e "${CYAN}Frontend-Prozesse: $frontend_count${NC}"
    echo -e "${CYAN}Docker Container: $docker_count${NC}"
    echo -e "${CYAN}Gesamt Neuronode-Prozesse: $total_neuronode${NC}"
    echo ""
    
    # Empfehlungen
    if [ $total_neuronode -gt 0 ]; then
        echo -e "${YELLOW}💡 Empfehlungen:${NC}"
        echo -e "  • Verwenden Sie ${GREEN}./stop-all.sh${NC} für vollständige Beendigung"
        echo -e "  • Verwenden Sie ${GREEN}./quick-stop.sh${NC} für schnelle Beendigung"
        echo -e "  • Verwenden Sie ${GREEN}./start-all.sh${NC} für Neustart"
    else
        echo -e "${GREEN}✅ System ist bereit für einen Neustart${NC}"
    fi
    echo ""
}

# Hauptprogramm
main() {
    check_standard_ports
    find_neuronode_processes
    check_docker_containers
    scan_all_ports
    scan_port_range
    show_summary
    
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🔍 SCAN ABGESCHLOSSEN                     ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
}

# Skript ausführen
main "$@" 