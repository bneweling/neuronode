#!/bin/bash
# start-backend.sh - Startet nur Backend Services (Docker + API)

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

# Logs-Verzeichnis erstellen
mkdir -p "$ROOT_DIR/logs"

echo -e "${BLUE}🚀 Starte Neuronode Backend...${NC}"
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

# 1. Docker Services starten
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

# 2. Backend API Server starten
echo -e "${BLUE}🌐 Starte Backend API Server...${NC}"

# Prüfe ob Virtual Environment existiert
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${RED}❌ Backend Virtual Environment nicht gefunden. Führen Sie setup.sh aus.${NC}"
    exit 1
fi

# Prüfe ob API bereits läuft
if [ -f "$BACKEND_DIR/.api.pid" ]; then
    OLD_PID=$(cat "$BACKEND_DIR/.api.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  API läuft bereits (PID: $OLD_PID)${NC}"
        echo "Stoppe alte API-Instanz..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f "$BACKEND_DIR/.api.pid"
fi

# Aktiviere Virtual Environment und starte API
cd "$BACKEND_DIR"
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Prüfe ob API-Module verfügbar sind
python -c "from src.api.main import app" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API-Module nicht verfügbar. Überprüfen Sie die Installation.${NC}"
    exit 1
fi

# API im Hintergrund starten
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8080 > "$ROOT_DIR/logs/api.log" 2>&1 &
API_PID=$!
echo $API_PID > "$BACKEND_DIR/.api.pid"

# Kurz warten und prüfen ob API gestartet ist
sleep 3
if ps -p $API_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API Server gestartet (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ Backend API Server konnte nicht gestartet werden${NC}"
    echo "Siehe logs/api.log für Details"
    exit 1
fi

# Teste API-Verbindung
echo -n "Teste API-Verbindung"
for i in {1..10}; do
    if curl -s http://localhost:8080/docs > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Backend API erreichbar${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 10 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Backend API braucht länger zum Starten${NC}"
    fi
done

# Zurück zum Root-Verzeichnis
cd "$ROOT_DIR"

echo ""
echo -e "${GREEN}🎉 Neuronode Backend erfolgreich gestartet!${NC}"
echo ""
echo -e "${BLUE}📋 Verfügbare Services:${NC}"
echo "   🌐 Backend API: http://localhost:8080"
echo "   📚 API Docs: http://localhost:8080/docs"
echo "   🗃️  Neo4j Browser: http://localhost:7474 (neo4j/password)"
echo "   📊 ChromaDB: http://localhost:8000"
echo ""
echo -e "${BLUE}🔧 Verwendung:${NC}"
echo "   cd neuronode-backend && ./ki-cli.sh --help"
echo "   cd neuronode-backend && ./ki-cli.sh query \"Ihre Frage\""
echo ""
echo -e "${BLUE}📊 Logs:${NC}"
echo "   Backend: logs/api.log"
echo ""
echo -e "${YELLOW}🛑 Stoppen mit: ./stop-all.sh${NC}" 