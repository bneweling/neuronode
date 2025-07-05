#!/bin/bash

# =============================================================================
# NEURONODE QUICK-STOP SCRIPT
# Schnelle Beendigung aller Neuronode-Prozesse ohne Bestätigung
# =============================================================================

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}🛑 Quick-Stop: Beende alle Neuronode-Prozesse...${NC}"

# Schnelle Prozess-Beendigung
quick_kill() {
    local pattern="$1"
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    [ -n "$pids" ] && kill -TERM $pids 2>/dev/null
    sleep 1
    local remaining=$(pgrep -f "$pattern" 2>/dev/null)
    [ -n "$remaining" ] && kill -KILL $remaining 2>/dev/null
}

# Schnelle Port-Beendigung
quick_kill_port() {
    local port="$1"
    local pids=$(lsof -ti :$port 2>/dev/null)
    [ -n "$pids" ] && kill -TERM $pids 2>/dev/null
    sleep 1
    local remaining=$(lsof -ti :$port 2>/dev/null)
    [ -n "$remaining" ] && kill -KILL $remaining 2>/dev/null
}

# Docker Services stoppen
echo -e "${YELLOW}Stoppe Docker Services...${NC}"
if [ -d "neuronode-backend" ]; then
    cd neuronode-backend
    docker-compose down >/dev/null 2>&1
    cd ..
fi

# Prozesse nach Pattern beenden
echo -e "${YELLOW}Beende Backend-Prozesse...${NC}"
quick_kill "uvicorn.*src\.api\.main"
quick_kill "python.*neuronode-backend"
quick_kill "python.*src\.cli"

echo -e "${YELLOW}Beende Frontend-Prozesse...${NC}"
quick_kill "next.*dev"
quick_kill "next.*start"
quick_kill "node.*neuronode-webapp"
quick_kill "npm.*run.*dev"

echo -e "${YELLOW}Beende alle Neuronode-Prozesse...${NC}"
quick_kill "neuronode"

# Standard-Ports beenden
echo -e "${YELLOW}Beende Prozesse auf Standard-Ports...${NC}"
for port in 3000 3001 4000 5000 6379 7474 7687 8000 8080; do
    quick_kill_port $port
done

# Aufräumen
rm -f *.pid neuronode-backend/*.pid neuronode-webapp/*.pid 2>/dev/null

echo -e "${GREEN}✅ Quick-Stop abgeschlossen${NC}"

# Kurzer Status-Check
active_ports=""
for port in 3000 8080 7474; do
    if lsof -ti :$port >/dev/null 2>&1; then
        active_ports="$active_ports $port"
    fi
done

if [ -n "$active_ports" ]; then
    echo -e "${YELLOW}⚠️ Noch aktive Ports: $active_ports${NC}"
    echo -e "${YELLOW}Führen Sie './stop-all.sh' für detaillierte Beendigung aus${NC}"
else
    echo -e "${GREEN}✅ Alle wichtigen Ports sind frei${NC}"
fi 