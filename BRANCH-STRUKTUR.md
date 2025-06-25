# Branch-Struktur des KI-Wissenssystems

## Übersicht

Das KI-Wissenssystem wird in zwei parallelen Versionen entwickelt, um verschiedene Frontend-Interfaces zu unterstützen:

## Branches

### `main` - Obsidian Plugin Version
- **Zweck**: Vollständige Integration mit Obsidian
- **Frontend**: Obsidian Plugin (`obsidian-ki-plugin/`)
- **Zielgruppe**: Nutzer, die bereits Obsidian verwenden
- **Features**:
  - Nahtlose Integration in Obsidian-Workflows
  - Plugin-basierte Benutzeroberfläche
  - Direkte Einbindung in Obsidian Vault

### `webapp-version` - Standalone Web-App Version
- **Zweck**: Eigenständige Web-Anwendung
- **Frontend**: Next.js Web-App (`ki-wissenssystem-webapp/`)
- **Zielgruppe**: Nutzer ohne Obsidian oder für allgemeine Nutzung
- **Features**:
  - Moderne Web-App mit Material Design 3
  - Responsives Design für alle Geräte
  - Eigenständige Benutzeroberfläche

## Gemeinsame Komponenten

Beide Branches teilen sich:
- **Backend-API** (`ki-wissenssystem/src/api/`)
- **Core-Funktionalitäten** (Document Processing, Retrievers, etc.)
- **Konfiguration und Setup-Skripte**

## Entwicklungsstrategie

1. **Feature-Entwicklung**: Neue Backend-Features werden in `main` entwickelt
2. **Branch-Sync**: Regelmäßige Merges von Backend-Änderungen zwischen Branches
3. **Frontend-spezifisch**: UI/UX-Änderungen bleiben Branch-spezifisch

## Deployment

- `main`: Obsidian Plugin + Backend Services
- `webapp-version`: Web-App + Backend Services

## Migration zwischen Branches

```bash
# Zu Obsidian Version wechseln
git checkout main

# Zu Web-App Version wechseln  
git checkout webapp-version

# Backend-Änderungen synchronisieren
git checkout webapp-version
git merge main
``` 