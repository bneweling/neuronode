# setup.ps1 - KI-Wissenssystem Setup für Windows
# Dieses Skript muss als Administrator ausgeführt werden

param(
    [switch]$SkipDocker,
    [switch]$SkipPlugin,
    [string]$PluginPath = "..\obsidian-ki-plugin"
)

# Farben für bessere Lesbarkeit
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green "✅ $args" }
function Write-Error { Write-ColorOutput Red "❌ $args" }
function Write-Warning { Write-ColorOutput Yellow "⚠️  $args" }
function Write-Info { Write-ColorOutput Blue "$args" }

# Prüfe Administrator-Rechte
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Error "Dieses Skript muss als Administrator ausgeführt werden!"
    Write-Info "Rechtsklick auf PowerShell -> 'Als Administrator ausführen'"
    exit 1
}

Write-Info "=== KI-Wissenssystem Setup für Windows ==="
Write-Info "Backend-Verzeichnis: $PWD"

# Prüfe ob wir im richtigen Verzeichnis sind
if (-not (Test-Path "requirements.txt") -or -not (Test-Path "src")) {
    Write-Error "Fehler: Bitte führen Sie dieses Skript im ki-wissenssystem Hauptverzeichnis aus!"
    Write-Info "Aktuelles Verzeichnis: $PWD"
    Write-Info "Erwartete Dateien: requirements.txt, src/"
    exit 1
}

# Prüfe ob Plugin-Verzeichnis existiert
if (-not $SkipPlugin -and -not (Test-Path $PluginPath)) {
    Write-Warning "Obsidian Plugin nicht gefunden unter: $PluginPath"
    $customPath = Read-Host "Geben Sie den Pfad zum obsidian-ki-plugin Verzeichnis ein (oder Enter für ohne Plugin)"
    if ($customPath) {
        $PluginPath = $customPath
    } else {
        $SkipPlugin = $true
    }
}

# Log-Datei
$LogFile = "setup.log"
Start-Transcript -Path $LogFile -Append

function Handle-Error {
    param($Message)
    Write-Error $Message
    Write-Info "Siehe $LogFile für Details"
    Stop-Transcript
    exit 1
}

# 1. Voraussetzungen prüfen
function Test-Prerequisites {
    Write-Info "`n1. Prüfe Voraussetzungen..."
    
    # Chocolatey
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Warning "Chocolatey nicht gefunden. Installiere Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        if ($LASTEXITCODE -ne 0) { Handle-Error "Chocolatey Installation fehlgeschlagen" }
    }
    Write-Success "Chocolatey verfügbar"
    
    # Python 3.11
    $pythonVersion = python --version 2>$null
    if (-not $pythonVersion -or $pythonVersion -notmatch "3\.11") {
        Write-Warning "Python 3.11 nicht gefunden. Installiere Python..."
        choco install python311 -y
        if ($LASTEXITCODE -ne 0) { Handle-Error "Python Installation fehlgeschlagen" }
        refreshenv
    }
    Write-Success "Python 3.11 verfügbar"
    
    # Docker Desktop
    if (-not $SkipDocker) {
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            Write-Warning "Docker nicht gefunden. Installiere Docker Desktop..."
            choco install docker-desktop -y
            if ($LASTEXITCODE -ne 0) { Handle-Error "Docker Installation fehlgeschlagen" }
            Write-Info "Docker Desktop wurde installiert. Bitte starten Sie Docker Desktop und führen Sie das Skript erneut aus."
            exit 0
        }
        
        # Docker läuft?
        try {
            docker info 2>$null | Out-Null
            Write-Success "Docker läuft"
        } catch {
            Write-Warning "Docker läuft nicht. Starte Docker Desktop..."
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            Write-Info "Warte auf Docker..."
            do {
                Start-Sleep -Seconds 3
                try {
                    docker info 2>$null | Out-Null
                    break
                } catch {
                    Write-Host "." -NoNewline
                }
            } while ($true)
            Write-Success "`nDocker läuft"
        }
    }
    
    # Node.js für Obsidian Plugin
    if (-not $SkipPlugin -and -not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Warning "Node.js nicht gefunden. Installiere Node.js..."
        choco install nodejs -y
        if ($LASTEXITCODE -ne 0) { Handle-Error "Node.js Installation fehlgeschlagen" }
        refreshenv
    }
    if (-not $SkipPlugin) { Write-Success "Node.js verfügbar" }
}

# 2. Repository Setup
function Initialize-Repository {
    Write-Info "`n2. Repository Setup..."
    
    # Erstelle fehlende Verzeichnisse
    @("data", "logs", "data\documents", "data\temp", "ssl") | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }
    
    # __init__.py Dateien erstellen
    Get-ChildItem -Path "src" -Recurse -Directory | ForEach-Object {
        $initFile = Join-Path $_.FullName "__init__.py"
        if (-not (Test-Path $initFile)) {
            New-Item -ItemType File -Path $initFile -Force | Out-Null
        }
    }
    
    Write-Success "Repository-Struktur vorbereitet"
}

# 3. Python Environment
function Initialize-PythonEnv {
    Write-Info "`n3. Python Virtual Environment einrichten..."
    
    # Alte venv entfernen falls vorhanden
    if (Test-Path "venv") {
        Remove-Item -Recurse -Force "venv"
    }
    
    # Neue venv erstellen
    python -m venv venv
    if ($LASTEXITCODE -ne 0) { Handle-Error "Virtual Environment konnte nicht erstellt werden" }
    
    # Aktivieren
    & "venv\Scripts\Activate.ps1"
    
    # Pip upgrade
    python -m pip install --upgrade pip
    
    # Requirements installieren
    Write-Info "Installiere Python-Pakete..."
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Handle-Error "Python-Pakete konnten nicht installiert werden" }
    
    Write-Success "Python Environment eingerichtet"
}

# 4. Environment Variables
function Initialize-EnvFile {
    Write-Info "`n4. Environment-Variablen konfigurieren..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
        } else {
            # .env.example erstellen
            @"
# LLM API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Database Connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

CHROMA_HOST=localhost
CHROMA_PORT=8000

# LLM Routing Preferences
CLASSIFIER_MODEL=gemini-pro
EXTRACTOR_MODEL=gpt-4-turbo-preview
SYNTHESIZER_MODEL=claude-3-opus-20240229
VALIDATOR_MODEL_1=gpt-4-turbo-preview
VALIDATOR_MODEL_2=claude-3-opus-20240229
"@ | Out-File -FilePath ".env.example" -Encoding UTF8
            Copy-Item ".env.example" ".env"
        }
        
        Write-Warning ".env Datei erstellt. Bitte API-Keys eintragen!"
        Write-Info "Öffne .env in Editor..."
        
        # Versuche Editor zu öffnen
        if (Get-Command code -ErrorAction SilentlyContinue) {
            code .env
        } elseif (Get-Command notepad -ErrorAction SilentlyContinue) {
            notepad .env
        } else {
            Start-Process .env
        }
        
        Read-Host "Drücken Sie Enter nachdem Sie die API-Keys eingetragen haben"
    }
    
    Write-Success "Environment-Variablen konfiguriert"
}

# 5. Docker Services
function Initialize-DockerServices {
    if ($SkipDocker) {
        Write-Warning "Docker-Setup übersprungen"
        return
    }
    
    Write-Info "`n5. Docker Services starten..."
    
    # Docker Compose Datei prüfen
    if (-not (Test-Path "docker-compose.yml")) {
        Handle-Error "docker-compose.yml nicht gefunden. Bitte Datei manuell erstellen"
    }
    
    # Services stoppen falls sie laufen
    docker-compose down 2>$null
    
    # Services starten
    Write-Info "Starte Docker Services..."
    docker-compose up -d neo4j chromadb redis
    if ($LASTEXITCODE -ne 0) { Handle-Error "Docker Services konnten nicht gestartet werden" }
    
    # Warten auf Services
    Write-Info "Warte auf Service-Bereitschaft..."
    
    # Neo4j health check
    Write-Host "Warte auf Neo4j" -NoNewline
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7474" -TimeoutSec 2 -ErrorAction Stop
            Write-Host ""
            Write-Success "Neo4j bereit"
            break
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
            if ($i -eq 30) {
                Write-Host ""
                Write-Warning "Neo4j braucht länger als erwartet"
            }
        }
    }
    
    # ChromaDB health check
    Write-Host "Warte auf ChromaDB" -NoNewline
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/heartbeat" -TimeoutSec 2 -ErrorAction Stop
            Write-Host ""
            Write-Success "ChromaDB bereit"
            break
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
            if ($i -eq 30) {
                Write-Host ""
                Write-Warning "ChromaDB braucht länger als erwartet"
            }
        }
    }
    
    Write-Success "Docker Services gestartet"
}

# 6. System testen
function Test-System {
    Write-Info "`n6. System testen..."
    
    # Aktiviere venv für Tests
    & "venv\Scripts\Activate.ps1"
    
    # Python imports testen
    Write-Info "Teste Python-Imports..."
    python -c "from src.config.settings import settings; print('Settings geladen')"
    if ($LASTEXITCODE -eq 0) { 
        Write-Success "Python-Imports OK" 
    } else { 
        Write-Warning "Import-Fehler" 
    }
    
    # CLI testen
    Write-Info "Teste CLI..."
    python -m src.cli --help | Out-Null
    if ($LASTEXITCODE -eq 0) { 
        Write-Success "CLI funktioniert" 
    } else { 
        Write-Warning "CLI-Fehler" 
    }
    
    if (-not $SkipDocker) {
        # Verbindungen testen
        python -c @"
try:
    from src.storage.neo4j_client import Neo4jClient
    neo4j = Neo4jClient()
    neo4j.close()
    print('✅ Neo4j-Verbindung OK')
except Exception as e:
    print(f'❌ Neo4j-Fehler: {e}')

try:
    from src.storage.chroma_client import ChromaClient
    chroma = ChromaClient()
    print('✅ ChromaDB-Verbindung OK')
except Exception as e:
    print(f'❌ ChromaDB-Fehler: {e}')
"@
    }
}

# 7. Obsidian Plugin
function Initialize-ObsidianPlugin {
    if ($SkipPlugin) {
        Write-Warning "Obsidian Plugin-Setup übersprungen"
        return
    }
    
    Write-Info "`n7. Obsidian Plugin einrichten..."
    
    $install = Read-Host "Möchten Sie das Obsidian Plugin installieren? (j/n)"
    if ($install -match "^[Jj]") {
        if (Test-Path $PluginPath) {
            Push-Location $PluginPath
            
            Write-Info "Installiere Node-Dependencies..."
            npm install
            if ($LASTEXITCODE -ne 0) { Write-Warning "npm install fehlgeschlagen" }
            
            # Installiere D3-Typen falls nicht vorhanden
            npm list @types/d3 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Info "Installiere TypeScript-Typen..."
                npm install --save-dev @types/d3
                if ($LASTEXITCODE -ne 0) { Write-Warning "TypeScript-Typen Installation fehlgeschlagen" }
            }
            
            Write-Info "Baue Plugin..."
            npm run build
            if ($LASTEXITCODE -ne 0) { Write-Warning "Plugin-Build fehlgeschlagen" }
            
            # Obsidian Plugin-Verzeichnis finden
            $obsidianLocal = "$env:APPDATA\Obsidian"
            $obsidianRoaming = "$env:LOCALAPPDATA\Obsidian"
            
            if (Test-Path $obsidianLocal) {
                Write-Success "Obsidian Plugin vorbereitet (AppData\Roaming)"
                Write-Info ""
                Write-Info "🔍 Verwenden Sie diese Skripte:"
                Write-Info "  .\setup-obsidian.ps1          - All-in-One Plugin Setup (empfohlen)"
                Write-Info "  .\install-obsidian-plugin.ps1 - Manuelle Plugin-Installation"
                Write-Info ""
                Write-Info "Oder manuell kopieren nach:"
                Write-Info "$obsidianLocal\IhrVault\.obsidian\plugins\"
            } elseif (Test-Path $obsidianRoaming) {
                Write-Success "Obsidian Plugin vorbereitet (AppData\Local)"
                Write-Info ""
                Write-Info "🔍 Verwenden Sie diese Skripte:"
                Write-Info "  .\setup-obsidian.ps1          - All-in-One Plugin Setup (empfohlen)"
                Write-Info "  .\install-obsidian-plugin.ps1 - Manuelle Plugin-Installation"
                Write-Info ""
                Write-Info "Oder manuell kopieren nach:"
                Write-Info "$obsidianRoaming\IhrVault\.obsidian\plugins\"
            } else {
                Write-Warning "Obsidian-Verzeichnis nicht gefunden"
                Write-Info "Mögliche Pfade:"
                Write-Info "  - %APPDATA%\Obsidian\IhrVault\.obsidian\plugins\"
                Write-Info "  - %LOCALAPPDATA%\Obsidian\IhrVault\.obsidian\plugins\"
                Write-Info "Bitte kopieren Sie das Plugin manuell nach einem dieser Pfade."
            }
            
            Pop-Location
        } else {
            Write-Warning "Obsidian Plugin-Verzeichnis nicht gefunden"
        }
    }
}

# 8. Startskripte erstellen
function New-StartScripts {
    Write-Info "`n8. Erstelle Startskripte..."
    
    # API Start-Skript (PowerShell)
    @"
# start-api.ps1
& "venv\Scripts\Activate.ps1"
`$env:PYTHONPATH = "`$env:PYTHONPATH;`$PWD"
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080
"@ | Out-File -FilePath "start-api.ps1" -Encoding UTF8
    
    # CLI Wrapper (PowerShell)
    @"
# ki-cli.ps1
param([Parameter(ValueFromRemainingArguments=`$true)]`$args)
& "venv\Scripts\Activate.ps1"
`$env:PYTHONPATH = "`$env:PYTHONPATH;`$PWD"
python -m src.cli @args
"@ | Out-File -FilePath "ki-cli.ps1" -Encoding UTF8
    
    # Docker Start-Skript (PowerShell)
    @"
# start-services.ps1
docker-compose up -d neo4j chromadb redis
Write-Host "Warte auf Services..."
Start-Sleep -Seconds 10
docker-compose ps
"@ | Out-File -FilePath "start-services.ps1" -Encoding UTF8
    
    # Batch-Wrapper für einfache Verwendung
    @"
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0start-api.ps1" %*
"@ | Out-File -FilePath "start-api.bat" -Encoding ASCII
    
    @"
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0ki-cli.ps1" %*
"@ | Out-File -FilePath "ki-cli.bat" -Encoding ASCII
    
    Write-Success "Startskripte erstellt"
}

# 9. Finale Instruktionen
function Show-FinalInstructions {
    Write-Success "`n=== Setup abgeschlossen! ==="
    Write-Info ""
    Write-Info "📋 Nächste Schritte:"
    Write-Info ""
    Write-Info "1. API-Keys in .env eintragen (falls noch nicht geschehen)"
    Write-Info "   notepad .env"
    Write-Info ""
    Write-Info "2. Services starten:"
    Write-Info "   .\start-services.ps1  # Docker Services"
    Write-Info "   .\start-api.ps1       # API Server"
    Write-Info ""
    Write-Info "3. CLI verwenden:"
    Write-Info "   .\ki-cli.ps1 query `"Ihre Frage`""
    Write-Info "   .\ki-cli.ps1 process dokument.pdf"
    Write-Info "   .\ki-cli.ps1 stats"
    Write-Info ""
    Write-Info "   ODER mit Batch-Dateien:"
    Write-Info "   ki-cli.bat query `"Ihre Frage`""
    Write-Info ""
    Write-Info "4. Web-Interface:"
    Write-Info "   API Docs: http://localhost:8080/docs"
    Write-Info "   Neo4j:    http://localhost:7474 (neo4j/password)"
    Write-Info ""
    Write-Info "5. Obsidian Plugin:"
    Write-Info "   .\setup-obsidian.ps1          # All-in-One Setup (empfohlen)"
    Write-Info "   - Plugin in Obsidian aktivieren"
    Write-Info "   - API URL: http://localhost:8080"
    Write-Info ""
    Write-Info "📚 Dokumentation: siehe README.md"
    Write-Info "❓ Bei Problemen: siehe $LogFile"
}

# Hauptprogramm
function Main {
    try {
        Test-Prerequisites
        Initialize-Repository
        Initialize-PythonEnv
        Initialize-EnvFile
        Initialize-DockerServices
        Test-System
        Initialize-ObsidianPlugin
        New-StartScripts
        Show-FinalInstructions
    } catch {
        Handle-Error "Unerwarteter Fehler: $($_.Exception.Message)"
    } finally {
        Stop-Transcript
    }
}

# Ausführen
Main 