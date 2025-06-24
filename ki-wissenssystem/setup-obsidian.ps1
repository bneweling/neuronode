# setup-obsidian.ps1 - All-in-One Obsidian Plugin Setup für Windows

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

Write-Info "🔌 KI-Wissenssystem Obsidian Plugin Setup"
Write-Host ""

# Funktion zur Plugin-Installation
function Install-PluginToVault {
    param(
        [string]$VaultName,
        [string]$VaultPath,
        [string]$PluginSource
    )
    
    $pluginTarget = Join-Path $VaultPath ".obsidian\plugins\obsidian-ki-plugin"
    
    Write-Info "📦 Installiere Plugin in Vault: $VaultName"
    
    # Erstelle Verzeichnisse falls nötig
    $pluginsDir = Join-Path $VaultPath ".obsidian\plugins"
    if (-not (Test-Path $pluginsDir)) {
        New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
    }
    
    # Prüfe ob Plugin bereits existiert
    if (Test-Path $pluginTarget) {
        $overwrite = Read-Host "⚠️  Plugin bereits vorhanden. Überschreiben? (j/n)"
        if ($overwrite -notmatch "^[Jj]") {
            Write-Host "Überspringe $VaultName"
            return
        }
        Remove-Item -Path $pluginTarget -Recurse -Force
    }
    
    # Kopiere Plugin-Dateien
    New-Item -ItemType Directory -Path $pluginTarget -Force | Out-Null
    Copy-Item "$PluginSource\main.js" $pluginTarget
    Copy-Item "$PluginSource\manifest.json" $pluginTarget
    Copy-Item "$PluginSource\styles.css" $pluginTarget
    
    if ($?) {
        Write-Success "Plugin erfolgreich installiert in: $VaultName"
    } else {
        Write-Error "Plugin-Installation fehlgeschlagen für: $VaultName"
    }
}

# 1. Prüfe Plugin-Quellverzeichnis
$PluginSource = "..\obsidian-ki-plugin"
Write-Info "📦 Prüfe Plugin-Quellverzeichnis..."

if (-not (Test-Path $PluginSource)) {
    Write-Error "Plugin-Quellverzeichnis nicht gefunden: $PluginSource"
    Write-Host "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert."
    exit 1
}

# 2. Prüfe/Baue Plugin falls nötig
if (-not (Test-Path "$PluginSource\main.js")) {
    Write-Warning "Plugin noch nicht gebaut. Baue Plugin..."
    Push-Location $PluginSource
    
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Plugin-Build fehlgeschlagen"
            Pop-Location
            exit 1
        }
        Pop-Location
    } else {
        Write-Error "npm nicht gefunden. Bitte installieren Sie Node.js"
        Pop-Location
        exit 1
    }
}

Write-Success "Plugin ist bereit"

# 3. Finde Obsidian-Vaults
Write-Info "🔍 Suche nach Obsidian-Installationen..."

$obsidianLocal = "$env:APPDATA\Obsidian"
$obsidianRoaming = "$env:LOCALAPPDATA\Obsidian"

$obsidianPath = $null
if (Test-Path "$obsidianLocal\obsidian.json") {
    $obsidianPath = $obsidianLocal
    Write-Success "Obsidian gefunden (AppData\Roaming)"
} elseif (Test-Path "$obsidianRoaming\obsidian.json") {
    $obsidianPath = $obsidianRoaming
    Write-Success "Obsidian gefunden (AppData\Local)"
} else {
    Write-Error "Obsidian-Installation nicht gefunden"
    Write-Host "Bitte starten Sie Obsidian mindestens einmal."
    exit 1
}

# Parse und zeige Vaults
Write-Host ""
Write-Info "📁 Verfügbare Vaults:"

try {
    $configPath = Join-Path $obsidianPath "obsidian.json"
    $config = Get-Content $configPath | ConvertFrom-Json
    
    if (-not $config.vaults -or $config.vaults.Count -eq 0) {
        Write-Host "Keine Vaults gefunden."
        exit 1
    }
    
    $vaultList = @()
    $i = 1
    
    foreach ($vaultId in $config.vaults.PSObject.Properties.Name) {
        $vault = $config.vaults.$vaultId
        $vaultPath = $vault.path
        $vaultName = Split-Path $vaultPath -Leaf
        
        $vaultList += @{
            Number = $i
            Name = $vaultName
            Path = $vaultPath
        }
        
        Write-Host "$i. $vaultName"
        Write-Host "   Pfad: $vaultPath"
        
        # Prüfe Plugin-Status
        $pluginPath = Join-Path $vaultPath ".obsidian\plugins\obsidian-ki-plugin"
        if (Test-Path $pluginPath) {
            Write-Host "   Status: ✅ Plugin bereits installiert"
        } else {
            Write-Host "   Status: ⚪ Plugin nicht installiert"
        }
        Write-Host ""
        $i++
    }
    
    # 4. Benutzer-Auswahl
    $choice = Read-Host "Welchen Vault möchten Sie verwenden? (Nummer eingeben oder 'a' für alle)"
    
    if ($choice -eq "a" -or $choice -eq "A") {
        # Installiere in alle Vaults
        Write-Info "📦 Installiere Plugin in alle Vaults..."
        foreach ($vault in $vaultList) {
            Install-PluginToVault -VaultName $vault.Name -VaultPath $vault.Path -PluginSource $PluginSource
        }
    } else {
        # Installiere in ausgewählten Vault
        $selectedVault = $vaultList | Where-Object { $_.Number -eq [int]$choice }
        
        if (-not $selectedVault) {
            Write-Error "Ungültige Auswahl"
            exit 1
        }
        
        Install-PluginToVault -VaultName $selectedVault.Name -VaultPath $selectedVault.Path -PluginSource $PluginSource
    }
    
} catch {
    Write-Error "Fehler beim Lesen der Konfiguration: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
Write-Success "🎉 Plugin-Setup abgeschlossen!"
Write-Host ""
Write-Info "📋 Nächste Schritte:"
Write-Host "1. Starten Sie Obsidian neu"
Write-Host "2. Gehen Sie zu Settings → Community Plugins"
Write-Host "3. Aktivieren Sie 'KI-Wissenssystem'"
Write-Host "4. Konfigurieren Sie die API-URL: http://localhost:8080" 