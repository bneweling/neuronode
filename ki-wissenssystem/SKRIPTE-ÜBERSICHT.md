# 📋 Skripte-Übersicht

Vollständige Übersicht aller verfügbaren Skripte für das KI-Wissenssystem (Linux/macOS).

## 🚀 System-Management

### Vollständiger Start/Stop
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `start-all.sh` | macOS/Linux | Vollständiger System-Start |
| `stop-all.sh` | macOS/Linux | Vollständiger System-Stop |

### Services-Management
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `start-services.sh` | macOS/Linux | Nur Docker Services starten |
| `start-api.sh` | macOS/Linux | Nur API Server starten |

## ⚙️ Setup und Installation

### Hauptinstallation
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `setup.sh` | macOS/Linux | Vollständige System-Installation |

### Entwicklungstools
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `scripts/setup/install-dev-tools.sh` | macOS/Linux | Entwicklungstools installieren |
| `scripts/setup/requirements-dev.txt` | Alle | Entwicklungsabhängigkeiten |

## 📱 Obsidian Plugin

### Plugin-Installation
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `scripts/obsidian/setup-obsidian.sh` | macOS/Linux | All-in-One Plugin Setup |
| `scripts/obsidian/find-obsidian-paths.sh` | macOS/Linux | Vault-Pfade finden + Installation |
| `scripts/obsidian/install-obsidian-plugin.sh` | macOS/Linux | Erweiterte Plugin-Installation |
| `scripts/obsidian/update-obsidian-plugin.sh` | macOS/Linux | Plugin-Updates mit Backup |

## 🛠️ CLI Tools

### Kommandozeile
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `ki-cli.sh` | macOS/Linux | CLI Wrapper |
| `scripts/cli/ki-cli.sh` | macOS/Linux | CLI Implementation |

## 🚀 Entwicklung

### Entwicklungs-Modus
| Skript | Plattform | Beschreibung |
|--------|-----------|--------------|
| `dev-mode.sh` | macOS/Linux | Interaktiver Entwicklungs-Modus |
| `scripts/dev/dev-mode.sh` | macOS/Linux | Entwicklungs-Implementierung |

## 📁 Empfohlene Nutzung

### Für Endbenutzer (einfach):
```bash
# macOS/Linux
./start-all.sh         # System starten
./ki-cli.sh stats      # CLI verwenden
./stop-all.sh          # System stoppen
```

### Für Entwickler:
```bash
# macOS/Linux
./setup.sh                     # Einmalige Installation
./scripts/setup/install-dev-tools.sh  # Entwicklungstools
./scripts/obsidian/setup-obsidian.sh  # Plugin installieren
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

1. **Skript nicht ausführbar** (macOS/Linux):
   ```bash
   chmod +x skript-name.sh
   ```

2. **Docker nicht verfügbar**:
   - macOS: Docker Desktop starten
   - Linux: `sudo systemctl start docker`

## 📊 Skript-Statistiken

- **Gesamt**: 15+ aktive Skripte
- **Platform-Support**: Linux/macOS optimiert
- **Organisation**: Strukturiert in `scripts/` Unterordnern
- **Benutzerfreundlichkeit**: Einfache Bash-Skripte

## 🎯 Nächste Schritte

1. **Erste Installation**: `./setup.sh`
2. **Plugin installieren**: `./scripts/obsidian/setup-obsidian.sh`
3. **System starten**: `./start-all.sh`
4. **Entwicklung**: `./dev-mode.sh`

## ✅ Status: Konsolidiert & Production-Ready!

**Streamlined Linux/macOS-Architektur:**
- 📂 `scripts/` Ordner mit kategorisierten Skripten
- 🛠️ Fokus auf macOS/Linux-Kompatibilität
- 📱 Einheitliche Bash-Implementierung
- 🚀 Optimiert für Produktionsreife

Alle Skripte sind vollständig dokumentiert und produktionsbereit! 🎉 