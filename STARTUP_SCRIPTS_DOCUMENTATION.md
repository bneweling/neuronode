# 🚀 Neuronode Startup Scripts Documentation

## Übersicht

Die Startup-Skripte wurden vollständig modernisiert und für den aktuellen Stand der Neuronode-Webapp optimiert. Alle veralteten Dependencies (wie Obsidian) wurden entfernt und durch moderne, funktionale Alternativen ersetzt.

## 📁 Skript-Struktur

```
neuronode/
├── setup.sh                              # 🔧 Haupt-Setup (Backend + Frontend)
├── start-all.sh                          # 🚀 Startet alle Services
├── start-backend.sh                      # 🔧 Nur Backend
├── start-frontend.sh                     # 🎨 Nur Frontend  
├── start-services.sh                     # 🐳 Nur Docker Services
├── stop-all.sh                           # 🛑 Stoppt alle Services (detailliert)
├── quick-stop.sh                         # ⚡ Schneller Stop ohne Bestätigung
├── scan-ports.sh                         # 🔍 Port-Scanner für alle Prozesse
├── neuronode-backend/
│   ├── scripts/setup/setup.sh            # 🔧 Backend-Setup
│   ├── start-api.sh                      # 🚀 Backend API
│   ├── start-services.sh                 # 🐳 Docker Services
│   └── ki-cli.sh                         # 🖥️ CLI Wrapper
└── neuronode-webapp/
    ├── setup.sh                          # 🎨 Frontend-Setup
    ├── start-dev.sh                      # 🚀 Development Server
    ├── build-prod.sh                     # 🏗️ Production Build
    └── run-tests.sh                      # 🧪 Test Suite
```

## 🔧 Setup-Skripte

### Haupt-Setup (`./setup.sh`)

**Zweck**: Vollständige Einrichtung des gesamten Neuronode-Systems

**Features**:
- ✅ Systemvoraussetzungen prüfen (Python 3.11+, Node.js 18+, Docker)
- ✅ Backend Virtual Environment einrichten
- ✅ Frontend Dependencies installieren
- ✅ Docker Services starten
- ✅ Datenbankschema migrieren
- ✅ Alle Startskripte generieren
- ✅ Umfassende Systemtests

**Verwendung**:
```bash
./setup.sh
```

### Backend-Setup (`neuronode-backend/scripts/setup/setup.sh`)

**Zweck**: Isolierte Backend-Einrichtung

**Features**:
- ✅ Python Virtual Environment
- ✅ Requirements Installation
- ✅ Docker Services (Neo4j, ChromaDB, Redis)
- ✅ Datenbankschema-Migration
- ✅ Environment-Konfiguration
- ✅ API-Startskripte

**Verwendung**:
```bash
cd neuronode-backend
./scripts/setup/setup.sh
```

### Frontend-Setup (`neuronode-webapp/setup.sh`)

**Zweck**: Isolierte Frontend-Einrichtung

**Features**:
- ✅ Node.js Dependencies
- ✅ Playwright Browser Installation
- ✅ TypeScript & ESLint Validation
- ✅ Environment-Konfiguration
- ✅ Test Suite Setup
- ✅ Development Tools

**Verwendung**:
```bash
cd neuronode-webapp
./setup.sh
```

## 🚀 Start-Skripte

### Alle Services (`./start-all.sh`)

**Zweck**: Startet das komplette System mit einem Befehl

**Startet**:
- 🐳 Docker Services (Neo4j, ChromaDB, Redis)
- 🔧 Backend API (Port 8080)
- 🎨 Frontend (Port 3000)

**Features**:
- ✅ Automatische Service-Abhängigkeiten
- ✅ Health Checks für alle Services
- ✅ Intelligente Pfad-Erkennung
- ✅ Hintergrund-Prozesse mit PID-Tracking
- ✅ Zentrale Logs im `logs/` Verzeichnis
- ✅ Umfassende Fehlerbehandlung

**Verwendung**:
```bash
./start-all.sh
```

### Backend-Only (`./start-backend.sh`)

**Zweck**: Nur Backend-Services starten

**Startet**:
- 🐳 Docker Services (Neo4j, ChromaDB, Redis)
- 🔧 Backend API (Port 8080)

**Features**:
- ✅ Health Checks für Docker Services
- ✅ API-Modul-Validierung
- ✅ PID-basiertes Prozess-Management
- ✅ Separate Logs für Backend

**Verwendung**:
```bash
./start-backend.sh
```

### Frontend-Only (`./start-frontend.sh`)

**Zweck**: Nur Frontend-Development-Server starten

**Features**:
- ✅ Node.js Dependencies prüfen
- ✅ PID-basiertes Prozess-Management
- ✅ Frontend-spezifische Logs
- ✅ Warnung wenn Backend nicht läuft

**Verwendung**:
```bash
./start-frontend.sh
```

### Services-Only (`./start-services.sh`)

**Zweck**: Nur Docker-Services starten

**Startet**:
- 🐳 Neo4j (Port 7474)
- 🐳 ChromaDB (Port 8000)
- 🐳 Redis (Port 6379)

**Features**:
- ✅ Umfassende Health Checks
- ✅ Einzelne Service-Validierung
- ✅ Empfehlungen für nächste Schritte

**Verwendung**:
```bash
./start-services.sh
```

## 🛑 Stop-Skripte

### Vollständiger Stop (`./stop-all.sh`)

**Zweck**: Alle Services ordnungsgemäß und detailliert stoppen

**Features**:
- 🔍 **Intelligente Prozess-Erkennung** - Findet alle Neuronode-Prozesse
- 🌐 **Port-basierte Suche** - Erkennt Prozesse auf beliebigen Ports
- 🐳 **Docker Integration** - Stoppt alle Container
- 🧹 **Cleanup** - Entfernt temporäre Dateien
- 📊 **Detaillierter Status-Report** - Zeigt verbleibende Prozesse
- ⚠️ **Sicherheitsabfrage** - Bestätigung vor Beendigung
- 🔄 **Graceful + Force Kill** - Versucht erst SIGTERM, dann SIGKILL

**Stoppt**:
- 🛑 Backend API Prozesse (uvicorn, Python)
- 🛑 Frontend Development Server (Next.js, Node.js)
- 🛑 Docker Services (Neo4j, ChromaDB, Redis)
- 🛑 CLI-Prozesse
- 🛑 Alle Neuronode-bezogenen Prozesse auf beliebigen Ports

**Verwendung**:
```bash
./stop-all.sh
```

### Schneller Stop (`./quick-stop.sh`)

**Zweck**: Schnelle Beendigung ohne Bestätigung und ausführliche Ausgaben

**Features**:
- ⚡ **Sofortige Ausführung** - Keine Bestätigung erforderlich
- 🎯 **Fokussiert** - Nur wesentliche Ausgaben
- 🔄 **Schnelle Beendigung** - Kurze Wartezeiten
- 📊 **Kompakter Status** - Nur wichtige Ports prüfen

**Verwendung**:
```bash
./quick-stop.sh
```

### Port-Scanner (`./scan-ports.sh`)

**Zweck**: Findet alle Neuronode-bezogenen Prozesse und ihre Ports

**Features**:
- 🔍 **Standard-Port-Check** - Prüft bekannte Ports (3000, 8080, 7474, etc.)
- 🔎 **Pattern-basierte Suche** - Findet Prozesse nach verschiedenen Mustern
- 🐳 **Docker-Integration** - Zeigt Container-Status
- 🌐 **Erweiterte Port-Suche** - Scannt große Port-Bereiche
- 📊 **Detaillierte Prozess-Info** - PID, Ports, Working Directory
- 📋 **Zusammenfassung** - Übersicht und Empfehlungen

**Verwendung**:
```bash
./scan-ports.sh
```

## 🎯 Spezialisierte Skripte

### Backend API (`neuronode-backend/start-api.sh`)

**Zweck**: Nur Backend API starten (ohne Docker Services)

**Verwendung**:
```bash
cd neuronode-backend
./start-api.sh
```

### CLI Wrapper (`neuronode-backend/ki-cli.sh`)

**Zweck**: Neuronode CLI mit korrekter Umgebung

**Verwendung**:
```bash
cd neuronode-backend
./ki-cli.sh --help
```

### Frontend Development (`neuronode-webapp/start-dev.sh`)

**Zweck**: Frontend mit Backend-Integration

**Features**:
- ✅ Backend-Verfügbarkeit prüfen
- ✅ API-Typen generieren
- ✅ Development Server starten

**Verwendung**:
```bash
cd neuronode-webapp
./start-dev.sh
```

### Production Build (`neuronode-webapp/build-prod.sh`)

**Zweck**: Optimierter Production Build

**Features**:
- ✅ API-Typen generieren
- ✅ Next.js Production Build
- ✅ Optimierungen & Minifizierung

**Verwendung**:
```bash
cd neuronode-webapp
./build-prod.sh
```

### Test Suite (`neuronode-webapp/run-tests.sh`)

**Zweck**: Alle Tests ausführen

**Testet**:
- 🧪 Unit Tests mit Coverage
- ♿ Accessibility Tests
- 🎭 E2E Tests

**Verwendung**:
```bash
cd neuronode-webapp
./run-tests.sh
```

## 🌐 Service URLs

Nach dem Start sind folgende Services verfügbar:

| Service | URL | Beschreibung |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | Next.js Webapp |
| Backend API | http://localhost:8080 | FastAPI Server |
| API Docs | http://localhost:8080/docs | OpenAPI Dokumentation |
| Neo4j | http://localhost:7474 | Graph Database (neo4j/password) |
| ChromaDB | http://localhost:8000 | Vector Database |
| Redis | localhost:6379 | Cache & Session Store |

## 🔄 Typische Workflows

### Erstmaliges Setup

```bash
# 1. Komplettes System einrichten
./setup.sh

# 2. API-Keys konfigurieren
nano neuronode-backend/.env

# 3. System starten
./start-all.sh
```

### Entwicklung

```bash
# Backend entwickeln
./start-backend.sh

# Frontend entwickeln (separates Terminal)
./start-frontend.sh

# Tests ausführen
cd neuronode-webapp && ./run-tests.sh
```

### Production Deployment

```bash
# Build erstellen
cd neuronode-webapp && ./build-prod.sh

# Production Server starten
npm start
```

### Debugging & Troubleshooting

```bash
# Alle laufenden Prozesse anzeigen
./scan-ports.sh

# Schnell alle Services stoppen
./quick-stop.sh

# Detailliert alle Services stoppen
./stop-all.sh

# System neu starten
./start-all.sh
```

## 🚫 Entfernte veraltete Features

Die folgenden veralteten Dependencies wurden entfernt:

- ❌ **Obsidian Plugin Integration** - Deprecated für das Projekt
- ❌ **Legacy Model Configurations** - Durch MODEL_PROFILE ersetzt
- ❌ **Protobuf Workarounds** - Nicht mehr benötigt
- ❌ **Hardcoded Plugin Paths** - Nicht mehr relevant
- ❌ **Manual Node.js Setup** - Automatisiert durch Homebrew

## 🔧 Technische Verbesserungen

### Backend Setup
- ✅ Python 3.11+ & 3.12 Support
- ✅ Moderne pip/setuptools/wheel Installation
- ✅ Robuste Health Checks
- ✅ Verbesserte Error Handling
- ✅ Automatische Environment-Erstellung

### Frontend Setup
- ✅ Node.js 18+ Requirement
- ✅ Playwright Browser Installation
- ✅ TypeScript & ESLint Validation
- ✅ Comprehensive Testing Setup
- ✅ Environment Configuration

### Stop-Skripte
- ✅ **Intelligente Prozess-Erkennung** - Findet Prozesse auf beliebigen Ports
- ✅ **Graceful Shutdown** - SIGTERM vor SIGKILL
- ✅ **Pattern-basierte Suche** - Verschiedene Suchstrategien
- ✅ **Docker Integration** - Automatisches Container-Management
- ✅ **Cleanup-Funktionen** - Temporäre Dateien entfernen
- ✅ **Status-Reporting** - Detaillierte Übersicht nach dem Stoppen

### Allgemeine Verbesserungen
- ✅ Farbige, benutzerfreundliche Ausgabe
- ✅ Detaillierte Logging
- ✅ Parallele Service-Starts
- ✅ Graceful Shutdown Handling
- ✅ Umfassende Dokumentation

## 📋 Fehlerbehebung

### Häufige Probleme

**Problem**: `Docker Services starten nicht`
```bash
# Lösung: Docker Desktop starten
open -a Docker
./start-services.sh
```

**Problem**: `API-Typen können nicht generiert werden`
```bash
# Lösung: Backend zuerst starten
./start-backend.sh
# In neuem Terminal:
cd neuronode-webapp && npm run generate:api-types
```

**Problem**: `Python Virtual Environment Fehler`
```bash
# Lösung: Virtual Environment neu erstellen
cd neuronode-backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: `Prozesse laufen noch nach dem Stoppen`
```bash
# Lösung: Detaillierte Analyse und Beendigung
./scan-ports.sh       # Prozesse finden
./stop-all.sh         # Vollständige Beendigung
```

**Problem**: `Unbekannte Ports belegt`
```bash
# Lösung: Port-Scanner verwenden
./scan-ports.sh       # Alle Ports und Prozesse anzeigen
```

### Stop-Skript Strategien

**Normale Beendigung:**
```bash
./stop-all.sh         # Mit Bestätigung und Details
```

**Schnelle Beendigung:**
```bash
./quick-stop.sh       # Ohne Bestätigung, minimal
```

**Analyse vor Beendigung:**
```bash
./scan-ports.sh       # Erst analysieren
./stop-all.sh         # Dann detailliert stoppen
```

### Logs & Debugging

- **Setup-Logs**: `setup.log` in jeweiligem Verzeichnis
- **Backend-Logs**: Console Output von uvicorn
- **Frontend-Logs**: Next.js Console Output
- **Docker-Logs**: `docker-compose logs`
- **Port-Analyse**: `./scan-ports.sh`

## 🎉 Fazit

Die modernisierten Startup-Skripte bieten:

- 🚀 **Einfache Bedienung** - Ein Befehl startet das gesamte System
- 🔧 **Modularer Aufbau** - Einzelne Services können isoliert gestartet werden
- 🛡️ **Robuste Fehlerbehandlung** - Umfassende Validierung und Health Checks
- 📱 **Moderne Dependencies** - Aktuelle Versionen ohne veraltete Komponenten
- 🎯 **Entwicklerfreundlich** - Klare Ausgaben und detaillierte Dokumentation
- 🛑 **Intelligente Beendigung** - Findet und stoppt alle Prozesse auf beliebigen Ports
- 🔍 **Umfassende Analyse** - Port-Scanner für vollständige Übersicht

Das System ist jetzt bereit für moderne Entwicklungsworkflows und Production-Deployments! 