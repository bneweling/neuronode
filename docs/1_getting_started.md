# 🚀 **Getting Started - Lokale Entwicklung**

## **Ziel: System in unter 30 Minuten lauffähig**

Dieser Guide führt neue Entwickler durch den kompletten Setup-Prozess für die lokale Entwicklungsumgebung des Neuronodes.

---

## 📋 **Voraussetzungen**

### **Erforderliche Software:**
```bash
# Prüfe deine aktuellen Versionen:
node --version          # >= 18.0.0
npm --version           # >= 9.0.0
docker --version        # >= 20.0.0
docker-compose --version # >= 2.0.0
python3 --version       # >= 3.11.0
git --version           # >= 2.30.0
```

### **Systemanforderungen:**
- **RAM:** Mindestens 8GB (16GB empfohlen)
- **Speicher:** 5GB freier Speicherplatz
- **Ports:** 3000, 4000, 5432, 6379, 8000, 8001 verfügbar

---

## ⚡ **Quick Start (5 Minuten)**

```bash
# 1. Repository klonen
git clone [REPOSITORY_URL]
cd neuronode-main

# 2. System starten (alle Services)
./manage.sh up

# 3. Warten bis Services bereit sind (ca. 2 Minuten)
./manage.sh health

# 4. Browser öffnen
open http://localhost:3000
```

**Das war's! Das System sollte jetzt laufen.**

---

## 🔧 **Detaillierter Setup (falls Quick Start nicht funktioniert)**

### **Schritt 1: Environment Setup**

```bash
# Backend Environment
cd neuronode
cp .env.example .env

# Wichtige Environment-Variablen setzen:
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key
# LITELLM_MASTER_KEY=your_litellm_key
```

### **Schritt 2: Docker Services starten**

```bash
# PostgreSQL & Redis starten
docker-compose up -d postgres redis

# Warten bis Datenbanken bereit sind
./manage.sh health
```

### **Schritt 3: Backend Services**

```bash
# Python Environment
cd neuronode
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# LiteLLM Proxy starten
./manage.sh litellm:start

# Backend API starten
./manage.sh backend:start
```

### **Schritt 4: Frontend**

```bash
# Frontend Dependencies
cd neuronode-webapp
npm install --legacy-peer-deps

# Development Server starten
npm run dev
```

---

## 🧪 **System validieren**

### **Health Checks:**
```bash
# Alle Services prüfen
./manage.sh health

# Erwartete Ausgabe:
# ✅ Frontend: http://localhost:3000 - OK
# ✅ Backend: http://localhost:8000 - OK  
# ✅ LiteLLM: http://localhost:4000 - OK
# ✅ PostgreSQL: localhost:5432 - OK
# ✅ Redis: localhost:6379 - OK
```

### **E2E Tests ausführen:**
```bash
# Vollständige Systemvalidierung
./manage.sh test:e2e

# Erwartete Ausgabe:
# ✅ 14/14 Tests passed
# ✅ All browsers: Chrome, Firefox, Safari, Edge
# ✅ Performance: All benchmarks exceeded
```

---

## 🎯 **Erste Schritte**

### **1. System erkunden:**
- **Frontend:** http://localhost:3000
- **API Dokumentation:** http://localhost:8000/docs
- **LiteLLM UI:** http://localhost:4000/ui

### **2. Test-Dokument hochladen:**
```bash
# Beispiel-Dokument aus den Fixtures verwenden
cp tests/fixtures/test-document.pdf ~/Desktop/
# Dann via Web-UI hochladen
```

### **3. Chat-Funktion testen:**
```bash
# Gehe zu http://localhost:3000/chat
# Frage: "Was sind die wichtigsten Erkenntnisse aus dem Dokument?"
```

### **4. Graph-Visualisierung:**
```bash
# Gehe zu http://localhost:3000/graph
# Interaktive Wissensgraph-Visualisierung
```

---

## 🛠️ **Development Workflow**

### **Code-Änderungen:**
```bash
# Frontend (Hot Reload)
cd neuronode-webapp
# Änderungen werden automatisch übernommen

# Backend (Neustart erforderlich)
cd neuronode
# Nach Änderungen:
./manage.sh backend:restart
```

### **Debugging:**
```bash
# Logs anzeigen
./manage.sh logs

# Einzelne Services debuggen
./manage.sh logs:frontend
./manage.sh logs:backend
./manage.sh logs:litellm
```

### **Tests während Development:**
```bash
# Frontend Tests
cd neuronode-webapp
npm test

# Backend Tests  
cd neuronode
python -m pytest tests/

# E2E Tests (vollständig)
./manage.sh test:e2e
```

---

## 🔧 **Häufige Management-Commands**

```bash
# System Management
./manage.sh up              # Alles starten
./manage.sh down            # Alles stoppen
./manage.sh restart         # Neustart
./manage.sh status          # Status anzeigen

# Development
./manage.sh logs            # Alle Logs
./manage.sh clean           # Cleanup
./manage.sh format          # Code formatieren
./manage.sh lint            # Code-Qualität prüfen

# Database
./manage.sh db:reset        # Datenbank zurücksetzen
./manage.sh db:migrate      # Migrationen ausführen
./manage.sh db:seed         # Test-Daten laden
```

---

## 🆘 **Troubleshooting**

### **Häufige Probleme:**

**1. Ports bereits belegt:**
```bash
# Prüfe welche Ports belegt sind
lsof -i :3000 -i :4000 -i :5432 -i :6379 -i :8000 -i :8001

# Stoppe andere Services falls nötig
./manage.sh down
```

**2. Docker-Probleme:**
```bash
# Docker neu starten
docker system prune -a
./manage.sh up
```

**3. Node/NPM-Probleme:**
```bash
# Node modules neu installieren
cd neuronode-webapp
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**4. Python-Environment-Probleme:**
```bash
# Virtual Environment neu erstellen
cd neuronode
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**5. Services starten nicht:**
```bash
# Health Check Details
./manage.sh health --verbose

# Einzelne Services manuell starten
./manage.sh backend:start --debug
./manage.sh frontend:start --debug
```

---

## 📚 **Nächste Schritte**

Nach erfolgreichem Setup:

1. **Architektur verstehen:** Lese [2_architecture.md](2_architecture.md)
2. **Testing-Strategien:** Lese [3_testing_strategy.md](3_testing_strategy.md)
3. **Code-Basis erkunden:** 
   - Frontend: `neuronode-webapp/src/`
   - Backend: `neuronode/src/`
4. **Beitragen:** Siehe `CONTRIBUTING.md` für Development-Richtlinien

---

## ✅ **Erfolg-Checkliste**

- [ ] Alle Services laufen (./manage.sh health)
- [ ] Frontend erreichbar (http://localhost:3000)
- [ ] Backend API erreichbar (http://localhost:8000/docs)
- [ ] LiteLLM UI erreichbar (http://localhost:4000/ui)
- [ ] Test-Dokument hochgeladen
- [ ] Chat-Funktion getestet
- [ ] Graph-Visualisierung funktioniert
- [ ] E2E Tests bestanden (./manage.sh test:e2e)

---

**🎉 Herzlichen Glückwunsch! Du hast das Neuronode erfolgreich lokal aufgesetzt.**

*Geschätzte Setup-Zeit: 15-30 Minuten*  
*Bei Problemen: Siehe [6_troubleshooting.md](6_troubleshooting.md)* 