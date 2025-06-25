# KI-Wissenssystem - Web-App Version

Eine moderne, eigenständige Web-Anwendung für intelligente Dokumentenverarbeitung und Wissensmanagement.

## Überblick

Diese Version des KI-Wissenssystems bietet eine vollständig eigenständige Web-Anwendung mit:

- **Moderne Benutzeroberfläche** mit Material Design 3
- **Responsives Design** für Desktop, Tablet und Mobile
- **Real-time Chat** mit dem KI-System
- **Interaktive Knowledge Graph** Visualisierung
- **Drag & Drop Dokumenten-Upload**
- **Erweiterte Suchfunktionen**

## Architektur

```
ki-wissenssystem-webapp/     # Next.js Web-App (Frontend)
├── src/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React Komponenten
│   └── lib/                 # Utilities

ki-wissenssystem/            # Backend Services
├── src/api/                 # FastAPI Backend
├── src/document_processing/ # Dokumentenverarbeitung
├── src/retrievers/          # RAG Retrieval System
└── src/storage/             # Vector- & Graph-Datenbank
```

## Quick Start

### 1. Backend Services starten

```bash
cd ki-wissenssystem
./start-all.sh
```

### 2. Web-App starten

```bash
cd ki-wissenssystem-webapp
npm install
npm run dev
```

Die Web-App ist dann unter http://localhost:3000 verfügbar.

## Features

### 🚀 Moderne Web-App
- Next.js 15 mit Turbopack
- TypeScript für Type Safety
- Material Web Components
- Responsive Design

### 🤖 KI-Integration
- RAG-basiertes Question Answering
- Intelligente Dokumentenklassifizierung
- Automatische Wissensextraktion
- Neo4j Knowledge Graph

### 📄 Dokumentenverarbeitung
- PDF, Word, PowerPoint, Excel Support
- Automatische OCR für gescannte Dokumente
- Chunk-basierte Vectorisierung
- Metadaten-Extraktion

### 🔍 Erweiterte Suche
- Semantische Suche
- Hybrid Retrieval (Dense + Sparse)
- Kontext-bewusste Antworten
- Knowledge Graph Navigation

## Development

### Entwicklungsumgebung

```bash
# Backend Development Mode
cd ki-wissenssystem
./dev-mode.sh

# Frontend Development
cd ki-wissenssystem-webapp
npm run dev
```

### API Dokumentation

FastAPI Docs: http://localhost:8000/docs

### Testing

```bash
# Backend Tests
cd ki-wissenssystem
python -m pytest tests/

# Frontend Tests
cd ki-wissenssystem-webapp
npm test
```

## Deployment

### Docker Deployment

```bash
# Backend Services
cd ki-wissenssystem
docker-compose up -d

# Web-App (separate deployment)
cd ki-wissenssystem-webapp
docker build -t ki-webapp .
docker run -p 3000:3000 ki-webapp
```

### Production Setup

1. **Backend Services**: Verwenden Sie `docker-compose.prod.yml`
2. **Database**: Neo4j und ChromaDB mit persistenten Volumes
3. **Web-App**: Next.js Build mit optimierter Bundle-Größe
4. **SSL/TLS**: Nginx Reverse Proxy mit SSL-Termination

## Konfiguration

### Backend (`ki-wissenssystem/.env`)
```env
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b

# Database Configuration
NEO4J_URI=bolt://localhost:7687
CHROMA_HOST=localhost
CHROMA_PORT=8000

# API Configuration
API_HOST=localhost
API_PORT=8000
```

### Web-App (Environment Variables)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Migrating from Obsidian Plugin

Diese Version ist vollständig eigenständig und benötigt keine Obsidian-Installation. 

### Datenübernahme

Dokumente und Wissensgraphen können direkt übernommen werden:

```bash
# Datenbanken sind kompatibel zwischen den Versionen
# Keine Migration notwendig
```

## Support

- **Dokumentation**: Siehe `/docs` Verzeichnis
- **Issues**: GitHub Issues für Bug Reports
- **Development**: Branch `webapp-version`

## Version

Diese README bezieht sich auf die **Web-App Version** des KI-Wissenssystems.
Für die Obsidian Plugin Version siehe Branch `main`. 