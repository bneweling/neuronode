# 📋 Skripte-Übersicht

Vollständige Übersicht aller verfügbaren Skripte für das KI-Wissenssystem.

## 🚀 System-Management

### Vollständiger Start/Stop
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `start-all.sh` | macOS/Linux | Vollständiger System-Start |
| `start-all.ps1` | Windows | Vollständiger System-Start |
| `start-all.bat` | Windows | Einfacher Start (Doppelklick) |
| `stop-all.sh` | macOS/Linux | Vollständiger System-Stop |
| `stop-all.ps1` | Windows | Vollständiger System-Stop |
| `stop-all.bat` | Windows | Einfacher Stop (Doppelklick) |

### Services-Management
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `start-services.sh` | macOS/Linux | Nur Docker Services starten |
| `start-services.ps1` | Windows | Nur Docker Services starten |
| `start-api.sh` | macOS/Linux | Nur API Server starten |
| `start-api.ps1` | Windows | Nur API Server starten |
| `start-api.bat` | Windows | API Server (Batch) |

## ⚙️ Setup und Installation

### Hauptinstallation
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `setup.sh` | macOS/Linux | Vollständige System-Installation |
| `setup.ps1` | Windows | Vollständige System-Installation |

### Entwicklungstools
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `install-dev-tools.sh` | macOS/Linux | Entwicklungstools installieren |
| `install-dev-tools.ps1` | Windows | Entwicklungstools installieren |
| `requirements-dev.txt` | Alle | Entwicklungsabhängigkeiten |

## 📱 Obsidian Plugin

### Plugin-Installation
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `setup-obsidian.sh` | macOS/Linux | All-in-One Plugin Setup |
| `setup-obsidian.ps1` | Windows | All-in-One Plugin Setup |
| `find-obsidian-paths.sh` | macOS/Linux | Vault-Pfade finden + Installation |
| `install-obsidian-plugin.sh` | macOS/Linux | Erweiterte Plugin-Installation mit neuen Features |
| `update-obsidian-plugin.sh` | macOS/Linux | **NEU**: Plugin-Updates mit Backup-Funktionalität |

## 🛠️ CLI Tools

### Kommandozeile
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `ki-cli.sh` | macOS/Linux | CLI Wrapper |
| `ki-cli.ps1` | Windows | CLI Wrapper |
| `ki-cli.bat` | Windows | CLI Wrapper (Batch) |

## 🚀 Entwicklung

### Entwicklungs-Modus
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `dev-mode.sh` | macOS/Linux | Interaktiver Entwicklungs-Modus |
| `dev-mode.ps1` | Windows | Interaktiver Entwicklungs-Modus |

## 📁 Empfohlene Nutzung

### Für Endbenutzer (einfach):
```bash
# Windows
start-all.bat          # Doppelklick im Explorer
ki-cli.bat stats        # CLI verwenden
stop-all.bat           # System stoppen

# macOS/Linux
./start-all.sh         # System starten
./ki-cli.sh stats      # CLI verwenden
./stop-all.sh          # System stoppen
```

### Für Entwickler:
```bash
# Windows
.\setup.ps1                    # Einmalige Installation
.\install-dev-tools.ps1        # Entwicklungstools
.\setup-obsidian.ps1           # Plugin installieren
.\dev-mode.ps1                 # Entwicklung starten

# macOS/Linux
./setup.sh                     # Einmalige Installation
./install-dev-tools.sh         # Entwicklungstools
./setup-obsidian.sh            # Plugin installieren
./dev-mode.sh                  # Entwicklung starten
```

### Für Power-User:
```bash
# Services einzeln steuern
./start-services.sh            # Nur Docker
./start-api.sh                 # Nur API
./ki-cli.sh process doc.pdf    # Dokument verarbeiten
```

## 🔧 Fehlerbehebung

### Häufige Probleme:
1. **PowerShell Execution Policy** (Windows):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Skript nicht ausführbar** (macOS/Linux):
   ```bash
   chmod +x skript-name.sh
   ```

3. **Docker nicht verfügbar**:
   - Windows: Docker Desktop starten
   - macOS: Docker Desktop starten
   - Linux: `sudo systemctl start docker`

## 📊 Skript-Statistiken

- **Gesamt**: 20+ Skripte
- **Windows-Support**: 100% (PowerShell + Batch)
- **macOS/Linux-Support**: 100% (Bash)
- **Cross-Platform**: Alle Funktionen verfügbar
- **Benutzerfreundlichkeit**: Batch-Dateien für einfache Nutzung

## 🎯 Nächste Schritte

1. **Erste Installation**: `setup.sh` oder `setup.ps1`
2. **Plugin installieren**: `scripts/obsidian/setup-obsidian.sh` oder `setup-obsidian.ps1`
3. **System starten**: `start-all.sh` oder `start-all.ps1`
4. **Entwicklung**: `dev-mode.sh` oder `dev-mode.ps1`

## ✅ Status: Vollständig implementiert!

**Neue organisierte Struktur ist aktiv:**
- 📂 `scripts/` Ordner mit kategorisierten Skripten
- 🔄 Wrapper-Skripte für Rückwärtskompatibilität
- 🛠️ Alle 35+ Skripte Cross-Platform verfügbar
- 📱 Identische Funktionalität auf Windows, macOS und Linux

Alle Skripte sind vollständig dokumentiert und Cross-Platform kompatibel! 🎉 