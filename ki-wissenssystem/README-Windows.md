# KI-Wissenssystem - Windows Setup

## 🪟 Installation unter Windows

### Voraussetzungen

- **Windows 10/11** (64-bit)
- **PowerShell 5.1+** (bereits in Windows enthalten)
- **Administrator-Rechte** für die Installation

### 🚀 Schnellstart

1. **PowerShell als Administrator öffnen**:
   - Rechtsklick auf Start-Button → "Windows PowerShell (Administrator)"
   - Oder: `Win + X` → "Windows PowerShell (Administrator)"

2. **Zum Projektverzeichnis wechseln**:
   ```powershell
   cd C:\Pfad\zu\ki-wissenssystem-main\ki-wissenssystem
   ```

3. **Setup-Skript ausführen**:
   ```powershell
   .\setup.ps1
   ```

### 📋 Setup-Optionen

Das Setup-Skript unterstützt verschiedene Parameter:

```powershell
# Vollständige Installation
.\setup.ps1

# Ohne Docker (falls bereits installiert oder nicht gewünscht)
.\setup.ps1 -SkipDocker

# Ohne Obsidian Plugin
.\setup.ps1 -SkipPlugin

# Benutzerdefinierter Plugin-Pfad
.\setup.ps1 -PluginPath "C:\Pfad\zum\obsidian-plugin"

# Kombination
.\setup.ps1 -SkipDocker -SkipPlugin
```

### 🔧 Was wird automatisch installiert?

Das Setup-Skript installiert automatisch über **Chocolatey**:

- ✅ **Python 3.11** - Für das Backend
- ✅ **Docker Desktop** - Für Datenbank-Services
- ✅ **Node.js** - Für das Obsidian Plugin
- ✅ **Chocolatey** - Paketmanager (falls nicht vorhanden)

### 🐳 Docker unter Windows

**Docker Desktop** wird automatisch installiert, aber:

1. Nach der ersten Installation muss **Docker Desktop manuell gestartet** werden
2. Das Setup-Skript erkennt dies und wartet automatisch
3. Bei Problemen: Docker Desktop aus dem Startmenü starten

### 🚀 System starten

Nach der Installation stehen mehrere Optionen zur Verfügung:

#### PowerShell-Skripte:
```powershell
# Services starten
.\start-services.ps1

# API Server starten
.\start-api.ps1

# CLI verwenden
.\ki-cli.ps1 query "Ihre Frage"
.\ki-cli.ps1 stats
```

#### Batch-Dateien (einfacher):
```cmd
# CLI verwenden (aus cmd oder Explorer)
ki-cli.bat query "Ihre Frage"
ki-cli.bat process dokument.pdf

# API starten
start-api.bat
```

### 🔧 Manuelle Installation (falls Setup fehlschlägt)

#### 1. Chocolatey installieren:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### 2. Abhängigkeiten installieren:
```powershell
choco install python311 docker-desktop nodejs -y
```

#### 3. Python Virtual Environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 📂 Dateistruktur unter Windows

```
ki-wissenssystem\
├── setup.ps1              # Windows Setup-Skript
├── start-api.ps1          # API Server starten (PowerShell)
├── start-api.bat          # API Server starten (Batch)
├── start-services.ps1     # Docker Services starten
├── ki-cli.ps1            # CLI Tool (PowerShell)
├── ki-cli.bat            # CLI Tool (Batch)
├── venv\                 # Python Virtual Environment
├── data\                 # Daten-Verzeichnis
├── logs\                 # Log-Dateien
└── src\                  # Quellcode
```

### 🔍 Fehlerbehebung

#### PowerShell Execution Policy:
```powershell
# Falls Skript-Ausführung blockiert ist:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Docker-Probleme:
```powershell
# Docker Status prüfen:
docker info

# Docker Services neu starten:
docker-compose down
docker-compose up -d neo4j chromadb redis
```

#### Python-Probleme:
```powershell
# Virtual Environment neu erstellen:
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 🌐 URLs und Ports

Nach erfolgreichem Setup sind folgende Services verfügbar:

- **API Server**: http://localhost:8080
- **API Dokumentation**: http://localhost:8080/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **ChromaDB**: http://localhost:8000

### 📱 Obsidian Plugin

#### 🚀 Automatische Installation (empfohlen):
```powershell
.\setup-obsidian.ps1    # All-in-One Setup mit allen Features
```

**Features der automatischen Installation:**
- ✅ Erkennt automatisch alle Obsidian-Vaults (lokal und Cloud)
- ✅ Installiert Plugin in alle oder ausgewählte Vaults
- ✅ Baut Plugin automatisch (npm install + build)
- ✅ Prüft ob Plugin bereits installiert ist
- ✅ Überschreib-Schutz mit Benutzerbestätigung

#### 📋 Manuelle Installation:
```powershell
# 1. Plugin bauen
cd ..\obsidian-ki-plugin
npm install
npm run build

# 2. Plugin-Ordner kopieren nach:
# %APPDATA%\Obsidian\IhrVault\.obsidian\plugins\ki-wissenssystem\

# 3. In Obsidian aktivieren:
# Settings → Community Plugins → "KI-Wissenssystem" aktivieren

# 4. API-URL konfigurieren: http://localhost:8080
```

#### 📄 Plugin-Features nutzen:
Nach der Installation stehen Ihnen diese Features zur Verfügung:

**Dokumentenupload:**
- **Ribbon-Icon** 📤 klicken oder **Strg+P** → "Open Document Upload"
- **Drag & Drop** Unterstützung für alle Dateiformate
- **Echtzeit-Analyse** vor dem Upload mit Transparenz
- **Fortschrittsanzeige** während der Verarbeitung

**Chat-Interface:**
- **Ribbon-Icon** 💬 klicken oder **Strg+P** → "Open Knowledge Chat"
- Intelligente Antworten mit Quellenangaben
- Automatische Graph-Visualisierung bei Antworten

**Wissensgraph:**
- **Ribbon-Icon** 🕸️ klicken oder **Strg+P** → "Open Knowledge Graph"
- Interaktive D3.js-Visualisierung
- Filter nach Dokumenttyp, Quelle, Beziehungstyp
- Zoom und Pan-Funktionen

### ❓ Support

Bei Problemen:

1. **Log-Dateien prüfen**: `setup.log`, `logs\api.log`
2. **Services-Status**: `docker-compose ps`
3. **Python-Environment**: `.\venv\Scripts\Activate.ps1` → `python --version`

### 🆚 Unterschiede zu macOS/Linux

- **PowerShell** statt Bash
- **Chocolatey** statt Homebrew
- **Batch-Dateien** für einfache CLI-Nutzung
- **Windows-Pfade** (`\` statt `/`)
- **Docker Desktop** erforderlich (nicht Docker Engine) 