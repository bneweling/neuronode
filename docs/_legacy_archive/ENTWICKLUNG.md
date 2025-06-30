# 🛠️ Neuronode - Entwicklungsguide

> **📚 Navigation**: [🏠 Hauptdokumentation](README.md) | [🌐 Web-App Guide](README-WEBAPP.md) | [📖 Dokumentationsübersicht](docs/README.md)

## ❓ **Code-Änderungen nach Setup**

Nach dem erfolgreichen Setup müssen **nicht alle Änderungen neu installiert werden**. Es hängt von der Art der Änderung ab:

## 🔄 **Automatische Code-Übernahme (Hot Reload)**

### ✅ **Python Backend - Sofort übernommen:**

```bash
# Diese Änderungen werden automatisch erkannt:
src/api/                    # API-Endpunkte
src/retrievers/             # Retriever-Logik  
src/orchestration/          # Orchestrierung
src/document_processing/    # Dokumentenverarbeitung
src/storage/               # Datenbankclients
src/config/                # Konfiguration
.env                       # Environment-Variablen
```

**Warum?** Die API läuft mit `uvicorn --reload`, was automatisch Python-Dateien überwacht.

### ✅ **Obsidian Plugin - Watch-Modus verfügbar:**

```bash
# Plugin im Entwicklungs-Modus starten:
cd obsidian-ki-plugin
npm run dev                # Automatisches Bauen bei Änderungen

# Dann in Obsidian: Cmd+R (Reload) nach Änderungen
```

## ❌ **Neuinstallation erforderlich**

### **Python Backend:**
- **Neue Pakete** in `requirements.txt`
- **Docker-Service-Änderungen** in `docker-compose.yml`
- **System-Dependencies** (z.B. neue Datenbanken)

### **Obsidian Plugin:**
- **Erste Installation** nach Code-Änderungen
- **Manifest-Änderungen** (`manifest.json`)
- **Neue Dependencies** in `package.json`

## 🚀 **Optimaler Entwicklungs-Workflow**

### **1. Einmaliges Setup:**
```bash
# Vollständige Installation
./setup.sh                 # macOS/Linux

# Plugin installieren  
./setup-obsidian.sh        # macOS/Linux
```

### **2. Entwicklungs-Modus starten:**
```bash
cd neuronode
./dev-mode.sh              # macOS/Linux - Interaktives Entwicklungs-Menü
```

### **3. Entwicklungs-Optionen:**

#### **Option A: Nur Backend-Entwicklung**
```bash
./dev-mode.sh → Option 1   # API mit Hot Reload (macOS/Linux)
# Code ändern → Automatisch übernommen! 🔥
```

#### **Option B: Nur Plugin-Entwicklung**
```bash
./dev-mode.sh → Option 2   # Plugin Watch-Modus (macOS/Linux)
# Code ändern → Automatisch gebaut → Cmd+R in Obsidian
```

#### **Option C: Full-Stack-Entwicklung**
```bash
# Terminal 1:
./dev-mode.sh → Option 1   # API Server (macOS/Linux)

# Terminal 2:  
./dev-mode.sh → Option 2   # Plugin Watch (macOS/Linux)
```

#### **Option D: Plugin-Features testen (NEU)**
```bash
./dev-mode.sh → Option 4   # Plugin-Features testen (macOS/Linux)
```

**Neue Plugin-Features verfügbar:**
- 📤 **Dokumentenupload** mit Drag & Drop Interface
- 🔍 **Echtzeit-Analyse** vor Upload mit Transparenz
- ⚙️ **Transparente Verarbeitung** mit Fortschrittsanzeige
- 💬 **Chat** mit automatischer Graph-Visualisierung
- 🕸️ **Interaktiver Wissensgraph** mit D3.js-Visualisierung

## 📝 **Entwicklungs-Beispiele**

### **Backend-Änderung (Hot Reload):**
```bash
# 1. API läuft bereits mit ./dev-mode.sh
# 2. Code ändern:
nano src/api/endpoints/auth.py

# 3. Speichern → Automatisch übernommen! ✅
# 4. Testen: http://localhost:8080/docs
```

### **Plugin-Änderung (Watch + Reload):**
```bash
# 1. Plugin Watch-Modus läuft
# 2. Code ändern:
nano obsidian-ki-plugin/src/components/ChatInterface.ts

# 3. Speichern → Automatisch gebaut ✅
# 4. In Obsidian: Cmd+R (Reload)
```

### **Neue Python-Bibliothek:**
```bash
# 1. Virtual Environment aktivieren
source venv/bin/activate

# 2. Paket installieren
pip install neue-bibliothek

# 3. Requirements aktualisieren
pip freeze | grep neue-bibliothek >> requirements.txt

# 4. Code verwenden → Hot Reload funktioniert ✅
```

### **Neue Plugin-Dependency:**
```bash
cd obsidian-ki-plugin

# 1. Dependency installieren
npm install neue-bibliothek

# 2. Plugin neu bauen
npm run build

# 3. Plugin neu installieren
../neuronode/setup-obsidian.sh

# 4. Obsidian neu starten
```

## 🔧 **Entwicklungs-Tools**

### **Backend-Debugging:**
```bash
# API-Logs in Echtzeit
tail -f neuronode/logs/api.log

# Docker-Service-Logs
docker-compose logs -f neo4j chromadb

# Python-Debugger
import pdb; pdb.set_trace()  # In Code einfügen
```

### **Plugin-Debugging:**
```bash
# Obsidian Developer Console
Cmd+Shift+I (macOS)

# Plugin-spezifische Logs
console.log("Debug:", data);  # In TypeScript-Code

# Hot Reload in Obsidian
Cmd+R (macOS)
```

## 🌐 **Entwicklungs-URLs**

```bash
# Nach ./dev-mode.sh sind verfügbar:
API Dokumentation:  http://localhost:8080/docs
API Health Check:   http://localhost:8080/health
Neo4j Browser:      http://localhost:7474
ChromaDB API:       http://localhost:8000
```

## 📦 **Service-Management**

### **Services starten/stoppen:**
```bash
# Alle Services starten
./start-all.sh

# Nur Docker Services
./start-services.sh

# Services stoppen  
./stop-all.sh

# Service-Status prüfen
docker-compose ps
```

### **Einzelne Services neu starten:**
```bash
# Neo4j neu starten
docker-compose restart neo4j

# ChromaDB neu starten  
docker-compose restart chromadb

# API neu starten (falls nicht im Watch-Modus)
pkill -f uvicorn && ./start-api.sh
```

## 🐛 **Häufige Entwicklungsprobleme**

### **"Module not found" nach neuer Bibliothek:**
```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Paket installieren
pip install fehlende-bibliothek

# API neu starten
./dev-mode.sh → Option 1
```

### **Plugin lädt nicht nach Änderungen:**
```bash
# 1. Plugin neu bauen
cd obsidian-ki-plugin && npm run build

# 2. Plugin neu installieren
cd ../neuronode && ./setup-obsidian.sh

# 3. Obsidian komplett neu starten
```

### **Docker Services anhalten:**
```bash
# Services laufen nicht
docker-compose up -d

# Ports bereits belegt
docker-compose down && docker-compose up -d

# Volumes zurücksetzen
docker-compose down -v && docker-compose up -d
```

## 🎯 **Produktions-Deployment**

### **Vor dem Deployment:**
```bash
# 1. Tests ausführen
pytest tests/

# 2. Plugin final bauen
cd obsidian-ki-plugin && npm run build

# 3. Requirements aktualisieren
pip freeze > requirements.txt

# 4. Git committen
git add . && git commit -m "Neue Features"
```

---

**Fazit: Nach dem Setup sind die meisten Code-Änderungen automatisch verfügbar! 🔥** 