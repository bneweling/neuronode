# find-obsidian-paths.ps1 - Obsidian Vault-Pfade finden und Plugin installieren (Windows)

Write-Host "🔍 Suche Obsidian Vault-Pfade..." -ForegroundColor Blue
Write-Host ""

# Obsidian Konfigurationspfade
$ObsidianConfig = "$env:APPDATA\Obsidian\obsidian.json"
$ObsidianLocalConfig = "$env:LOCALAPPDATA\Obsidian\obsidian.json"

# Plugin-Quellpfad
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$PluginSource = "$ScriptDir\..\..\..\obsidian-ki-plugin"

if (-not (Test-Path $PluginSource)) {
    Write-Host "❌ Plugin-Verzeichnis nicht gefunden: $PluginSource" -ForegroundColor Red
    Write-Host "Bitte stellen Sie sicher, dass das obsidian-ki-plugin Verzeichnis existiert." -ForegroundColor Yellow
    exit 1
}

# Funktion zum Lesen der Obsidian-Konfiguration
function Get-ObsidianVaults($configPath) {
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath | ConvertFrom-Json
            if ($config.vaults) {
                return $config.vaults.PSObject.Properties | ForEach-Object { $_.Value.path }
            }
        } catch {
            Write-Host "⚠️  Fehler beim Lesen von $configPath" -ForegroundColor Yellow
        }
    }
    return @()
}

# Sammle alle Vault-Pfade
$allVaults = @()
$allVaults += Get-ObsidianVaults $ObsidianConfig
$allVaults += Get-ObsidianVaults $ObsidianLocalConfig
$allVaults = $allVaults | Where-Object { $_ -and (Test-Path $_) } | Sort-Object -Unique

if ($allVaults.Count -eq 0) {
    Write-Host "❌ Keine Obsidian Vaults gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Mögliche Ursachen:" -ForegroundColor Yellow
    Write-Host "  - Obsidian ist nicht installiert"
    Write-Host "  - Keine Vaults erstellt"
    Write-Host "  - Konfigurationsdateien nicht gefunden"
    Write-Host ""
    Write-Host "Konfigurationspfade geprüft:" -ForegroundColor Cyan
    Write-Host "  - $ObsidianConfig"
    Write-Host "  - $ObsidianLocalConfig"
    exit 1
}

Write-Host "📁 Gefundene Obsidian Vaults:" -ForegroundColor Green
for ($i = 0; $i -lt $allVaults.Count; $i++) {
    $vault = $allVaults[$i]
    $pluginPath = "$vault\.obsidian\plugins\ki-wissenssystem"
    $installed = Test-Path $pluginPath
    $status = if ($installed) { "✅ Installiert" } else { "❌ Nicht installiert" }
    Write-Host "  [$($i + 1)] $vault $status"
}

Write-Host ""
Write-Host "Optionen:" -ForegroundColor Cyan
Write-Host "  [1-$($allVaults.Count)] Plugin in spezifischen Vault installieren"
Write-Host "  [a] Plugin in alle Vaults installieren"
Write-Host "  [q] Beenden"
Write-Host ""

$choice = Read-Host "Ihre Wahl"

if ($choice -eq "q") {
    Write-Host "Abgebrochen." -ForegroundColor Yellow
    exit 0
}

$targetVaults = @()
if ($choice -eq "a") {
    $targetVaults = $allVaults
    Write-Host "📦 Installiere Plugin in alle Vaults..." -ForegroundColor Blue
} elseif ($choice -match '^\d+$' -and [int]$choice -ge 1 -and [int]$choice -le $allVaults.Count) {
    $targetVaults = @($allVaults[[int]$choice - 1])
    Write-Host "📦 Installiere Plugin in gewählten Vault..." -ForegroundColor Blue
} else {
    Write-Host "❌ Ungültige Auswahl!" -ForegroundColor Red
    exit 1
}

# Plugin installieren
$success = 0
$total = $targetVaults.Count

foreach ($vault in $targetVaults) {
    $pluginDir = "$vault\.obsidian\plugins\ki-wissenssystem"
    
    try {
        # Plugin-Verzeichnis erstellen
        if (-not (Test-Path $pluginDir)) {
            New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null
        }
        
        # Plugin-Dateien kopieren
        Copy-Item "$PluginSource\main.js" $pluginDir -Force
        Copy-Item "$PluginSource\manifest.json" $pluginDir -Force
        Copy-Item "$PluginSource\styles.css" $pluginDir -Force
        
        Write-Host "✅ Plugin installiert in: $vault" -ForegroundColor Green
        $success++
    } catch {
        Write-Host "❌ Fehler bei Installation in $vault`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
if ($success -eq $total) {
    Write-Host "🎉 Plugin erfolgreich in $success von $total Vaults installiert!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Plugin in $success von $total Vaults installiert." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Nächste Schritte:" -ForegroundColor Cyan
Write-Host "  1. Obsidian neu starten"
Write-Host "  2. Settings → Community Plugins → 'KI-Wissenssystem' aktivieren"
Write-Host "  3. Plugin konfigurieren (API URL: http://localhost:8080)" 