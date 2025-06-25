# 🔄 KI-Wissenssystem Restart & Profil-Wechsel Anleitung

## Übersicht

Das KI-Wissenssystem verfügt über erweiterte Restart- und Profil-Wechsel-Funktionen, die automatische Neustarts nach Konfigurationsänderungen ermöglichen.

## 🚀 Quick Start

### Einfacher Neustart
```bash
# Schneller Neustart
./ki-restart.sh restart

# Oder ausführlich
./switch-model-profile.sh --restart
```

### Profil-Wechsel mit automatischem Restart
```bash
# Zu Gemini-Only wechseln (perfekt für Ihren neuen API Key!)
./ki-restart.sh gemini

# Zu anderen Profilen wechseln
./ki-restart.sh premium
./ki-restart.sh balanced
./ki-restart.sh openai
```

## 📋 Verfügbare Kommandos

### ki-restart.sh (Einfache Bedienung)
```bash
./ki-restart.sh [KOMMANDO]

System-Kommandos:
  stop       - System stoppen
  start      - System starten  
  restart, r - System neustarten
  status, s  - Aktuellen Status anzeigen

Profil-Wechsel mit Restart:
  gemini     - Zu Gemini-Only wechseln
  openai     - Zu OpenAI-Only wechseln
  premium    - Zu Premium wechseln
  balanced   - Zu Balanced wechseln
  cost       - Zu Cost-Effective wechseln
```

### switch-model-profile.sh (Erweiterte Optionen)
```bash
./switch-model-profile.sh [PROFIL] [OPTIONEN]

Optionen:
  --show, -s     - Aktuelles Profil anzeigen
  --list, -l     - Alle Profile auflisten
  --restart, -r  - Automatischen Restart durchführen
  --fg           - Im Vordergrund starten
  --stop         - System stoppen
  --start        - System starten
  --interactive  - Interaktiver Modus
```

## 🎯 Anwendungsfälle

### 1. Nach .env Änderungen (z.B. neuer Gemini API Key)
```bash
# Einfacher Neustart reicht
./ki-restart.sh restart
```

### 2. Profil-Wechsel für Tests
```bash
# Zu Gemini-Only für Gemini API Tests
./ki-restart.sh gemini

# Zurück zu Premium für Vollbetrieb
./ki-restart.sh premium
```

### 3. System-Wartung
```bash
# System stoppen
./ki-restart.sh stop

# Wartungsarbeiten...

# System wieder starten
./ki-restart.sh start
```

### 4. Interaktiver Modus
```bash
# Interaktive Profil-Auswahl
./switch-model-profile.sh --interactive
```

## 🔧 Technische Details

### Automatische Prozess-Erkennung
Das System erkennt automatisch laufende KI-Wissenssystem-Prozesse:
- FastAPI/Uvicorn Server
- Neo4j Verbindungen
- ChromaDB Prozesse
- Python-Hauptprozesse

### Graceful Shutdown
1. **SIGTERM** - Höflicher Shutdown-Request
2. **10 Sekunden Wartezeit** - Zeit für sauberes Beenden
3. **SIGKILL** - Force Kill falls nötig

### Hintergrund vs. Vordergrund
```bash
# Standard: Im Hintergrund starten
./ki-restart.sh restart

# Im Vordergrund (für Debugging)
./switch-model-profile.sh --restart --fg
```

## 🎛️ Profile im Detail

### Gemini-Only (Optimal für Ihren API Key)
```
🤖 Modelle:
  • Classifier: gemini-2.5-flash
  • Extractor: gemini-2.5-pro  
  • Synthesizer: gemini-2.5-pro
  • Validator 1: gemini-2.0-flash
  • Validator 2: gemini-2.5-flash

💰 Kosten: Niedrig
⚡ Performance: Gut
🔑 Benötigt nur: Google API Key
```

### Premium (Alle APIs erforderlich)
```
🤖 Modelle:
  • Classifier: gemini-2.5-flash
  • Extractor: gpt-4.1
  • Synthesizer: claude-opus-4-20250514
  • Validator 1: gpt-4o
  • Validator 2: claude-sonnet-4-20250514

💰 Kosten: Hoch
⚡ Performance: Maximal
🔑 Benötigt: Google + OpenAI + Anthropic API Keys
```

## 🚨 Fehlerbehebung

### Problem: "psutil not found"
```bash
# Lösung: psutil installieren
pip install psutil
```

### Problem: "Keine laufenden Prozesse gefunden"
```bash
# Prüfen ob System läuft
./ki-restart.sh status

# Manuell starten
./ki-restart.sh start
```

### Problem: "API Key fehlt"
```bash
# .env Datei prüfen
cat .env

# Dann Neustart
./ki-restart.sh restart
```

## 📊 Status-Überwachung

### Aktuellen Status prüfen
```bash
./ki-restart.sh status
```

Zeigt an:
- ✅ Aktuelles Profil
- 🤖 Verwendete Modelle
- 🔑 Benötigte API Keys
- 💰 Kostenschätzung
- ⚡ Performance-Level

## 🎉 Tipps & Tricks

### 1. Alias erstellen
```bash
# In ~/.bashrc oder ~/.zshrc
alias ki='cd /path/to/ki-wissenssystem && ./ki-restart.sh'

# Dann einfach:
ki status
ki restart
ki gemini
```

### 2. Schnelle Profil-Tests
```bash
# Gemini testen
./ki-restart.sh gemini
# ... Tests durchführen ...

# Zurück zu Balanced
./ki-restart.sh balanced
```

### 3. Entwicklungsmodus
```bash
# Im Vordergrund für Live-Logs
./switch-model-profile.sh balanced --restart --fg
```

---

## ✅ Zusammenfassung

Mit den erweiterten Restart-Funktionen können Sie:
- 🔄 **Automatische Neustarts** nach Profil-Wechseln
- 🎯 **Einfache Kommandos** für häufige Aufgaben
- 🛠️ **Intelligente Prozess-Verwaltung** mit graceful shutdown
- 📊 **Status-Überwachung** in Echtzeit
- 🤖 **Schnelle Profil-Wechsel** für verschiedene Test-Szenarien

**Für Ihren neuen Gemini API Key ist das System jetzt optimal vorbereitet!** 🚀 