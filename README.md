# 🧠 KI-Wissenssystem

Ein intelligentes Wissensmanagementsystem für Compliance und IT-Sicherheit mit KI-gestützter Dokumentenverarbeitung und Knowledge Graph.

## ✨ Features

### Backend (Python/FastAPI)
- 🔍 **Intelligente Dokumentenverarbeitung** - BSI, ISO 27001, NIST CSF
- 🧠 **KI-gestützte Abfragen** - OpenAI, Anthropic, Google Gemini
- 🕸️ **Knowledge Graph** - Neo4j mit automatischer Verknüpfung
- 📊 **Vector Search** - ChromaDB für semantische Suche
- 🐳 **Docker-basiert** - Einfache Installation und Skalierung

### Obsidian Plugin (TypeScript)
- 📄 **Transparenter Dokumentenupload** - Drag & Drop mit Echtzeit-Analyse
- 💬 **Intelligenter Chat** - Kontextuelle Antworten mit Quellenangaben
- 🕸️ **Interaktiver Wissensgraph** - D3.js-basierte Visualisierung
- ⚡ **Hot Reload** - Entwicklerfreundliche Umgebung
- 🔍 **Erweiterte Suche** - Semantische und strukturierte Suche

## 🚀 Schnellstart

### 🍎 macOS/Linux Setup

```bash
cd ki-wissenssystem
./setup.sh
```

### 🪟 Windows Setup

```powershell
cd ki-wissenssystem
.\setup.ps1
```

> **Windows-Nutzer**: Führen Sie PowerShell als Administrator aus!  
> Detaillierte Anleitung: [README-Windows.md](ki-wissenssystem/README-Windows.md)

## 📋 Voraussetzungen

### Allgemein
- **Docker** & Docker Compose
- **Python 3.11+**
- **Node.js 18+** (für Obsidian Plugin)

### Betriebssystem-spezifisch

#### macOS
- Homebrew (wird automatisch installiert)
- Xcode Command Line Tools

#### Windows
- PowerShell 5.1+ (bereits enthalten)
- Administrator-Rechte
- Chocolatey (wird automatisch installiert)

#### Linux
- apt/yum/pacman (je nach Distribution)
- curl, git

## 🏗️ Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Obsidian      │    │   Web Interface │    │   CLI Tools     │
│   Plugin        │    │   (FastAPI)     │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     KI-Wissenssystem      │
                    │      (Python API)         │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────┴─────┐         ┌───────┴───────┐       ┌───────┴───────┐
    │   Neo4j   │         │   ChromaDB    │       │   Redis       │
    │ (Graph DB)│         │ (Vector DB)   │       │  (Cache)      │
    └───────────┘         └───────────────┘       └───────────────┘
```

## 🛠️ Verwendung

### CLI Tools

```bash
# System starten
./start-all.sh

# Dokument verarbeiten
./ki-cli.sh process dokument.pdf

# Abfrage stellen
./ki-cli.sh query "Wie implementiere ich MFA nach BSI C5?"

# Statistiken anzeigen
./ki-cli.sh stats

# System stoppen
./stop-all.sh
```

### Web Interface

- **API Dokumentation**: http://localhost:8080/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)

### Obsidian Plugin

#### 🚀 Automatische Installation (empfohlen):
```bash
# macOS/Linux
cd ki-wissenssystem
./setup-obsidian.sh    # All-in-One Setup

# Windows
cd ki-wissenssystem
.\setup-obsidian.ps1   # Windows All-in-One Setup
```

#### 📋 Manuelle Installation:
1. **Plugin bauen**:
   ```bash
   cd obsidian-ki-plugin
   npm install
   npm run build
   ```

2. **Plugin installieren**:
   - **macOS lokal**: `~/Library/Application Support/obsidian/IhrVault/.obsidian/plugins/`
   - **macOS iCloud**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/IhrVault/.obsidian/plugins/`
   - **Windows**: `%APPDATA%\Obsidian\IhrVault\.obsidian\plugins\`

3. **In Obsidian aktivieren**:
   - Settings → Community Plugins → "KI-Wissenssystem" aktivieren

4. **API-URL konfigurieren**: `http://localhost:8080`

#### 📄 Plugin-Features nutzen:
- **📤 Dokumentenupload**: Ribbon-Icon oder Cmd+P → "Open Document Upload"
- **💬 Chat**: Ribbon-Icon oder Cmd+P → "Open Knowledge Chat"  
- **🕸️ Graph**: Ribbon-Icon oder Cmd+P → "Open Knowledge Graph"

## 🔧 Konfiguration

### Environment Variables

```bash
# .env Datei bearbeiten
nano .env
```

Wichtige Variablen:
```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CHROMA_HOST=localhost
CHROMA_PORT=8000
```

### LLM Model Routing

```env
CLASSIFIER_MODEL=gemini-pro
EXTRACTOR_MODEL=gpt-4-turbo-preview
SYNTHESIZER_MODEL=claude-3-opus-20240229
```

## 📚 Unterstützte Dokumenttypen

### Automatische Erkennung und Verarbeitung

| Dokumenttyp | Automatische Erkennung | Control-Extraktion | Chunk-Verarbeitung |
|-------------|------------------------|--------------------|--------------------|
| **BSI IT-Grundschutz** | ✅ | ✅ | ✅ |
| **BSI C5 Cloud** | ✅ | ✅ | ✅ |
| **ISO 27001** | ✅ | ✅ | ✅ |
| **NIST CSF** | ✅ | ✅ | ✅ |
| **Technische Whitepapers** | ✅ | ❌ | ✅ |
| **FAQ-Dokumente** | ✅ | ❌ | ✅ |
| **Allgemeine PDFs** | ✅ | ❌ | ✅ |

### Dateiformate
- **PDF** - Vollständige Text-Extraktion
- **Word (.docx)** - Struktur und Formatierung
- **Excel (.xlsx)** - Tabellen und Daten
- **PowerPoint (.pptx)** - Folien und Inhalte
- **Text (.txt)** - Einfache Textverarbeitung
- **XML** - Strukturierte Datenextraktion

## 📄 Transparenter Upload-Workflow

Das Plugin bietet vollständige Transparenz über den Verarbeitungsprozess:

### 1. **Upload-Analyse** (vor Verarbeitung)
- Dateityp-Erkennung mit Konfidenz
- Dokumentklassifizierung-Vorhersage
- Geschätzte Verarbeitungsdauer
- Erwartete Anzahl Controls/Chunks

### 2. **Echtzeit-Verarbeitung**
- Schritt-für-Schritt Fortschritt
- Aktuelle Verarbeitungsphase
- Geschätzte Restzeit
- Fehlerbehandlung mit Details

### 3. **Ergebnis-Transparenz**
- Extraktions-Qualitätsbewertung
- Beziehungs-Konfidenzwerte
- Quellenangaben mit Seitenzahlen
- Graph-Kontext mit Begründungen

## 🧪 Entwicklung

### 🚀 Schneller Einstieg

```bash
# 1. Repository klonen
git clone https://github.com/username/ki-wissenssystem.git
cd ki-wissenssystem

# 2. Setup ausführen (einmalig)
./setup.sh                 # macOS/Linux
# oder: .\setup.ps1         # Windows

# 3. Entwicklungs-Modus starten
cd ki-wissenssystem
./dev-mode.sh              # Interaktives Menü
```

### 🔥 Hot Reload verfügbar!

- **Backend**: Code-Änderungen werden automatisch übernommen
- **Plugin**: Watch-Modus mit `npm run dev`
- **Keine Neuinstallation** für die meisten Änderungen nötig

### 📚 Detaillierte Anleitung

Siehe [ENTWICKLUNG.md](ENTWICKLUNG.md) für:
- Hot Reload Setup
- Entwicklungs-Workflow
- Debugging-Tools
- Häufige Probleme

### Tests ausführen

```bash
pytest tests/
npm test  # Plugin-Tests
```

## 🐳 Docker Services

Das System verwendet folgende Services:

- **Neo4j 5** - Knowledge Graph Database
- **ChromaDB 0.5** - Vector Database für Embeddings
- **Redis 7** - Caching und Session-Management

### Service-Management

```bash
# Alle Services starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Services stoppen
docker-compose down
```

## 🔍 Fehlerbehebung

### Häufige Probleme

#### Docker-Probleme
```bash
# Docker Status prüfen
docker info

# Services neu starten
docker-compose down && docker-compose up -d
```

#### Python-Probleme
```bash
# Virtual Environment neu erstellen
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Plugin-Build-Probleme
```bash
cd obsidian-ki-plugin
rm -rf node_modules
npm install
npm run build
```

### Log-Dateien

- **Setup**: `setup.log` / `setup.log` (Windows)
- **API**: `logs/api.log`
- **Docker**: `docker-compose logs`

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Changes committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request erstellen

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/username/ki-wissenssystem/issues)
- **Diskussionen**: [GitHub Discussions](https://github.com/username/ki-wissenssystem/discussions)
- **Dokumentation**: [Wiki](https://github.com/username/ki-wissenssystem/wiki)

---

**Entwickelt mit ❤️ für bessere Compliance und IT-Sicherheit**