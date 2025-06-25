# 📁 Scripts Verzeichnis

Dieses Verzeichnis enthält alle Skripte für das KI-Wissenssystem, organisiert nach Plattform und Funktion.

## 📂 Ordnerstruktur

```
scripts/
├── setup/           # Installations-Skripte
│   ├── setup.sh           # macOS/Linux Setup
│   ├── setup.ps1          # Windows Setup
│   └── requirements-dev.txt  # Entwicklungsabhängigkeiten
├── obsidian/        # Obsidian Plugin-Skripte
│   ├── setup-obsidian.sh     # macOS/Linux Plugin Setup
│   ├── setup-obsidian.ps1    # Windows Plugin Setup
│   ├── find-obsidian-paths.sh  # Vault-Pfade finden
│   └── install-obsidian-plugin.sh  # Manuelle Installation
├── system/          # System-Management
│   ├── start-all.sh       # Vollständiger Start (macOS/Linux)
│   ├── start-all.ps1      # Vollständiger Start (Windows)
│   ├── stop-all.sh        # Vollständiger Stop (macOS/Linux)
│   ├── stop-all.ps1       # Vollständiger Stop (Windows)
│   ├── start-services.sh  # Nur Docker Services
│   └── start-services.ps1 # Nur Docker Services (Windows)
├── api/             # API-spezifische Skripte
│   ├── start-api.sh       # API Server (macOS/Linux)
│   ├── start-api.ps1      # API Server (Windows)
│   └── start-api.bat      # API Server (Windows Batch)
├── cli/             # CLI-Tools
│   ├── ki-cli.sh          # CLI Wrapper (macOS/Linux)
│   ├── ki-cli.ps1         # CLI Wrapper (Windows)
│   └── ki-cli.bat         # CLI Wrapper (Windows Batch)
└── dev/             # Entwicklungs-Tools
    ├── dev-mode.sh        # Entwicklungs-Modus (macOS/Linux)
    ├── dev-mode.ps1       # Entwicklungs-Modus (Windows)
    └── test-setup.sh      # Setup-Tests
```

## 🚀 Schnellstart

### Erstmalige Installation
```bash
# macOS/Linux
./scripts/setup/setup.sh

# Windows (PowerShell als Administrator)
.\scripts\setup\setup.ps1
```

### System starten
```bash
# macOS/Linux
./scripts/system/start-all.sh

# Windows
.\scripts\system\start-all.ps1
```

### Obsidian Plugin installieren
```bash
# macOS/Linux
./scripts/obsidian/setup-obsidian.sh

# Windows
.\scripts\obsidian\setup-obsidian.ps1
```

### Entwicklung
```bash
# macOS/Linux
./scripts/dev/dev-mode.sh

# Windows
.\scripts\dev\dev-mode.ps1
```

## 📋 Vorteile der neuen Struktur

1. **Bessere Organisation** - Skripte nach Funktion gruppiert
2. **Plattform-Klarheit** - .sh für Unix, .ps1 für Windows
3. **Einfache Navigation** - Intuitive Ordnerstruktur
4. **Wartbarkeit** - Verwandte Skripte zusammen
5. **Skalierbarkeit** - Einfach neue Kategorien hinzufügen

## 🔄 Migration

Die alte Struktur (Skripte im Hauptverzeichnis) wird noch unterstützt, aber die neue Struktur ist empfohlen für:
- Neue Installationen
- Entwicklungsumgebungen
- Bessere Übersicht

## 🛠️ Entwicklung

Neue Skripte sollten in der entsprechenden Kategorie abgelegt werden:
- Setup-bezogen → `scripts/setup/`
- System-Management → `scripts/system/`
- Plugin-bezogen → `scripts/obsidian/`
- Entwicklung → `scripts/dev/` 