# 🔌 KI-Wissenssystem Plugin - Installationsanleitung

Komplette Anleitung für die Installation des erweiterten KI-Wissenssystem Plugins mit allen neuen Features.

## 🚀 Neue Features (Version 1.0.0)

### ✨ **Was ist neu?**
- 💬 **Persistente Chat-Historie** mit Sitzungsverwaltung
- 🔍 **Erweiterte Graph-Suche** mit 4 Suchalgorithmen
- ⚖️ **Einheitliche Workbench** mit 4 Layout-Modi
- 🕸️ **Verbesserte Graph-Visualisierung** für große Netze
- 📱 **Responsive Design** für Desktop und Mobile

## 📋 Voraussetzungen prüfen

### System-Anforderungen
```bash
# Node.js Version prüfen (mindestens v16)
node --version

# npm prüfen
npm --version

# Python 3 prüfen
python3 --version
```

### KI-Wissenssystem Backend
```bash
# Backend sollte laufen
curl http://localhost:8080/health
```

## 🔄 Installation (Neu oder Update)

### Option 1: Automatische Installation (Empfohlen)

```bash
# Für neue Installation:
cd ki-wissenssystem
./install-obsidian-plugin.sh

# Für Updates bestehender Installationen:
./update-obsidian-plugin.sh
```

### Option 2: Manuelle Installation

1. **Plugin bauen**:
```bash
cd obsidian-ki-plugin
npm install
npm run build
```

2. **Dateien kopieren**:
```bash
# Finden Sie Ihren Obsidian Vault Pfad
ls -la ~/Library/Application\ Support/obsidian/obsidian.json

# Plugin-Verzeichnis erstellen
mkdir -p "VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin"

# Dateien kopieren
cp main.js manifest.json styles.css "VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin/"
```

## ⚙️ Plugin-Konfiguration

### 1. Plugin aktivieren
1. Obsidian starten
2. Settings → Community Plugins
3. "KI-Wissenssystem" aktivieren
4. **Wichtig**: Obsidian neu starten für neue Features

### 2. API-Einstellungen
```
API-URL: http://localhost:8080
WebSocket-URL: ws://localhost:8080/ws/chat
API-Key: (Optional - leer lassen für lokale Nutzung)
```

### 3. Performance-Einstellungen
```
Max. Kontext-Knoten: 10 (für große Vaults anpassen)
Graph-Tiefe: 2 (Verbindungsebenen)
Max. Chat-Sessions: 50 (automatische Bereinigung)
```

## 🎯 Feature-Tests

### Chat-System testen
1. **Chat öffnen**: Ribbon Icon oder `Cmd+P` → "Open Knowledge Chat"
2. **Nachricht senden**: Test-Frage eingeben
3. **Historie prüfen**: 📚 Historie-Button klicken
4. **Session-Verwaltung**: Neue Session erstellen

### Graph-Suche testen
1. **Graph öffnen**: Graph Icon oder `Cmd+P` → "Open Knowledge Graph"
2. **Suche aktivieren**: 🔍 Suche-Button klicken
3. **Algorithmen testen**:
   - Semantische Suche
   - Exakte Suche
   - Fuzzy-Suche
   - Graph-Walk

### Workbench-Layouts testen
1. **Chat-View öffnen**: Sollte automatisch Workbench-Modus aktivieren
2. **Layout wechseln**: ⚖️ Layout-Buttons ausprobieren
3. **Panel-Interaktion**: Chat → Graph Synchronisation testen

## 🛠️ Troubleshooting

### Plugin lädt nicht
```bash
# 1. Build-Fehler prüfen
cd obsidian-ki-plugin
npm run build

# 2. Obsidian Console öffnen (Cmd+Option+I)
# Nach Fehlern suchen

# 3. Plugin-Dateien prüfen
ls -la VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin/
```

### Chat-Historie leer
```bash
# Plugin-Daten prüfen
cat VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin/data.json

# Backup wiederherstellen falls vorhanden
ls -la VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin.backup.*
```

### API-Verbindung fehlgeschlagen
```bash
# Backend-Status prüfen
curl http://localhost:8080/health

# WebSocket testen
# In Browser-Konsole:
new WebSocket('ws://localhost:8080/ws/chat')
```

### Graph-Performance Probleme
1. **Max. Kontext-Knoten reduzieren**: Settings → 5-10
2. **Filter verwenden**: Nur relevante Knoten anzeigen
3. **Layout-Modus wechseln**: Search-focused für bessere Performance

## 📊 Feature-Übersicht

| Feature | Status | Test-Methode |
|---------|--------|--------------|
| Chat-Historie | ✅ | 📚 Button klicken |
| Session-Management | ✅ | Neue Sessions erstellen |
| Semantische Suche | ✅ | Graph-Suche → Semantisch |
| Exakte Suche | ✅ | Graph-Suche → Exakt |
| Fuzzy-Suche | ✅ | Graph-Suche → Fuzzy |
| Graph-Walk | ✅ | Graph-Suche → Graph-Walk |
| Balanced Layout | ✅ | Layout-Button |
| Chat-Focused Layout | ✅ | Layout-Button |
| Graph-Focused Layout | ✅ | Layout-Button |
| Search-Focused Layout | ✅ | Layout-Button |
| Responsive Design | ✅ | Browser-Größe ändern |

## 🔄 Update-Prozess

### Automatisches Update
```bash
./update-obsidian-plugin.sh
# Folgen Sie den Anweisungen für:
# 1. Alle Installationen aktualisieren
# 2. Spezifische Installation wählen
# 3. Nur Backup erstellen
```

### Manuelles Update
```bash
# 1. Backup erstellen
cp -r VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin \
     VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin.backup.$(date +%Y%m%d)

# 2. Neues Plugin bauen
cd obsidian-ki-plugin
npm run build

# 3. Dateien ersetzen
cp main.js manifest.json styles.css VAULT_PATH/.obsidian/plugins/obsidian-ki-plugin/
```

## 🆘 Support & Logs

### Debug-Informationen sammeln
```javascript
// In Obsidian Developer Console (Cmd+Option+I):
console.log('Plugin Status:', app.plugins.plugins['obsidian-ki-plugin']);
console.log('Plugin Data:', await app.plugins.plugins['obsidian-ki-plugin'].loadData());
```

### Log-Dateien
```bash
# Obsidian Logs (macOS)
tail -f ~/Library/Logs/Obsidian/main.log

# Plugin-spezifische Logs in Obsidian Console
```

### Performance-Monitoring
```javascript
// Memory Usage
console.log('Memory:', performance.memory);

// Plugin Performance
console.time('GraphSearch');
// ... Graph-Suche ausführen ...
console.timeEnd('GraphSearch');
```

## ✅ Installation erfolgreich!

**Nach erfolgreicher Installation sollten Sie haben:**
- ✅ Chat mit persistenter Historie
- ✅ 4 Graph-Suchalgorithmen verfügbar
- ✅ 4 Layout-Modi funktionsfähig
- ✅ Responsive UI auf allen Bildschirmgrößen
- ✅ Automatische Backups bei Updates

**Nächste Schritte:**
1. Testen Sie alle neuen Features
2. Passen Sie die Einstellungen an Ihre Bedürfnisse an
3. Erstellen Sie Ihr erstes Wissensnetz mit der neuen Workbench

---

**🎉 Viel Erfolg mit Ihrem erweiterten KI-Wissenssystem!** 