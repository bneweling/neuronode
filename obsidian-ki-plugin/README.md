# KI-Wissenssystem Obsidian Plugin

Ein leistungsstarkes Obsidian-Plugin für intelligente Wissensverwaltung mit KI-Unterstützung.

## 🚀 Features

### 💬 **Intelligenter Chat mit Persistenz**
- **Chat-Historie**: Automatische Speicherung aller Gespräche
- **Sitzungsverwaltung**: Organisierte Chat-Sessions mit Titeln und Zeitstempel
- **Suche & Navigation**: Durchsuchen Sie Ihre Chat-Historie
- **Auto-Titel**: Automatische Titel-Generierung aus Nachrichten

### 🔍 **Erweiterte Graph-Suche**
- **4 Suchalgorithmen**:
  - Semantische Suche (KI-basiert)
  - Exakte Textsuche
  - Fuzzy-Suche (tolerant für Tippfehler)
  - Graph-Walk (Verbindungsbasiert)
- **Intelligente Filter**: Nach Knotentyp, Verbindungen, Datum
- **Kategorien**: Automatische Gruppierung mit Statistiken
- **Live-Ergebnisse**: Echtzeit-Suche während der Eingabe

### ⚖️ **Einheitliche Workbench**
- **4 dynamische Layouts**:
  - Balanced: Ausgewogene Ansicht
  - Chat-fokussiert: Großer Chat-Bereich
  - Graph-fokussiert: Erweiterte Graph-Ansicht
  - Search-fokussiert: Maximierte Suchfunktionen
- **Bidirektionale Synchronisation**: Chat und Graph arbeiten zusammen
- **Panel-Management**: Flexible Anordnung der Arbeitsbereiche

### 🕸️ **Interaktive Graph-Visualisierung**
- **3D-Navigation**: Intuitive Erkundung großer Wissensnetze
- **Real-time Updates**: Live-Aktualisierung bei Änderungen
- **Responsive Design**: Optimal für Desktop und Mobile
- **Performance-Optimierung**: Effizient für 1000-10000 Knoten

## 📋 Installation

### Automatische Installation (Empfohlen)

```bash
# Im ki-wissenssystem Verzeichnis:
./install-obsidian-plugin.sh
```

### Manuelle Installation

1. **Plugin bauen**:
```bash
cd obsidian-ki-plugin
npm install
npm run build
```

2. **Plugin kopieren**:
```bash
# Kopieren Sie die Dateien in Ihr Obsidian-Plugin-Verzeichnis
cp main.js manifest.json styles.css ~/.obsidian/plugins/obsidian-ki-plugin/
```

3. **Plugin aktivieren**:
   - Obsidian → Settings → Community Plugins
   - Plugin "KI-Wissenssystem" aktivieren

## 🔄 Update

```bash
# Automatisches Update aller Installationen:
./update-obsidian-plugin.sh
```

## ⚙️ Konfiguration

### Plugin-Einstellungen

1. **API-Einstellungen**:
   - API-URL: `http://localhost:8080`
   - WebSocket-URL: `ws://localhost:8080/ws/chat`
   - API-Key: (Optional für erweiterte Features)

2. **Graph-Einstellungen**:
   - Max. Kontext-Knoten: `10` (für Performance)
   - Graph-Tiefe: `2` (Verbindungsebenen)

3. **Chat-Einstellungen**:
   - Max. Sessions: `50` (automatische Bereinigung)
   - Auto-Save: `Ein` (empfohlen)

### Themes

- **Light/Dark/Auto**: Automatische Anpassung an Obsidian-Theme
- **Responsive UI**: Optimiert für verschiedene Bildschirmgrößen

## 🎯 Verwendung

### Chat-System

1. **Neue Session starten**:
   - Klicken Sie auf das Chat-Icon in der Ribbon
   - Oder verwenden Sie Cmd+P → "Open Knowledge Chat"

2. **Historie verwalten**:
   - 📚 Button für Chat-Historie
   - Suche durch vergangene Gespräche
   - Sessions organisieren und löschen

### Graph-Exploration

1. **Graph öffnen**:
   - Klicken Sie auf das Graph-Icon
   - Oder verwenden Sie Cmd+P → "Open Knowledge Graph"

2. **Erweiterte Suche**:
   - 🔍 Button für Suchpanel
   - Wählen Sie Suchalgorithmus
   - Setzen Sie Filter und Kategorien

### Workbench-Layouts

1. **Layout wechseln**:
   - ⚖️ Layout-Buttons in der Toolbar
   - Oder verwenden Sie Keyboard-Shortcuts

2. **Panels anpassen**:
   - Drag & Drop für Panelgröße
   - Maximieren/Minimieren einzelner Bereiche

## 🔧 Systemanforderungen

- **Obsidian**: Version ≥ 1.0.0
- **Node.js**: Version ≥ 16.0.0
- **npm**: Aktuelle Version
- **KI-Wissenssystem Backend**: Laufend auf localhost:8080

## 🛠️ Entwicklung

### Setup

```bash
npm install
npm run dev  # Development-Modus
npm run build  # Production-Build
```

### Ordnerstruktur

```
src/
├── api/              # API-Clients
├── components/       # UI-Komponenten
│   ├── ChatInterface.ts
│   ├── GraphSearch.ts
│   └── GraphVisualization.ts
├── views/           # Obsidian-Views
└── types.ts         # TypeScript-Definitionen
```

## 📊 Performance

- **Große Graphs**: Optimiert für 1000-10000 Knoten
- **Memory Management**: Intelligente Bereinigung nicht verwendeter Daten
- **Lazy Loading**: Inhalte werden bei Bedarf geladen
- **Caching**: Effiziente Zwischenspeicherung von API-Antworten

## 🐛 Troubleshooting

### Häufige Probleme

1. **Plugin lädt nicht**:
   - Prüfen Sie die Browser-Konsole (Cmd+Option+I)
   - Überprüfen Sie die API-Verbindung

2. **Chat-Historie leer**:
   - Plugin-Daten werden in `.obsidian/plugins/obsidian-ki-plugin/data.json` gespeichert
   - Backup wiederherstellen falls verfügbar

3. **Graph-Performance**:
   - Reduzieren Sie Max. Kontext-Knoten
   - Verwenden Sie Filter für große Graphs

### Debug-Modus

```javascript
// In der Browser-Konsole:
window.kiWissenssystem.debug = true;
```

## 📝 Changelog

### Version 1.0.0
- ✨ Persistente Chat-Historie mit Sitzungsverwaltung
- ✨ Erweiterte Graph-Suche mit 4 Algorithmen
- ✨ Einheitliche Workbench mit flexiblen Layouts
- ✨ Verbesserte Performance für große Graphs
- ✨ Responsive Design für alle Bildschirmgrößen

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Commiten Sie Ihre Änderungen
4. Erstellen Sie einen Pull Request

## 📄 Lizenz

MIT License - siehe LICENSE-Datei für Details.

## 🆘 Support

Bei Problemen oder Fragen:

1. Prüfen Sie die [Troubleshooting](#-troubleshooting)-Sektion
2. Durchsuchen Sie die Issues im Repository
3. Erstellen Sie ein neues Issue mit detaillierter Beschreibung

---

**Made with ❤️ for the Obsidian Community**
