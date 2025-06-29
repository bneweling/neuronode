# Branch-Struktur des KI-Wissenssystems

## Übersicht

Das KI-Wissenssystem wird in zwei parallelen Versionen entwickelt, um verschiedene Frontend-Interfaces zu unterstützen:

## Aktuelle Branches

### `webapp-version` - Standalone Web-App Version ⭐ **AKTUELL**
- **Zweck**: Eigenständige Web-Anwendung (Hauptfokus)
- **Frontend**: Next.js Web-App (`ki-wissenssystem-webapp/`)
- **Status**: ✅ **Produktionsbereit** - Vollständig entwickelt und getestet
- **Zielgruppe**: Alle Nutzer - eigenständige, professionelle Lösung
- **Features**:
  - Moderne Web-App mit Material Design 3
  - Responsives Design für alle Geräte
  - Multi-Chat System mit Verlauf
  - Interaktive Graph-Visualisierung
  - Drag & Drop File Upload
  - Dark/Light Mode Support
  - Production-ready Deployment

### `main` - Obsidian Plugin Version
- **Zweck**: Vollständige Integration mit Obsidian (Legacy)
- **Frontend**: Obsidian Plugin (`obsidian-ki-plugin/`)
- **Status**: ⚠️ **Wartungsmodus** - Basisfunktionen verfügbar
- **Zielgruppe**: Existing Obsidian power users
- **Features**:
  - Nahtlose Integration in Obsidian-Workflows
  - Plugin-basierte Benutzeroberfläche
  - Direkte Einbindung in Obsidian Vault

## Gemeinsame Komponenten

Beide Branches teilen sich:
- **Backend-API** (`ki-wissenssystem/src/api/`) - ✅ Identisch
- **Core-Funktionalitäten** (Document Processing, Retrievers, etc.) - ✅ Identisch
- **Konfiguration und Setup-Skripte** - ✅ Cross-kompatibel
- **Docker Services** (Neo4j, ChromaDB, Redis) - ✅ Identisch

## Entwicklungsstrategie (Stand: 2025)

1. **Primäre Entwicklung**: Fokus auf `webapp-version` (aktuelle Branch)
2. **Backend-Features**: Alle neuen Features werden hier entwickelt
3. **Plugin-Maintenance**: `main` Branch wird nur für kritische Fixes aktualisiert
4. **Production Focus**: Alle Production-Features für Web-App

## Deployment-Status

- **`webapp-version`**: ✅ **Production-ready** mit vollständigem Monitoring
- **`main`**: ⚠️ Development/Personal use

## Migration zwischen Branches

```bash
# Aktuelle Web-App Version (empfohlen)
git checkout webapp-version

# Legacy Obsidian Version  
git checkout main

# Backend-Änderungen synchronisieren (bei Bedarf)
git checkout main
git merge webapp-version --strategy-option theirs
```

## Empfohlene Nutzung

**Für neue Projekte**: 🚀 `webapp-version` verwenden
**Für bestehende Obsidian-Nutzer**: `main` bis Migration abgeschlossen 