# 2. System-Architektur

## Überblick

Neuronode ist ein enterprise-grade KI-gestütztes Wissensmanagementsystem, das mit einer modernen Mikroservice-Architektur entwickelt wurde. Dieses Dokument beschreibt die umfassende Systemarchitektur, einschließlich Kernkomponenten, Datenfluss, LiteLLM-Integration und Enterprise-Sicherheitsfeatures.

## 🏗️ **SYSTEM-ARCHITEKTUR-ÜBERBLICK**

### **Hybrid UI Approach (Enterprise-Architektur)**
```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEURONODE ENTERPRISE ARCHITEKTUR                │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend-Schicht                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Next.js Web   │  │  Swagger API    │  │  LiteLLM UI     │    │
│  │   Anwendung     │  │  Dokumentation  │  │  (Admin Only)   │    │
│  │   (Port 3000)   │  │   (Port 8001)   │  │  (Port 4000)    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  API Gateway & Authentifizierungs-Schicht                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │           FastAPI Backend (Port 8001)                          ││
│  │  JWT Auth │ RBAC │ Rate Limiting │ Audit Logging │ CORS       ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  KI-Services-Schicht                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   LiteLLM       │  │  Smart Alias    │  │   Enhanced      │    │
│  │   Proxy         │  │   Manager       │  │  Model Manager  │    │
│  │  (Port 4000)    │  │  (27 Modelle)   │  │  Performance    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  Verarbeitungs-Schicht                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   Dokument-     │  │  Wissens-       │  │    Query        │
│  │   Verarbeitung  │  │  Extraktion     │  │  Orchestrator   │
│  │   Pipeline      │  │   Pipeline      │  │   & Synthese    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  Daten-Schicht                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │     Neo4j       │  │    ChromaDB     │  │   PostgreSQL    │    │
│  │  Knowledge      │  │  Vector Store   │  │  LiteLLM Data   │    │
│  │   Graph DB      │  │  (Port 8000)    │  │  (Port 5432)    │    │
│  │  (Port 7687)    │  └─────────────────┘  └─────────────────┘    │
│  └─────────────────┘  ┌─────────────────┐                         │
│                       │     Redis       │                         │
│                       │   Cache Store   │                         │
│                       │  (Port 6379)    │                         │
│                       └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 **LITELLM INTEGRATION ARCHITEKTUR**

### **Smart Alias Konfiguration (27 Modelle)**

**Task-Profile-Matrix-Implementierung:**
```yaml
# 25 Task-Profile-Kombinationen + 2 Embedding-Modelle
model_list:
  # Klassifizierungs-Modelle (5 Profile)
  - model_name: "classification_premium"
    litellm_params: 
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.1
      max_tokens: 500
      
  - model_name: "classification_balanced"
    litellm_params:
      model: "gpt-4o-mini"
      temperature: 0.2
      max_tokens: 400
      
  - model_name: "classification_cost_effective"
    litellm_params:
      model: "gemini-1.5-flash"
      temperature: 0.3
      max_tokens: 300
      
  # Extraktions-Modelle (5 Profile)
  - model_name: "extraction_premium"
    litellm_params:
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.0
      max_tokens: 2000
      
  # Synthese-Modelle (5 Profile)
  - model_name: "synthesis_premium"
    litellm_params:
      model: "claude-3-5-sonnet-20241022"
      temperature: 0.7
      max_tokens: 4000
      
  # Validierungs-Modelle (10 Profile - Primary + Secondary)
  - model_name: "validation_primary_premium"
    litellm_params:
      model: "gpt-4o"
      temperature: 0.1
      max_tokens: 1000
      
  # Embedding-Modelle (2)
  - model_name: "text_embedding_3_large"
    litellm_params:
      model: "text-embedding-3-large"
      
  - model_name: "text_embedding_ada_002"
    litellm_params:
      model: "text-embedding-ada-002"
```

### **Enhanced Model Manager Performance Tracking**

```python
class EnhancedModelManager:
    """Enterprise-Grade Model Management mit Performance Analytics"""
    
    async def get_performance_metrics(self, model_id: str) -> ModelPerformanceMetrics:
        """Real-time Performance Analytics für alle 27 Modelle"""
        return ModelPerformanceMetrics(
            model_id=model_id,
            avg_response_time=await self._calculate_avg_response_time(model_id),
            total_requests=await self._get_total_requests(model_id),
            success_rate=await self._calculate_success_rate(model_id),
            cost_per_1k_tokens=await self._get_cost_analysis(model_id),
            last_24h_usage=await self._get_24h_usage(model_id)
        )
    
    async def assign_optimal_model(self, task_type: str, profile: str) -> str:
        """Smart Model Assignment basierend auf Performance und Kosten"""
        performance_data = await self.get_all_performance_metrics()
        return self._select_optimal_model(task_type, profile, performance_data)
```

## 🔐 **ENTERPRISE-SICHERHEITS-ARCHITEKTUR**

### **Authentifizierung & Autorisierung**
```python
# JWT-basierte Authentifizierung mit LiteLLM Integration
SECURITY_CONFIG = {
    "jwt_secret": os.environ["JWT_SECRET_KEY"],
    "jwt_algorithm": "HS256",
    "access_token_expire_minutes": 60,
    "refresh_token_expire_days": 7,
    
    # LiteLLM Master Key Authentifizierung
    "litellm_master_key": os.environ["LITELLM_MASTER_KEY"],  # Format: sk-xxxxx
    "litellm_proxy_url": "http://localhost:4000",
    
    # Role-Based Access Control
    "rbac_roles": {
        "admin": ["read", "write", "model_management", "user_management"],
        "power_user": ["read", "write", "advanced_query"],
        "user": ["read", "basic_query"]
    }
}
```

### **API-Key-Management (Single Source of Truth)**
```yaml
# docker-compose.yml - Production Security Configuration
services:
  litellm-proxy:
    environment:
      - DISABLE_AUTH=false  # PRODUCTION SECURITY
      - UI_USERNAME=admin
      - UI_PASSWORD=${UI_PASSWORD}
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - LITELLM_SALT_KEY=${LITELLM_SALT_KEY}
      - LITELLM_MODE=PRODUCTION
      
      # AI Provider API Keys (NUR HIER)
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

**Sicherheits-Validierungs-Regeln:**
- ✅ API Keys NUR in LiteLLM-Umgebung
- ✅ KEINE hardcodierten Keys im Quellcode
- ✅ Environment Variable Validierung erforderlich
- ✅ Master Key Format Enforcement (sk-xxxxx)

## 📊 **DATENFLUSS-ARCHITEKTUR**

### **Dokumentverarbeitungs-Pipeline**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Datei-Upload  │───▶│   Format-       │───▶│   Inhalts-      │
│   (Multi-Typ)   │    │   Erkennung     │    │   Extraktion    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Metadaten-    │    │   Dokument-     │    │   Intelligente  │
│   Extraktion    │    │   Chunking      │    │   Klassifikation│
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Entitäten &   │    │   Vektor        │    │   Knowledge     │
│   Beziehungen   │    │   Embedding     │    │   Graph Storage │
│   (Smart Alias) │    │   (ChromaDB)    │    │   (Neo4j)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Query-Verarbeitungs-Pipeline**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nutzer-Query  │───▶│   Intent-       │───▶│   Query-        │
│   (Natürliche   │    │   Analyse       │    │   Erweiterung   │
│    Sprache)     │    │   (Smart Alias) │    │   & Planung     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hybrid        │    │   Kontext       │    │   Antwort-      │
│   Retrieval     │    │   Synthese      │    │   Generierung   │
│   (Vector+Graph)│    │   (Smart Alias) │    │   (Smart Alias) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🗄️ **DATENBANK-SCHEMAS**

### **Neo4j Knowledge Graph Schema**
```cypher
// Core Node-Typen
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

// Dokument-Knoten
(:Document {
  id: string,
  title: string,
  filename: string,
  document_type: string,
  upload_date: datetime,
  size_bytes: integer,
  checksum: string,
  metadata: map
})

// Entitäts-Knoten (Extrahiert durch LiteLLM)
(:Entity {
  id: string,
  name: string,
  type: string,
  confidence: float,
  extraction_model: string,
  properties: map
})

// Chunk-Knoten (Dokument-Segmente)
(:Chunk {
  id: string,
  content: string,
  position: integer,
  embedding_vector_id: string,
  tokens: integer
})

// Beziehungen
(:Document)-[:CONTAINS]->(:Chunk)
(:Chunk)-[:MENTIONS]->(:Entity)
(:Entity)-[:RELATED_TO]->(:Entity)
(:Document)-[:REFERENCES]->(:Document)
```

### **ChromaDB Vector Schema**
```python
# Vector Collection Konfiguration
VECTOR_COLLECTIONS = {
    "document_chunks": {
        "embedding_function": "text-embedding-3-large",
        "distance_metric": "cosine",
        "dimension": 3072,
        "metadata_fields": ["document_id", "chunk_position", "document_type"]
    },
    
    "entities": {
        "embedding_function": "text-embedding-ada-002", 
        "distance_metric": "cosine",
        "dimension": 1536,
        "metadata_fields": ["entity_type", "confidence", "extraction_model"]
    }
}
```

### **PostgreSQL LiteLLM Schema**
```sql
-- LiteLLM Management Tabellen
CREATE TABLE litellm_verificationtoken (
    token VARCHAR PRIMARY KEY,
    identifier VARCHAR NOT NULL,
    expires TIMESTAMP NOT NULL
);

CREATE TABLE litellm_budgettable (
    budget_id VARCHAR PRIMARY KEY,
    max_budget DECIMAL,
    soft_budget DECIMAL,
    current_cost DECIMAL,
    time_period VARCHAR,
    budget_duration VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Performance Analytics
CREATE TABLE model_performance_metrics (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_count INTEGER DEFAULT 0,
    avg_response_time DECIMAL,
    success_rate DECIMAL,
    cost_per_1k_tokens DECIMAL,
    error_count INTEGER DEFAULT 0
);
```

## 🔧 **API-DESIGN-PATTERNS**

### **REST API Endpoints**
```python
# Core Dokument-Management
POST   /api/documents/upload          # Multi-Format Dokumenten-Aufnahme
GET    /api/documents/{id}            # Dokument-Metadaten-Abruf
DELETE /api/documents/{id}            # Dokument-Löschung
GET    /api/documents/                # Dokument-Auflistung mit Filtern

# Wissens-Query & Retrieval
POST   /api/query                     # Natürliche Sprach-Abfragen
GET    /api/query/history             # Query-Verlaufs-Management
POST   /api/query/batch               # Batch-Query-Verarbeitung

# Knowledge Graph Operationen
GET    /api/graph/data                # Graph-Visualisierungs-Daten
GET    /api/graph/entities            # Entitäts-Exploration
GET    /api/graph/relationships       # Beziehungs-Analyse
POST   /api/graph/query               # Cypher Query Ausführung

# Admin & Model Management (Enterprise)
GET    /api/admin/models/health       # Model Health Status
POST   /api/admin/models/assign       # Model Assignment Updates
GET    /api/admin/models/performance  # Performance Analytics
POST   /api/admin/models/optimize     # Model Optimierung

# System Health & Monitoring
GET    /api/health                    # System Health Check
GET    /api/metrics                   # Performance Metriken
GET    /api/status                    # Service Status Überblick
```

### **WebSocket Endpoints (Real-time)**
```python
# Real-time Processing Updates
WS     /ws/documents/processing       # Dokumentverarbeitungs-Status
WS     /ws/graph/updates              # Graph-Update-Benachrichtigungen
WS     /ws/system/alerts              # System-Alert-Benachrichtigungen
```

## 🔄 **MIKROSERVICE-KOMMUNIKATION**

### **Service Dependencies**
```yaml
service_dependencies:
  frontend:
    depends_on: [backend_api]
    communication: HTTP/REST
    
  backend_api:
    depends_on: [litellm_proxy, neo4j, chromadb, redis]
    communication: HTTP/gRPC
    
  litellm_proxy:
    depends_on: [postgresql]
    communication: HTTP/REST
    external_apis: [openai, anthropic, google]
    
  document_processor:
    depends_on: [backend_api, neo4j, chromadb]
    communication: gRPC/Message Queue
    
  query_orchestrator:
    depends_on: [neo4j, chromadb, litellm_proxy]
    communication: gRPC/HTTP
```

### **Performance-Optimierungen**
- **Connection Pooling:** Datenbankverbindungs-Management
- **Caching-Strategie:** Redis-basiertes Query-Caching
- **Async Processing:** Non-blocking I/O-Operationen
- **Load Balancing:** Service-Verteilung und Skalierung
- **Circuit Breakers:** Fehlertoleranz und Resilienz

## 📈 **SKALIERBARKEITS-ÜBERLEGUNGEN**

### **Horizontale Skalierungs-Fähigkeiten**
- **Stateless Services:** Alle Services für horizontale Skalierung designed
- **Datenbank-Sharding:** Neo4j Clustering für Graph-Daten
- **Vector Store Partitionierung:** ChromaDB Collection Distribution
- **Load Balancing:** NGINX/HAProxy für Traffic-Verteilung

### **Performance-Benchmarks**
- **Gleichzeitige Nutzer:** 100+ gleichzeitig unterstützt
- **Dokumentverarbeitung:** 50+ Dokumente/Stunde dauerhaft
- **Query-Durchsatz:** 1000+ Abfragen/Stunde Kapazität
- **Response-Zeiten:** < 3s für komplexe Abfragen

---

Diese Architektur gewährleistet, dass Neuronode auf Enterprise-Anforderungen skalieren kann, während hohe Performance-, Sicherheits- und Zuverlässigkeits-Standards beibehalten werden.
