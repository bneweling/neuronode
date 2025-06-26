# KI-Wissenssystem - Komplette Neuinstallation 2025

## 🚨 **Aktualisierungsstatus (Januar 2025)**

**Setup-Skripte:** ✅ **AKTUALISIERT** - Bereit für Neuinstallation  
**Abhängigkeiten:** ✅ **AKTUELL** - Gemini 2.5 API integriert  
**Letzte Überprüfung:** Januar 2025

---

## 🚀 **Schnellstart (Empfohlen)**

### 1. **Automatische Installation:**
```bash
cd ki-wissenssystem
./setup.sh
```

**Das Setup-Skript erledigt automatisch:**
- ✅ Installiert alle Python-Abhängigkeiten
- ✅ Aktualisiert Gemini API-Integration (`langchain-google-genai==2.1.5`)
- ✅ Konfiguriert Pydantic Settings (`pydantic-settings==2.10.1`)
- ✅ Erstellt aktuelle `.env` Vorlage mit Modellprofilen
- ✅ Startet Docker Services (Neo4j, ChromaDB)
- ✅ Testet Gemini API-Integration
- ✅ Erstellt Startskripte

### 2. **API-Keys konfigurieren:**
```bash
nano .env
```

**Minimal erforderlich für Tests:**
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL_PROFILE=gemini_only
```

### 3. **System starten:**
```bash
./start-services.sh  # Docker Services
./start-api.sh       # API Server
```

### 4. **Webapp installieren:**
```bash
cd ../ki-wissenssystem-webapp
npm install
npm run dev
```

---

## 🔧 **Manuelle Installation (bei Problemen)**

### **Schritt 1: Voraussetzungen**
```bash
# macOS
brew install python@3.11 node docker

# Prüfen
python3.11 --version
node --version
docker --version
```

### **Schritt 2: Backend Setup**
```bash
cd ki-wissenssystem

# Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt

# Kritische Updates (2025)
pip install --upgrade langchain-google-genai==2.1.5
pip install --upgrade pydantic-settings==2.10.1
```

### **Schritt 3: Konfiguration**
```bash
# .env erstellen
cp env.example .env

# Bearbeiten
nano .env
```

**Aktuelle .env Vorlage (2025):**
```env
# API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Model Profile Configuration
MODEL_PROFILE=gemini_only  # Für Tests: nur Google API erforderlich
```

### **Schritt 4: Services starten**
```bash
# Docker Services
docker-compose up -d neo4j chromadb

# API testen
python scripts/setup/test-gemini-api.py

# API Server starten
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
```

### **Schritt 5: Frontend Setup**
```bash
cd ../ki-wissenssystem-webapp

# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Produktions-Build
npm run build
```

---

## 🎛️ **Modellprofile konfigurieren**

### **Verfügbare Profile (2025):**

#### **1. Gemini Only (Empfohlen für Tests):**
```env
MODEL_PROFILE=gemini_only
```
- **APIs:** Nur Google
- **Kosten:** Niedrig
- **Performance:** Hoch (Gemini 2.5)

#### **2. Premium (Produktiv):**
```env
MODEL_PROFILE=premium
```
- **APIs:** Google + OpenAI + Anthropic
- **Kosten:** Hoch
- **Performance:** Maximal

#### **3. Cost-Effective (Budget):**
```env
MODEL_PROFILE=cost_effective
```
- **APIs:** Google + OpenAI + Anthropic
- **Kosten:** Niedrig
- **Performance:** Gut

### **Profil wechseln:**
```bash
python3 scripts/system/switch-model-profile.py --list
python3 scripts/system/switch-model-profile.py gemini_only
```

---

## 🧪 **Testing & Verifikation**

### **1. Backend testen:**
```bash
cd ki-wissenssystem

# Gemini API
python scripts/setup/test-gemini-api.py

# System-Health
./ki-cli.sh --help

# Services prüfen
docker-compose ps
```

### **2. Frontend testen:**
```bash
cd ki-wissenssystem-webapp

# Development Server
npm run dev
# ➜ http://localhost:3000

# Build testen
npm run build
```

### **3. Integration testen:**
```bash
# API Dokumentation
curl http://localhost:8080/docs

# Neo4j Interface
open http://localhost:7474
```

---

## 📁 **Vollständige Verzeichnisstruktur**

```
ki-wissenssystem-main/
├── ki-wissenssystem/          # Backend (Python)
│   ├── setup.sh ✅            # Aktualisiert 2025
│   ├── requirements.txt ✅     # Gemini 2.5 ready
│   ├── .env.example ✅        # Aktuelle Vorlage
│   └── src/
├── ki-wissenssystem-webapp/   # Frontend (Next.js)
│   ├── package.json
│   └── src/
└── obsidian-ki-plugin/        # Obsidian Plugin
    ├── package.json
    └── src/
```

---

## 🚨 **Häufige Probleme & Lösungen**

### **Problem: "No module named 'langchain_google_genai'"**
```bash
pip install --upgrade langchain-google-genai==2.1.5
```

### **Problem: "No module named 'pydantic_settings'"**
```bash
pip install --upgrade pydantic-settings==2.10.1
```

### **Problem: Gemini API-Fehler**
```bash
# API-Key prüfen
python scripts/setup/test-gemini-api.py

# Profil auf gemini_only setzen
echo "MODEL_PROFILE=gemini_only" >> .env
```

### **Problem: Docker Services**
```bash
# Services neustarten
docker-compose down
docker-compose up -d

# Logs prüfen
docker-compose logs
```

---

## ✅ **Erfolgreich installiert wenn:**

- [ ] **Gemini API Test:** `python scripts/setup/test-gemini-api.py` ✅
- [ ] **Backend API:** `http://localhost:8080/docs` erreichbar
- [ ] **Frontend:** `http://localhost:3000` erreichbar  
- [ ] **Neo4j:** `http://localhost:7474` erreichbar
- [ ] **Profile:** `python scripts/system/switch-model-profile.py --show`

---

## 🎯 **Empfohlene Reihenfolge für Neuinstallation:**

1. **✅ Setup-Skript ausführen:** `./setup.sh`
2. **✅ API-Keys eintragen:** `.env` bearbeiten
3. **✅ Gemini testen:** `python scripts/setup/test-gemini-api.py`
4. **✅ Backend starten:** `./start-api.sh`
5. **✅ Frontend installieren:** `cd ../ki-wissenssystem-webapp && npm install && npm run dev`

**Status:** 🟢 **PRODUKTIONSBEREIT** mit Gemini 2.5 API 