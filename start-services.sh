#!/bin/bash
# start-services.sh - Startet nur die Docker Services (Neo4j, ChromaDB, Redis)

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Basis-Verzeichnisse
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/neuronode-backend"

echo -e "${BLUE}🚀 Starte Neuronode Docker Services...${NC}"
echo -e "${CYAN}Root: $ROOT_DIR${NC}"
echo -e "${CYAN}Backend: $BACKEND_DIR${NC}"
echo ""

# Prüfe Backend-Verzeichnis
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend-Verzeichnis nicht gefunden: $BACKEND_DIR${NC}"
    exit 1
fi

# Prüfe ob Docker läuft
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker läuft nicht. Bitte Docker Desktop starten.${NC}"
    exit 1
fi

# Docker Services starten
echo -e "${BLUE}📦 Starte Docker Services...${NC}"
cd "$BACKEND_DIR"
docker-compose up -d neo4j chromadb redis

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Starten der Docker Services${NC}"
    exit 1
fi

# Warte auf Services mit Health-Checks
echo -e "${YELLOW}⏳ Warte auf Service-Bereitschaft...${NC}"

# Neo4j Health Check
echo -n "Warte auf Neo4j"
for i in {1..30}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Neo4j bereit${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Neo4j braucht länger als erwartet${NC}"
    fi
done

# ChromaDB Health Check
echo -n "Warte auf ChromaDB"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ ChromaDB bereit${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  ChromaDB braucht länger als erwartet${NC}"
    fi
done

# Redis Health Check
echo -n "Warte auf Redis"
for i in {1..15}; do
    if redis-cli -p 6379 ping > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Redis bereit${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 15 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Redis braucht länger als erwartet${NC}"
    fi
done

# Zurück zum Root-Verzeichnis
cd "$ROOT_DIR"

echo ""
echo -e "${GREEN}🎉 Docker Services erfolgreich gestartet!${NC}"
echo ""
echo -e "${BLUE}📋 Verfügbare Services:${NC}"
echo "   🗃️  Neo4j Browser: http://localhost:7474 (neo4j/password)"
echo "   📊 ChromaDB: http://localhost:8000"
echo "   🔴 Redis: localhost:6379"
echo ""
echo -e "${BLUE}🔧 Nächste Schritte:${NC}"
echo "   ./start-backend.sh    # Backend API starten"
echo "   ./start-frontend.sh   # Frontend starten"
echo "   ./start-all.sh        # Alles zusammen starten"
echo ""
echo -e "${YELLOW}🛑 Stoppen mit: ./stop-all.sh${NC}" 