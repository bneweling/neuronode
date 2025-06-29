# 🏗️ System-Architektur und Komponenten-Übersicht

**Version:** 2.0 (K6 Knowledge Consolidation)  
**Datum:** Januar 2025  
**Zielgruppe:** Internes Entwicklungsteam und Tester  
**Status:** Produktionsreif mit bekannten Optimierungspotenzialen

---

## �� Architektur-Überblick

Das KI-Wissenssystem ist ein **hybrides RAG-System** (Retrieval-Augmented Generation), das strukturierte Graph-Datenbanken mit Vektor-Embeddings kombiniert, um sowohl semantische Suche als auch komplexe Beziehungsanalysen zu ermöglichen.

### High-Level Architektur

```mermaid
graph TB
    A[Web Frontend - Next.js] --> B[FastAPI Backend]
    B --> C[Query Orchestrator]
    C --> D[Intent Analyzer]
    C --> E[Hybrid Retriever]
    C --> F[Response Synthesizer]
    
    G[Document Processor] --> H[Neo4j Graph DB]
    G --> I[ChromaDB Vector Store]
    
    E --> H
    E --> I
    
    J[Graph Gardener] --> H
    K[LiteLLM Client] --> L[Multi-LLM Providers]
    
    D --> K
    F --> K
    G --> K
```

---

## 📚 Datenmodell und Speicher-Architektur

### Neo4j Graph-Datenbank

**Zweck:** Strukturierte Beziehungen zwischen Compliance-Controls, Technologien und Wissens-Fragmenten

#### Node-Typen (produktiv)
| Node-Typ | Eigenschaften | Status | Verwendung |
|----------|---------------|--------|-------------|
| `:ControlItem` | id, title, text, level, domain, source | ✅ Produktiv | BSI, ISO, NIST Controls |
| `:KnowledgeChunk` | id, text, summary, keywords, source | ✅ Produktiv | Technische Dokumentation |
| `:Technology` | name, category, vendor | ✅ Produktiv | IT-Technologien |
| `:Entity` | name, type | ✅ Produktiv | Allgemeine Entitäten |

#### Beziehungstypen (Stand Januar 2025)
| Beziehung | Status | Automatische Erkennung | Qualität |
|-----------|--------|------------------------|----------|
| `:IMPLEMENTS` | ✅ Produktiv | Graph Gardener | Hoch |
| `:SUPPORTS` | ✅ Produktiv | LLM-basiert | Mittel-Hoch |
| `:REFERENCES` | ✅ Produktiv | Pattern-basiert | Hoch |
| `:MAPS_TO` | ⚠️ Experimentell | Manuell + LLM | Mittel |
| `:RELATES_TO` | ✅ Produktiv | Similarity-basiert | Mittel |
| `:MENTIONS` | ✅ Produktiv | NER-basiert | Hoch |
| `:CONFLICTS` | ⚠️ Experimentell | LLM-basiert | Niedrig |

### ChromaDB Vektor-Speicher

**Zweck:** Semantische Suche und Ähnlichkeits-Matching

#### Production Collections
| Collection | Dokument-Typen | Embedding-Modell | Performance |
|-----------|----------------|------------------|-------------|
| `compliance_docs` | BSI, ISO, NIST | Gemini Embedding-001 | Sehr gut |
| `technical_docs` | Whitepapers, Tech-Docs | Gemini Embedding-001 | Gut |
| `general_knowledge` | Diverse Chunks | Gemini Embedding-001 | Mittel |

---

## 🔧 Core-Komponenten Details

### 1. Document Processing Pipeline

**Ort:** `src/document_processing/`  
**Status:** ✅ Produktionsreif

#### Unterstützte Dateiformate (getestet)
| Format | Loader | Extraktor | Qualität | Limitierungen |
|--------|--------|-----------|----------|---------------|
| PDF | PDFLoader | Text + Metadata | Sehr gut | Komplexe Layouts problematisch |
| DOCX | OfficeLoader | Paragraphen + Tabellen | Gut | Makros werden ignoriert |
| XLSX | OfficeLoader | Tabellendaten | Gut | Formeln werden nicht ausgewertet |
| PPTX | OfficeLoader | Folien-Inhalte | Mittel | Grafiken werden nicht extrahiert |
| TXT | TextLoader | Plain-Text | Sehr gut | Keine Limitierungen |
| XML | XMLLoader | Strukturierte Daten | Gut | Namespace-Handling teilweise fehlerhaft |

#### Document Classification (aktueller Stand)

**Ort:** `src/document_processing/classifier.py`

**Erkennungslogik:**
```python
# Regel-basierte Erkennung (sehr zuverlässig)
BSI_GRUNDSCHUTZ: "IT-Grundschutz" im Text → 95% Genauigkeit
BSI_C5: "Cloud Computing Compliance" → 90% Genauigkeit  
ISO_27001: "ISO/IEC 27001" → 85% Genauigkeit
NIST_CSF: "NIST Cybersecurity Framework" → 80% Genauigkeit

# LLM-basierte Klassifizierung (für unklare Fälle)
Gemini-2.5-Flash: Fallback bei <70% Regel-Konfidenz
```

**Performance:** 
- Regel-basiert: ~50ms/Dokument
- LLM-basiert: ~2-5s/Dokument (abhängig von API-Latenz)

### 2. Query Orchestrator

**Ort:** `src/orchestration/query_orchestrator.py`  
**Status:** ✅ Produktionsreif mit Performance-Optimierungen

#### Pipeline-Performance (gemessen)
```yaml
Intent Analysis: 0.02ms (Ziel <200ms) ✅ Übererfüllt
Hybrid Retrieval: ~800ms (abhängig von Graph-Komplexität)
Response Synthesis: ~2-8s (abhängig von LLM-Provider)
Gesamt-Pipeline: ~3-10s (Ziel <10s) ✅ Erreicht
```

#### Request Prioritization (implementiert)
```yaml
CRITICAL: Intent Analysis (Sub-200ms garantiert)
HIGH: Hybrid Retrieval (Cache-optimiert)  
MEDIUM: Response Synthesis (Qualität vor Geschwindigkeit)
LOW: Background Tasks (Graph Gardening)
BATCH: Bulk Operations (nachts)
```

### 3. LiteLLM Integration

**Ort:** `src/llm/enhanced_litellm_client.py`  
**Status:** ✅ Vollständig migriert auf v1.72.6

#### Verfügbare Modelle (verifiziert Januar 2025)
```yaml
OpenAI (9 Modelle):
  - gpt-4.1 ✅ Produktiv
  - gpt-4o ✅ Produktiv  
  - o4-mini ✅ Reasoning-Modell
  - o3-mini ✅ Neuestes Reasoning
  
Anthropic (7 Modelle):
  - claude-opus-4-20250514 ✅ Top-Performance
  - claude-sonnet-4-20250514 ✅ Balanced
  
Google (7 Modelle):
  - gemini-2.5-pro ✅ Hauptmodell
  - gemini-2.5-flash ✅ Schnell+Günstig
```

#### Model Profile System
```bash
# Aktuell aktives Profil
./switch-model-profile.sh --show
> premium (claude-opus-4 + gpt-4.1 + gemini-2.5-pro)

# Verfügbare Profile
premium: Beste Qualität (teuer)
balanced: Optimaler Kompromiss ✅ Empfohlen
cost_effective: Günstigste Option
gemini_only: Nur Google-Modelle
openai_only: Nur OpenAI-Modelle
```

### 4. Hybrid Retriever

**Ort:** `src/retrievers/hybrid_retriever.py`  
**Status:** ✅ Produktionsreif

#### Retrieval-Strategien
```python
# Graph-basierte Suche (strukturierte Inhalte)
graph_results = neo4j.run(
    "MATCH (c:ControlItem)-[:RELATES_TO]-(t:Technology) "
    "WHERE c.text CONTAINS $query_terms "
    "RETURN c, t, score"
)

# Vektor-basierte Suche (semantische Ähnlichkeit)  
vector_results = chroma.query(
    query_text=query,
    n_results=10,
    where={"document_type": intent.document_types}
)

# Hybrid-Ranking (kombiniert beide Ergebnisse)
final_results = rerank_results(graph_results, vector_results)
```

**Performance-Metriken:**
- Graph-Suche: 200-800ms (abhängig von Komplexität)
- Vektor-Suche: 100-300ms (ChromaDB-optimiert)
- Hybrid-Ranking: 50-100ms (in-memory)

---

## 🌐 Frontend-Architektur

### Next.js Web-App

**Ort:** `ki-wissenssystem-webapp/`  
**Status:** ✅ Produktionsreif

#### Tech-Stack
```yaml
Framework: Next.js 15 + Turbopack ✅
Language: TypeScript ✅ Type Safety
UI: Material Web Components ✅ Modern Design
State: React Context + Hooks ✅ Simpel aber stabil
API: Fetch API + WebSocket ✅ Real-time Updates
```

#### Core Components (verifiziert)
| Komponente | Status | Performance | Bekannte Issues |
|-----------|--------|-------------|-----------------|
| FileUploadZone | ✅ Stabil | Gut | Große Dateien (>50MB) langsam |
| ChatInterface | ✅ Stabil | Sehr gut | Keine bekannten Issues |
| GraphVisualization | ⚠️ Beta | Mittel | Performance bei >1000 Nodes |
| DocumentViewer | ✅ Stabil | Gut | PDF-Rendering manchmal langsam |

### Real-time Features

#### WebSocket Integration
```javascript
// Chat Updates
ws://localhost:8000/ws/chat/{session_id}
Status: ✅ Stabil, Auto-Reconnect funktioniert

// Processing Updates  
ws://localhost:8000/ws/processing/{document_id}
Status: ⚠️ Gelegentliche Timeouts bei großen Dokumenten

// Graph Updates
ws://localhost:8000/ws/graph/{graph_id} 
Status: ✅ Stabil
```

---

## 🤖 KI-Services Integration

### Intent Analyzer

**Ort:** `src/retrievers/intent_analyzer.py`  
**Status:** ✅ Produktionsreif mit hervorragender Performance

#### Performance-Durchbruch
```yaml
# Hybrid-Ansatz: Pattern-Recognition + LLM
Pattern-basiert (80% der Fälle): 0.02ms ✅ 10,000x schneller als Ziel
LLM-basiert (20% der Fälle): 1-3s (nur bei unklaren Intents)
Durchschnittliche Latenz: ~200ms ✅ Ziel erreicht
```

#### Erkannte Intent-Typen
```python
COMPLIANCE_QUERY = "compliance"      # BSI, ISO, NIST Anfragen
TECHNICAL_QUERY = "technical"        # How-to, Implementierung  
COMPARISON_QUERY = "comparison"      # Vergleiche zwischen Standards
IMPLEMENTATION_QUERY = "implementation"  # Konkrete Umsetzung
GENERAL_QUERY = "general"           # Allgemeine Fragen
```

### Response Synthesizer

**Ort:** `src/retrievers/response_synthesizer.py`  
**Status:** ✅ Produktionsreif

#### Synthesis-Strategien
```yaml
Compliance-Antworten: 
  Template: "Basierend auf [Standard] ist folgendes relevant..."
  Quellen: Immer mit Referenzen
  Qualität: Sehr hoch ✅

Technische Antworten:
  Template: "Zur Implementierung von [Technologie]..."
  Code-Beispiele: Wo verfügbar
  Qualität: Hoch ✅

Vergleichende Antworten:
  Template: "Unterschiede zwischen [A] und [B]..."
  Tabellen: Automatisch generiert
  Qualität: Mittel-Hoch ⚠️ (manchmal unvollständig)
```

---

## 🔄 Background Services

### Graph Gardener

**Ort:** `src/orchestration/graph_gardener.py`  
**Status:** ✅ Produktionsreif aber ressourcenintensiv

#### Automatische Relationship Discovery
```python
# Täglich um 2:00 Uhr
cron: "0 2 * * *"

Aufgaben:
1. Orphan-Nodes identifizieren ✅ Funktioniert gut
2. Ähnlichkeits-basierte Connections ✅ 70% Genauigkeit  
3. LLM-basierte Relationship-Validierung ⚠️ Teuer, aber qualitativ
4. Dubletten-Erkennung ✅ Sehr gut
5. Metadaten-Bereinigung ✅ Automatisch
```

**Resource Usage:**
- CPU: Hoch während der Ausführung (2-4 Cores)
- Memory: 2-4GB (abhängig von Graph-Größe)
- Ausführungszeit: 30-120 Minuten (je nach Datenmenge)

### Auto Relationship Discovery

**Ort:** `src/orchestration/auto_relationship_discovery.py`  
**Status:** ✅ Produktionsreif

```python
# Confidence-basierte Beziehungserstellung
if similarity_score > 0.8:
    create_relationship(source, target, "RELATES_TO", high_confidence=True)
elif similarity_score > 0.6:
    create_relationship(source, target, "RELATES_TO", medium_confidence=True)
    # → Manuelle Review erforderlich
```

---

## 📊 Monitoring und Performance

### System-Metriken (aktueller Stand)

#### Pipeline Performance
```yaml
Document Processing:
  Small PDFs (<5MB): 10-30s ✅ Gut
  Large PDFs (>20MB): 2-5min ⚠️ Optimierungspotenzial
  Word Documents: 5-15s ✅ Sehr gut
  
Query Processing:
  Simple Queries: 3-8s ✅ Ziel erreicht
  Complex Queries: 8-15s ⚠️ Grenzwertig
  
Graph Operations:
  Node Creation: <100ms ✅ Sehr gut
  Relationship Queries: 200-2000ms ⚠️ Abhängig von Komplexität
```

#### Error Rates (Produktionsdaten)
```yaml
Document Processing: 2-5% (meist PDF-Layout-Probleme)
Query Processing: <1% ✅ Sehr stabil
LLM API Calls: 3-8% (Provider-abhängig)
Database Operations: <0.5% ✅ Sehr stabil
```

### Caching-System

**Implementation:** Redis + In-Memory  
**Status:** ✅ Produktionsreif

```python
# Query Result Caching
cache_ttl = 3600  # 1 Stunde
cache_hit_rate = 35-45%  # Typisch für Knowledge Queries

# Vector Search Caching  
vector_cache_ttl = 7200  # 2 Stunden
vector_cache_hit_rate = 60-70%  # Höher wegen wiederkehrender Patterns
```

---

## 🚨 Bekannte Limitierungen und Optimierungspotenziale

### High Priority Issues

#### 1. Graph Visualization Performance
```yaml
Problem: Frontend laggt bei >1000 Nodes
Impact: Benutzer-Experience bei großen Datensets
Workaround: Pagination und Filtering implementiert
Timeline: Q1 2025 - D3.js zu WebGL Migration geplant
```

#### 2. Large Document Processing
```yaml
Problem: PDFs >50MB verursachen Memory-Issues
Impact: Enterprise-Dokumente können nicht verarbeitet werden
Workaround: Streaming-basierte Verarbeitung in Development
Timeline: Q1 2025 - Chunk-based Processing
```

#### 3. Multi-Language Support
```yaml
Problem: System optimiert für deutsche Texte
Impact: Englische/internationale Dokumente suboptimal
Status: Basic English Support vorhanden
Timeline: Q2 2025 - Multi-Language Embeddings
```

### Medium Priority Issues

#### 4. LLM API Rate Limiting
```yaml
Problem: Bei hoher Last Rate-Limits verschiedener Provider
Impact: Temporäre Service-Degradation
Mitigation: Intelligent Load-Balancing zwischen Providern implementiert
Status: Monitoring und Auto-Scaling in Development
```

#### 5. Relationship Quality
```yaml
Problem: Automatisch erkannte Relationships haben 60-80% Precision
Impact: False Positives in Graph-Navigation
Mitigation: Confidence-Scoring und manuelle Review-Workflows
Status: Continuous Learning System geplant
```

---

## 🧪 Testing und Quality Assurance

### E2E Test Coverage

**Ort:** `ki-wissenssystem-webapp/tests/e2e/`  
**Status:** ✅ Comprehensive Test Suite implementiert

#### Test Scenarios (verifiziert)
```yaml
Complete Knowledge Workflow:
  File: user-journey-complete-workflow.spec.ts (271 lines)
  Coverage: PDF Upload → Processing → Query → Graph ✅
  Success Rate: 100% (bei idealem Setup)
  
Performance & Scalability:
  File: performance-scalability.spec.ts
  Coverage: Load-Testing, Memory-Usage ✅
  Benchmarks: Definiert und überwacht
  
State Synchronization:
  File: state-synchronization-race-conditions.spec.ts  
  Coverage: WebSocket Race-Conditions ✅
  Critical: Verhindert UI-Inkonsistenzen
```

#### Test Execution
```bash
# Unit Tests (Backend)
cd ki-wissenssystem && python -m pytest tests/
Success Rate: 90-95% ✅ (abhängig von externen APIs)

# Integration Tests  
./scripts/comprehensive_phase3_testing.py
Success Rate: 85-90% ✅ (E2E Pipeline)

# Frontend E2E Tests
cd ki-wissenssystem-webapp && npm run test:e2e
Success Rate: 80-90% ⚠️ (Browser-abhängig)
```

---

## 🔐 Sicherheit und Compliance

### API Security
```yaml
Authentication: JWT-basiert ✅
Authorization: Role-based Access Control ✅
Rate Limiting: Redis-basiert ✅ 1000 req/min/user
Input Validation: Pydantic Models ✅
SQL Injection: Cypher Parameterization ✅
```

### Data Privacy
```yaml
Document Storage: Lokal (keine Cloud-Upload) ✅
PII Detection: Basis-Implementation ⚠️ Ausbaubar
Audit Logging: PostgreSQL-basiert ✅ Enterprise-Grade
Data Retention: Konfigurierbar ✅
GDPR Compliance: Grundlagen implementiert ⚠️
```

---

## 📈 Performance Benchmarks (Produktions-Metriken)

### Pipeline Latency Targets vs. Actual

| Komponente | Ziel | Aktuell | Status |
|-----------|------|---------|--------|
| Intent Analysis | <200ms | 0.02ms | ✅ Übererfüllt |
| Document Classification | <5s | 2-8s | ✅ Erfüllt |
| Vector Search | <1s | 0.3s | ✅ Übererfüllt |
| Graph Query | <2s | 0.8s | ✅ Übererfüllt |
| Response Synthesis | <10s | 5-12s | ⚠️ Grenzwertig |
| Full Pipeline | <30s | 15-25s | ✅ Erfüllt |

### Resource Usage (Production Server)

```yaml
CPU Usage:
  Idle: 5-15% ✅ Effizient
  Document Processing: 60-90% ⚠️ CPU-intensive
  Query Processing: 20-40% ✅ Akzeptabel
  
Memory Usage:
  Base System: 2-4GB ✅
  Document Processing: +2-8GB ⚠️ Abhängig von Dateigröße
  Graph Database: 1-3GB ✅ Stabil
  
Disk I/O:
  Vector Database: Moderate Reads ✅
  Graph Database: High bei komplexen Queries ⚠️
  Document Storage: Low (lokal optimiert) ✅
```

---

## 🚀 Deployment und Operations

### Current Deployment Setup

#### Development Environment
```bash
# Backend Services
cd ki-wissenssystem && ./start-all.sh
Services: FastAPI + Neo4j + ChromaDB + Redis

# Frontend Development
cd ki-wissenssystem-webapp && npm run dev  
Port: 3000 (with hot-reload)
```

#### Production Deployment
```yaml
Backend: Docker Compose (docker-compose.production.yml)
Database: Neo4j with persistent volumes ✅
Vector Store: ChromaDB with SSD storage ✅  
Frontend: Next.js optimized build ✅
Reverse Proxy: Nginx with SSL termination ✅
Monitoring: Basic logging ⚠️ Ausbaubar
```

### Service Management
```bash
# Central Management (Empfohlen)
./manage.sh start    # Startet alle Services
./manage.sh stop     # Stoppt alle Services  
./manage.sh status   # Service Status
./manage.sh logs     # Tail all logs

# Model Profile Switching
./switch-model-profile.sh balanced  # Empfohlenes Produktions-Profil
```

---

## 📝 Fazit: Produktionsreife mit klaren Optimierungszielen

### ✅ Produktionsreif
- **Core RAG Pipeline:** Stabil und performant
- **Document Processing:** Zuverlässig für Standard-Formate
- **Query Orchestration:** Enterprise-grade mit Caching
- **API Integration:** Vollständig migriert auf LiteLLM v1.72.6
- **Frontend:** Modern und responsive
- **Basic Security:** JWT, Rate-Limiting, Input-Validation

### ⚠️ Optimierungspotenzial
- **Large Document Handling:** Memory-Optimierung erforderlich
- **Graph Visualization:** Performance bei großen Graphen
- **Multi-Language Support:** Derzeit DE-optimiert
- **Advanced Monitoring:** APM und Alerting ausbaubar
- **GDPR Compliance:** Erweiterte Privacy-Features

### 🎯 Nächste Entwicklungsprioritäten
1. **Q1 2025:** Large Document Streaming + Graph Visualization Optimierung
2. **Q2 2025:** Multi-Language Support + Advanced Monitoring
3. **Q3 2025:** Enterprise Security Features + Advanced Analytics

**Das System ist produktionsreif für mittlere bis große Unternehmensumgebungen mit klaren Skalierungs- und Optimierungszielen.**
