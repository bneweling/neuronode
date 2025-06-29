# 🆘 **Troubleshooting & Problemlösung**

## **Systematische Problemdiagnose**

Dieses Dokument hilft bei der schnellen Lösung häufiger Probleme im KI-Wissenssystem.

---

## 🔍 **Erste Diagnose**

### **System-Status prüfen:**
```bash
# Umfassende Systemprüfung
./manage.sh health

# Detaillierte Diagnose
./manage.sh status --verbose

# Alle Logs anzeigen
./manage.sh logs --tail=50
```

### **Service-Verfügbarkeit testen:**
```bash
# Frontend
curl -f http://localhost:3000 || echo "❌ Frontend nicht erreichbar"

# Backend API
curl -f http://localhost:8000/health || echo "❌ Backend nicht erreichbar"

# LiteLLM Proxy
curl -f http://localhost:4000/health || echo "❌ LiteLLM nicht erreichbar"

# PostgreSQL
pg_isready -h localhost -p 5432 || echo "❌ PostgreSQL nicht erreichbar"

# Redis
redis-cli -h localhost -p 6379 ping || echo "❌ Redis nicht erreichbar"
```

---

## 🚨 **Häufige Probleme & Lösungen**

### **1. System startet nicht (./manage.sh up)**

**Symptom:** Services starten nicht oder crashen sofort

**Diagnose:**
```bash
# Prüfe verwendete Ports
lsof -i :3000 -i :4000 -i :5432 -i :6379 -i :8000 -i :8001

# Docker-Status prüfen
docker ps -a
docker-compose ps
```

**Lösungsansätze:**
```bash
# Lösung 1: Ports freigeben
sudo lsof -ti :3000 | sudo xargs kill -9
sudo lsof -ti :4000 | sudo xargs kill -9
# ... für alle anderen Ports

# Lösung 2: Docker komplett neu starten
./manage.sh down
docker system prune -a
./manage.sh up

# Lösung 3: Einzelne Services debuggen
./manage.sh backend:start --debug
./manage.sh frontend:start --debug
```

### **2. Frontend lädt nicht (White Screen)**

**Symptom:** Weiße Seite oder JavaScript-Fehler

**Diagnose:**
```bash
# Browser-Console prüfen (F12)
# Netzwerk-Tab prüfen auf 404/500 Fehler

# Frontend-Logs prüfen
./manage.sh logs:frontend
```

**Lösungsansätze:**
```bash
# Lösung 1: Dependencies neu installieren
cd ki-wissenssystem-webapp
rm -rf node_modules package-lock.json .next
npm install --legacy-peer-deps
npm run build

# Lösung 2: Port-Konflikt lösen
./manage.sh frontend:restart --port=3001

# Lösung 3: Environment-Variablen prüfen
cat ki-wissenssystem-webapp/.env.local
# NEXT_PUBLIC_API_URL sollte gesetzt sein
```

### **3. Backend API nicht erreichbar (HTTP 500/502)**

**Symptom:** API-Aufrufe schlagen fehl

**Diagnose:**
```bash
# Backend-Logs detailliert
./manage.sh logs:backend --tail=100

# Python-Fehler prüfen
cd ki-wissenssystem
source venv/bin/activate
python -c "import sys; print(sys.path)"
```

**Lösungsansätze:**
```bash
# Lösung 1: Python-Environment reparieren
cd ki-wissenssystem
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lösung 2: Datenbank-Migration
./manage.sh db:migrate
./manage.sh db:seed

# Lösung 3: Environment-Variablen validieren
cd ki-wissenssystem
cat .env
# Alle erforderlichen Keys gesetzt?
```

### **4. LiteLLM Proxy Probleme**

**Symptom:** Chat-Anfragen schlagen fehl, LLM-Responses fehlen

**Diagnose:**
```bash
# LiteLLM-Logs prüfen
./manage.sh logs:litellm

# Proxy-Konfiguration prüfen
curl http://localhost:4000/v1/models
```

**Lösungsansätze:**
```bash
# Lösung 1: API-Keys prüfen
cd ki-wissenssystem
grep -E "(OPENAI|ANTHROPIC|GOOGLE)_API_KEY" .env
# Keys korrekt gesetzt?

# Lösung 2: LiteLLM-Service neustarten
./manage.sh litellm:restart

# Lösung 3: Proxy-Konfiguration reparieren
./manage.sh litellm:reset
./manage.sh litellm:configure
```

### **5. Datenbank-Verbindungsprobleme**

**Symptom:** PostgreSQL/Redis-Verbindungsfehler

**Diagnose:**
```bash
# Database-Container prüfen
docker ps | grep postgres
docker ps | grep redis

# Verbindung testen
psql -h localhost -U postgres -d knowledge_system
redis-cli -h localhost ping
```

**Lösungsansätze:**
```bash
# Lösung 1: Container neustarten
docker-compose restart postgres redis

# Lösung 2: Volumes prüfen/reparieren
docker volume ls | grep ki-wissenssystem
./manage.sh db:reset

# Lösung 3: Ports prüfen
netstat -an | grep 5432
netstat -an | grep 6379
```

### **6. E2E Tests schlagen fehl**

**Symptom:** Playwright-Tests nicht erfolgreich

**Diagnose:**
```bash
# Test-Ausgabe detailliert
./manage.sh test:e2e --debug

# Browser-Installation prüfen
cd ki-wissenssystem-webapp
npx playwright install --with-deps
```

**Lösungsansätze:**
```bash
# Lösung 1: Browser-Dependencies installieren
npx playwright install chromium firefox webkit

# Lösung 2: Test-Environment reparieren
cd ki-wissenssystem-webapp
rm -rf test-results
npm test -- --headed

# Lösung 3: Mock-Services prüfen
./manage.sh test:e2e --use-mocks
```

---

## 🔧 **Erweiterte Diagnose-Tools**

### **System-Health Deep-Check:**
```bash
#!/bin/bash
# System-Health-Check Script

echo "🔍 SYSTEM DEEP HEALTH CHECK"
echo "=========================="

echo "1. Disk Space:"
df -h

echo -e "\n2. Memory Usage:"
free -h

echo -e "\n3. Docker Status:"
docker system df

echo -e "\n4. Process Status:"
ps aux | grep -E "(node|python|postgres|redis)" | head -10

echo -e "\n5. Network Ports:"
netstat -an | grep -E "(3000|4000|5432|6379|8000|8001)"

echo -e "\n6. Service Response Times:"
time curl -s http://localhost:3000 > /dev/null
time curl -s http://localhost:8000/health > /dev/null
time curl -s http://localhost:4000/health > /dev/null
```

### **Log-Analyse Tools:**
```bash
# Fehler-Pattern suchen
./manage.sh logs | grep -i error | tail -20

# Performance-Probleme identifizieren
./manage.sh logs | grep -E "(slow|timeout|memory)" | tail -10

# API-Request-Analyse
./manage.sh logs:backend | grep -E "POST|GET" | tail -20
```

---

## 📊 **Performance-Troubleshooting**

### **Frontend-Performance:**
```bash
# Bundle-Größe analysieren
cd ki-wissenssystem-webapp
npm run analyze

# Lighthouse-Audit
npx lighthouse http://localhost:3000

# Memory-Leaks debuggen
# Browser DevTools > Performance Tab
```

### **Backend-Performance:**
```bash
# Python-Profiling
cd ki-wissenssystem
pip install py-spy
py-spy top --pid $(pgrep -f "python.*main.py")

# Database-Performance
psql -h localhost -U postgres -d knowledge_system
\timing on
EXPLAIN ANALYZE SELECT * FROM documents LIMIT 10;
```

---

## 🎯 **Spezifische Szenarien**

### **Szenario 1: "Alles war gestern OK, heute geht nichts"**
```bash
# Schritt 1: Git-Status prüfen
git status
git diff

# Schritt 2: System-Reset
./manage.sh down
./manage.sh clean
./manage.sh up

# Schritt 3: Cache leeren
docker system prune -a
rm -rf ki-wissenssystem-webapp/.next
rm -rf ki-wissenssystem-webapp/node_modules
```

### **Szenario 2: "Tests liefen, jetzt nicht mehr"**
```bash
# Schritt 1: Test-Environment zurücksetzen
cd ki-wissenssystem-webapp
rm -rf test-results
npx playwright install

# Schritt 2: Mock-Services überprüfen
./manage.sh test:validate-mocks

# Schritt 3: Einzelne Tests debuggen
npm test -- --headed --timeout=60000
```

### **Szenario 3: "Neuer Entwickler, System läuft nicht"**
```bash
# Schritt 1: Vollständige Neuinstallation
rm -rf node_modules venv .next
./manage.sh install:fresh

# Schritt 2: Environment-Setup
cp .env.example .env
# API-Keys konfigurieren

# Schritt 3: Guided Setup
./manage.sh setup:guided
```

---

## 🚨 **Emergency-Procedures**

### **Kompletter System-Reset:**
```bash
#!/bin/bash
echo "🚨 EMERGENCY RESET - ALLE DATEN GEHEN VERLOREN!"
read -p "Wirklich fortfahren? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    # Alle Services stoppen
    ./manage.sh down
    
    # Docker komplett bereinigen
    docker system prune -a -f
    docker volume prune -f
    
    # Node modules löschen
    rm -rf ki-wissenssystem-webapp/node_modules
    rm -rf ki-wissenssystem-webapp/.next
    
    # Python venv löschen
    rm -rf ki-wissenssystem/venv
    
    # Neustart
    ./manage.sh install:fresh
    ./manage.sh up
    
    echo "✅ System wurde komplett zurückgesetzt"
fi
```

### **Backup & Recovery:**
```bash
# Backup erstellen (vor Reset)
./manage.sh backup:create emergency-backup-$(date +%Y%m%d_%H%M%S)

# Backup wiederherstellen
./manage.sh backup:restore emergency-backup-20250629_143000
```

---

## 📞 **Support-Kontakte**

### **Interne Ressourcen:**
- **Dokumentation:** [docs/README.md](README.md)
- **Architecture:** [2_architecture.md](2_architecture.md)
- **API-Dokumentation:** http://localhost:8000/docs

### **Externe Ressourcen:**
- **LiteLLM Docs:** https://docs.litellm.ai/
- **Next.js Troubleshooting:** https://nextjs.org/docs/messages
- **Docker Debugging:** https://docs.docker.com/config/containers/logging/

---

## ✅ **Erfolgreiche Lösung validieren**

```bash
# Nach jeder Problemlösung:
./manage.sh health
./manage.sh test:e2e --quick
./manage.sh performance:check

# Erwartete Ausgabe:
# ✅ Alle Services: Gesund
# ✅ E2E Tests: Bestanden
# ✅ Performance: Innerhalb der Grenzwerte
```

---

**💡 Tipp:** Dokumentiere gelöste Probleme für das Team - füge neue Szenarien zu diesem Dokument hinzu!

*Letzte Aktualisierung: 2025-06-29* 