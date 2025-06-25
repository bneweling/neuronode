#!/bin/bash
# stop-all.sh - Stoppt alle Services

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stoppe KI-Wissenssystem...${NC}"

# API Server stoppen
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "Stoppe API Server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
        
        # Warte bis Prozess beendet ist
        for i in {1..10}; do
            if ! ps -p $API_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # Force kill falls nötig
        if ps -p $API_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Erzwinge Beendigung der API...${NC}"
            kill -9 $API_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ API Server gestoppt${NC}"
    else
        echo -e "${YELLOW}⚠️  API Server war nicht aktiv${NC}"
    fi
    rm -f .api.pid
else
    echo -e "${YELLOW}⚠️  Keine API PID-Datei gefunden${NC}"
fi

# Docker Services stoppen
echo "Stoppe Docker Services..."
docker-compose down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker Services gestoppt${NC}"
else
    echo -e "${RED}❌ Fehler beim Stoppen der Docker Services${NC}"
fi

echo -e "${GREEN}🎉 System gestoppt!${NC}"
