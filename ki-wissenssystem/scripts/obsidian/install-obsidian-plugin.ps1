# install-obsidian-plugin.ps1 - Manuelle Plugin-Installation (Windows)

param(
    [string]$VaultPath = "",
    [switch]$Force = $false
)

Write-Host "📦 KI-Wissenssystem Plugin Installation" -ForegroundColor Blue
Write-Host ""

# Plugin-Quellpfad
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$PluginSource = "$ScriptDir\..\..\..\obsidian-ki-plugin"

if (-not (Test-Path $PluginSource)) {
    Write-Host "❌ Plugin-Verzeichnis nicht gefunden: $PluginSource" -ForegroundColor Red
    Write-Host "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert." -ForegroundColor Yellow
    exit 1
}

# Vault-Pfad bestimmen
if (-not $VaultPath) {
    $VaultPath = Read-Host "Geben Sie den Pfad zu Ihrem Obsidian Vault ein"
}

if (-not (Test-Path $VaultPath)) {
    Write-Host "❌ Vault-Pfad nicht gefunden: $VaultPath" -ForegroundColor Red
    exit 1
}

# Plugin-Zielverzeichnis
$PluginDir = "$VaultPath\.obsidian\plugins\ki-wissenssystem"

# Prüfe ob Plugin bereits installiert ist
if ((Test-Path $PluginDir) -and -not $Force) {
    Write-Host "⚠️  Plugin bereits installiert in: $PluginDir" -ForegroundColor Yellow
    $overwrite = Read-Host "Überschreiben? (j/n)"
    if ($overwrite -ne "j" -and $overwrite -ne "J") {
        Write-Host "Installation abgebrochen." -ForegroundColor Yellow
        exit 0
    }
}

try {
    # Plugin-Verzeichnis erstellen
    if (-not (Test-Path $PluginDir)) {
        New-Item -ItemType Directory -Path $PluginDir -Force | Out-Null
        Write-Host "📁 Plugin-Verzeichnis erstellt: $PluginDir" -ForegroundColor Cyan
    }
    
    # Prüfe ob Plugin gebaut wurde
    if (-not (Test-Path "$PluginSource\main.js")) {
        Write-Host "⚠️  Plugin nicht gebaut. Baue Plugin..." -ForegroundColor Yellow
        Push-Location $PluginSource
        try {
            if (Get-Command npm -ErrorAction SilentlyContinue) {
                npm install
                npm run build
                Write-Host "✅ Plugin erfolgreich gebaut" -ForegroundColor Green
            } else {
                Write-Host "❌ npm nicht gefunden. Bitte Node.js installieren." -ForegroundColor Red
                exit 1
            }
        } finally {
            Pop-Location
        }
    }
    
    # Plugin-Dateien kopieren
    Write-Host "📋 Kopiere Plugin-Dateien..." -ForegroundColor Cyan
    Copy-Item "$PluginSource\main.js" $PluginDir -Force
    Copy-Item "$PluginSource\manifest.json" $PluginDir -Force
    Copy-Item "$PluginSource\styles.css" $PluginDir -Force
    
    Write-Host "✅ Plugin erfolgreich installiert!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Installation-Pfad: $PluginDir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Nächste Schritte:" -ForegroundColor Cyan
    Write-Host "  1. Obsidian neu starten"
    Write-Host "  2. Settings → Community Plugins → 'KI-Wissenssystem' aktivieren"
    Write-Host "  3. Plugin konfigurieren:"
    Write-Host "     - API URL: http://localhost:8080"
    Write-Host "     - Stellen Sie sicher, dass das Backend läuft"
    Write-Host ""
    Write-Host "🚀 Backend starten mit: .\start-all.ps1" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Fehler bei der Installation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 