# 🧠 Neuronode - Enterprise Knowledge Management System

**Version:** 2.0  
**Status:** Produktionsreif  
**Letzte Aktualisierung:** Januar 2025

Neuronode ist ein enterprise-grade KI-gestütztes Wissensmanagementsystem, das strukturierte Graph-Datenbanken mit Vektor-Embeddings kombiniert, um sowohl semantische Suche als auch komplexe Beziehungsanalysen zu ermöglichen.

## 🚀 **ÜBERSICHT**

### **Was ist Neuronode?**

Neuronode transformiert unstrukturierte Dokumente in ein intelligentes, durchsuchbares Knowledge Graph. Das System nutzt moderne KI-Modelle über LiteLLM für:

- **Dokumentverarbeitung**: Multi-Format-Support (PDF, DOCX, TXT, XML, etc.)
- **Intelligente Extraktion**: Automatische Entitäts- und Beziehungserkennung
- **Hybrid-Suche**: Kombination aus semantischer Vektorsuche und Graph-Traversierung
- **Natürliche Sprache**: Chat-Interface für komplexe Wissensabfragen
- **Visualisierung**: Interaktive Knowledge Graph-Darstellung

### **Kernfeatures**

- ✅ **27 Smart-Alias AI-Modelle** über LiteLLM-Integration
- ✅ **Enterprise-Sicherheit** mit JWT, RBAC und Rate Limiting
- ✅ **Multi-Format-Dokumentenverarbeitung** 
- ✅ **Real-time Chat-Interface** mit Kontext-Awareness
- ✅ **Interaktive Graph-Visualisierung**
- ✅ **Umfassendes Testing** mit 100% E2E-Coverage
- ✅ **Performance-optimiert** für Enterprise-Workloads

## 📋 **SCHNELLSTART**

### **Systemanforderungen**
- Docker & Docker Compose
- Node.js 18+ (für Frontend-Entwicklung)
- 8GB RAM (minimum), 16GB empfohlen
- 50GB freier Speicherplatz

### **1. Repository klonen**
```bash
git clone <repository-url>
cd neuronode
```

### **2. Umgebung konfigurieren**
```bash
# API-Keys konfigurieren (erforderlich für Produktivbetrieb)
cp neuronode-backend/env.example neuronode-backend/.env

# API-Keys in .env eintragen:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
```

### **3. Services starten**
```bash
# Alle Services starten (Backend + LiteLLM + Datenbanken)
cd neuronode-backend
./manage.sh start

# Frontend starten (separates Terminal)
cd neuronode-webapp
npm install
npm run dev
```

### **4. System validieren**
```bash
# Health Checks
curl http://localhost:8001/health    # Backend API
curl http://localhost:4000/health    # LiteLLM Proxy
open http://localhost:3000           # Frontend
open http://localhost:4000/ui        # LiteLLM Admin UI
```

## 🏗️ **ARCHITEKTUR**

### **Service-Überblick**
```
Frontend (Next.js)     → http://localhost:3000
├── Backend API        → http://localhost:8001
├── LiteLLM Proxy      → http://localhost:4000
├── Neo4j Graph DB     → bolt://localhost:7687
├── ChromaDB Vectors   → http://localhost:8000
├── PostgreSQL         → localhost:5432
└── Redis Cache        → localhost:6379
```

### **Datenfluss**
1. **Upload**: Dokumente über Web-Interface hochladen
2. **Processing**: Automatische Klassifikation und Chunking
3. **Extraction**: KI-basierte Entitäts- und Beziehungserkennung
4. **Storage**: Hybrid-Speicherung in Graph- und Vector-Datenbank
5. **Query**: Natürliche Sprache → Hybrid Retrieval → KI-Antwort

## 🔧 **VERWENDUNG**

### **Dokumente hochladen**
1. Frontend öffnen: http://localhost:3000
2. "Upload" → Datei auswählen → Upload starten
3. Processing-Status verfolgen
4. Dokument in Knowledge Graph verfügbar

### **Wissen abfragen**
1. "Chat" → Natürliche Frage eingeben
2. System kombiniert Graph- und Vektor-Suche
3. KI generiert kontextuelle Antwort mit Quellen
4. Ergebnisse in Graph visualisieren

### **Graph erkunden**
1. "Graph" → Interaktive Visualisierung
2. Knoten und Beziehungen explorieren
3. Filter und Suchfunktionen nutzen
4. Export-Funktionen verfügbar

## 🧪 **TESTING**

### **E2E Tests ausführen**
```bash
# Vollständige E2E-Test-Suite
cd neuronode-webapp
npm run test:e2e

# Spezifische Test-Szenarien
npx playwright test user-journey-complete-workflow.spec.ts
npx playwright test performance-scalability.spec.ts
```

### **Backend Tests**
```bash
cd neuronode-backend
pytest tests/ -v --cov=src --cov-report=html
```

### **Test-Coverage**
- **Unit Tests**: 90%+ Coverage
- **Integration Tests**: 80%+ Coverage  
- **E2E Tests**: 100% Critical Path Coverage

## 📊 **MONITORING**

### **System Health**
```bash
# Service Status überprüfen
./manage.sh status

# Service Logs anzeigen
./manage.sh logs

# Performance Metriken
curl http://localhost:8001/metrics
```

### **LiteLLM Monitoring**
- **Admin UI**: http://localhost:4000/ui
- **Model Performance**: Real-time Analytics
- **Cost Tracking**: Token Usage & API Costs
- **Rate Limits**: Request Throttling Status

## 🔐 **SICHERHEIT**

### **Produktionseinstellungen**
```bash
# API-Keys niemals in Git committen
# Nur in .env oder Environment Variables

# LiteLLM Authentifizierung aktivieren
DISABLE_AUTH=false
UI_USERNAME=admin
UI_PASSWORD=secure-password-2025

# JWT-Konfiguration
JWT_SECRET_KEY=your-secure-secret
LITELLM_MASTER_KEY=sk-your-master-key
```

### **Sicherheitsfeatures**
- ✅ JWT-basierte Authentifizierung
- ✅ Role-Based Access Control (RBAC)
- ✅ API Rate Limiting
- ✅ Input Validation & Sanitization
- ✅ Audit Logging

## 🚀 **DEPLOYMENT**

### **Development**
```bash
./manage.sh start     # Lokale Entwicklung
npm run dev           # Frontend mit Hot-Reload
```

### **Production**
```bash
# Docker Compose für Production
docker-compose -f deployment/docker-compose.production.yml up -d

# Environment Variables konfigurieren
cp deployment/production-env.template .env
# API-Keys und Passwörter konfigurieren
```

### **Skalierung**
- **Horizontal**: Stateless Services, Load Balancing
- **Datenbank**: Neo4j Clustering, ChromaDB Partitionierung
- **Performance**: Redis Caching, Connection Pooling

## 📚 **DOKUMENTATION**

### **Vollständige Dokumentation**
- **[Getting Started](docs/1_getting_started.md)**: Detaillierte Installation
- **[Architektur](docs/2_architecture.md)**: System-Design und Komponenten
- **[Datenmodell](docs/2_data_model.md)**: Schema und Beziehungen
- **[Workflows](docs/3_workflows.md)**: Entwicklungs-Prozesse
- **[Deployment](docs/4_deployment.md)**: Production Setup
- **[Komponenten](docs/5_components.md)**: Feature-Details
- **[Testing](docs/7_enterprise_testing.md)**: Umfassende Test-Strategie
- **[Troubleshooting](docs/6_troubleshooting.md)**: Fehlerbehebung

### **API-Dokumentation**
- **Swagger UI**: http://localhost:8001/docs
- **Interactive API**: Vollständige Endpoint-Dokumentation
- **Authentication**: JWT-basierte API-Authentifizierung

## 🛠️ **ENTWICKLUNG**

### **Projekt-Struktur**
```
neuronode/
├── neuronode-backend/         # Backend Services
│   ├── src/                   # Python Source Code
│   ├── tests/                 # Backend Tests
│   ├── docker-compose.yml     # Development Services
│   └── manage.sh              # Service Management
├── neuronode-webapp/          # Frontend Application
│   ├── src/                   # Next.js Source Code
│   ├── tests/                 # E2E Tests
│   └── package.json           # Frontend Dependencies
└── docs/                      # Dokumentation
```

### **Beitragen**
1. **Issues**: GitHub Issues für Bugs und Feature Requests
2. **Pull Requests**: Feature Branches → Main
3. **Testing**: Alle Tests müssen bestehen
4. **Code Style**: ESLint + Prettier für Frontend, Black für Backend

### **Technologie-Stack**
- **Backend**: Python, FastAPI, Neo4j, ChromaDB, Redis
- **Frontend**: Next.js, TypeScript, Material Web Components
- **AI/ML**: LiteLLM, OpenAI, Anthropic, Google AI
- **Infrastructure**: Docker, PostgreSQL, NGINX

## 📈 **PERFORMANCE**

### **Benchmarks**
- **Dokumentverarbeitung**: < 30 Sekunden (Standard-PDFs)
- **Chat-Antworten**: < 5 Sekunden (komplexe Abfragen)
- **Graph-Visualisierung**: < 3 Sekunden (bis 1000 Knoten)
- **Concurrent Users**: 100+ gleichzeitig unterstützt

### **Optimierungen**
- **Caching**: Redis für häufige Abfragen
- **Async Processing**: Non-blocking I/O
- **Smart Routing**: Model-spezifische Optimierungen
- **Resource Management**: Memory-effiziente Verarbeitung

## 🏆 **STATUS & ROADMAP**

### **Aktuelle Version (2.0)**
- ✅ LiteLLM Integration (27 Modelle)
- ✅ Enterprise Testing Framework
- ✅ Production-Ready Security
- ✅ Comprehensive Documentation
- ✅ Performance Optimizations

### **Nächste Releases**
- **Q1 2025**: Multi-Language Support, Enhanced Analytics
- **Q2 2025**: Advanced Visualizations, API v2
- **Q3 2025**: Enterprise Integrations, Advanced Security

## 📞 **SUPPORT**

### **Community**
- **GitHub**: Issues, Diskussionen, Feature Requests
- **Dokumentation**: Umfassende Guides und Tutorials
- **Examples**: Code-Beispiele und Use Cases

### **Enterprise Support**
- **Professional Services**: Implementation Support
- **Custom Development**: Feature-Entwicklung
- **Training**: Team-Schulungen und Best Practices

---

**Neuronode - Transforming Knowledge into Intelligence** 🧠✨
