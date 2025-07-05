#!/bin/bash
# start-frontend.sh - Startet nur das Frontend

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Basis-Verzeichnisse
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/neuronode-webapp"

# Logs-Verzeichnis erstellen
mkdir -p "$ROOT_DIR/logs"

echo -e "${BLUE}🚀 Starte Neuronode Frontend...${NC}"
echo -e "${CYAN}Root: $ROOT_DIR${NC}"
echo -e "${CYAN}Frontend: $FRONTEND_DIR${NC}"
echo ""

# Prüfe Frontend-Verzeichnis
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend-Verzeichnis nicht gefunden: $FRONTEND_DIR${NC}"
    exit 1
fi

# Prüfe ob node_modules existiert
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${RED}❌ Frontend node_modules nicht gefunden. Führen Sie setup.sh aus.${NC}"
    exit 1
fi

# Prüfe ob Frontend bereits läuft
if [ -f "$FRONTEND_DIR/.next.pid" ]; then
    OLD_PID=$(cat "$FRONTEND_DIR/.next.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Frontend läuft bereits (PID: $OLD_PID)${NC}"
        echo "Stoppe alte Frontend-Instanz..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f "$FRONTEND_DIR/.next.pid"
fi

# Frontend im Hintergrund starten
echo -e "${BLUE}🎨 Starte Frontend...${NC}"
cd "$FRONTEND_DIR"
nohup npm run dev > "$ROOT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_DIR/.next.pid"

# Kurz warten und prüfen ob Frontend gestartet ist
sleep 5
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend gestartet (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Frontend konnte nicht gestartet werden${NC}"
    echo "Siehe logs/frontend.log für Details"
    exit 1
fi

# Teste Frontend-Verbindung
echo -n "Teste Frontend-Verbindung"
for i in {1..15}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Frontend erreichbar${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 15 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Frontend braucht länger zum Starten${NC}"
    fi
done

# Zurück zum Root-Verzeichnis
cd "$ROOT_DIR"

echo ""
echo -e "${GREEN}🎉 Neuronode Frontend erfolgreich gestartet!${NC}"
echo ""
echo -e "${BLUE}📋 Verfügbare Services:${NC}"
echo "   🎨 Frontend: http://localhost:3000"
echo ""
echo -e "${BLUE}🔧 Verwendung:${NC}"
echo "   Öffnen Sie http://localhost:3000 im Browser"
echo ""
echo -e "${BLUE}📊 Logs:${NC}"
echo "   Frontend: logs/frontend.log"
echo ""
echo -e "${YELLOW}⚠️  Hinweis: Das Backend muss separat gestartet werden!${NC}"
echo -e "${YELLOW}🛑 Stoppen mit: ./stop-all.sh${NC}" 