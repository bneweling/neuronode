# 🛑 Neuronode Stop Scripts

## Schnelle Übersicht

### 🔍 Analyse
```bash
./scan-ports.sh          # Alle Prozesse und Ports anzeigen
```

### ⚡ Schneller Stop
```bash
./quick-stop.sh          # Sofortige Beendigung ohne Bestätigung
```

### 🛑 Vollständiger Stop
```bash
./stop-all.sh            # Detaillierte Beendigung mit Bestätigung
```

## Features

### `scan-ports.sh` 🔍
- ✅ Findet alle Neuronode-Prozesse auf beliebigen Ports
- ✅ Zeigt Standard-Ports (3000, 8080, 7474, etc.)
- ✅ Docker Container Status
- ✅ Detaillierte Prozess-Informationen
- ✅ Port-Range Scanning
- ✅ Empfehlungen für weitere Schritte

### `quick-stop.sh` ⚡
- ✅ Keine Bestätigung erforderlich
- ✅ Schnelle Ausführung (< 10 Sekunden)
- ✅ Stoppt alle wichtigen Services
- ✅ Kompakter Status-Report
- ✅ Ideal für Entwicklung

### `stop-all.sh` 🛑
- ✅ Intelligente Prozess-Erkennung
- ✅ Graceful Shutdown (SIGTERM → SIGKILL)
- ✅ Findet Prozesse auf allen Ports
- ✅ Docker Container Management
- ✅ Cleanup temporärer Dateien
- ✅ Detaillierter Status-Report
- ✅ Sicherheitsabfrage

## Typische Workflows

### Entwicklung
```bash
# Schnell stoppen zwischen Tests
./quick-stop.sh

# Neustart
./start-all.sh
```

### Debugging
```bash
# Erst analysieren
./scan-ports.sh

# Dann detailliert stoppen
./stop-all.sh
```

### Production
```bash
# Vollständige, sichere Beendigung
./stop-all.sh
```

## Was wird gestoppt?

### Backend
- uvicorn Prozesse (API Server)
- Python CLI Prozesse
- Alle Python-Prozesse mit "neuronode"

### Frontend  
- Next.js Development Server
- Next.js Production Server
- Node.js Prozesse im neuronode-webapp
- npm/npx Prozesse

### Docker
- Neo4j Container
- ChromaDB Container
- Redis Container
- Alle neuronode-* Container

### Ports
- **Standard**: 3000, 3001, 4000, 5000, 6379, 7474, 7687, 8000, 8080
- **Erweitert**: Alle Ports mit Neuronode-Prozessen

## Sicherheit

- ✅ Graceful Shutdown zuerst (SIGTERM)
- ✅ Force Kill nur wenn nötig (SIGKILL)
- ✅ Bestätigung bei vollständigem Stop
- ✅ Detaillierte Logs und Reports
- ✅ Keine Systemdienste betroffen 