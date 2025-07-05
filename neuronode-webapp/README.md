# Neuronode Frontend

Eine moderne React-basierte Benutzeroberfläche für das Neuronode-System mit KI-Chat, Wissensgraph-Visualisierung und Dokumenten-Upload.

## 🚀 Schnellstart

```bash
# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Build für Produktion
npm run build
```

## 🔧 API-Typen-Generierung

Um die TypeScript-Typen für die Backend-API zu generieren, muss das Backend gestartet werden:

### Schritt 1: Backend starten
```bash
# Ins Backend-Verzeichnis wechseln
cd ../neuronode-backend

# Backend-API starten
./scripts/api/start-api.sh
```

### Schritt 2: API-Typen generieren
```bash
# Zurück ins Frontend-Verzeichnis
cd ../neuronode-webapp

# API-Typen generieren (Backend muss laufen)
npm run generate:api-types
```

Die generierten Typen werden in `src/types/api.generated.ts` gespeichert und automatisch beim Build-Prozess aktualisiert.

## 📁 Projektstruktur

```
src/
├── app/                    # Next.js App Router Seiten
│   ├── chat/              # KI-Chat Interface
│   ├── graph/             # Wissensgraph-Visualisierung
│   ├── upload/            # Dokumenten-Upload
│   ├── status/            # System-Status Dashboard
│   └── settings/          # Anwendungseinstellungen
├── components/            # Wiederverwendbare Komponenten
│   ├── chat/             # Chat-spezifische Komponenten
│   ├── graph/            # Graph-Visualisierung
│   ├── upload/           # File-Upload Komponenten
│   ├── layout/           # Layout-Komponenten
│   └── error/            # Fehlerbehandlung
├── hooks/                # Custom React Hooks
├── contexts/             # React Context Provider
├── services/             # API-Services
├── types/                # TypeScript Typen
├── theme/                # MUI Theme Konfiguration
└── lib/                  # Utility-Funktionen
```

## 🎨 Design System

Das Frontend nutzt Material-UI (MUI) mit einem angepassten Tabler-Theme für eine moderne und konsistente Benutzeroberfläche.

## 🧪 Testing

```bash
# Unit Tests
npm run test

# E2E Tests
npm run test:e2e

# Accessibility Tests
npm run test:accessibility

# Performance Tests
npm run test:performance
```

## 📊 Performance Monitoring

Das System enthält integriertes Performance-Monitoring mit:
- Page Load Tracking
- Component Render Tracking
- API Call Performance
- Core Web Vitals

## 🔍 Bundle-Analyse

```bash
# Bundle-Analyse ausführen
npm run analyze

# Entwicklungsmodus mit Analyse
npm run dev:analyze
```

## 🌐 Modi

### Demo-Modus
- Nutzt synthetische Daten
- Keine Backend-Verbindung erforderlich
- Ideal für Entwicklung und Präsentationen

### Produktions-Modus
- Verbindung zum echten Backend
- Authentifizierung erforderlich
- Vollständige Funktionalität

## 📝 Verfügbare Scripts

| Script | Beschreibung |
|--------|--------------|
| `dev` | Entwicklungsserver starten |
| `build` | Produktions-Build erstellen |
| `start` | Produktions-Server starten |
| `lint` | Code-Linting ausführen |
| `test` | Unit Tests ausführen |
| `test:e2e` | End-to-End Tests |
| `test:accessibility` | Accessibility Tests |
| `generate:api-types` | API-Typen generieren |
| `analyze` | Bundle-Analyse |

## 🛠️ Entwicklung

### Voraussetzungen
- Node.js 18+
- npm oder yarn
- Laufendes Neuronode-Backend (für API-Typen)

### Umgebungsvariablen
```env
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_DEMO_MODE=false
```

### Code-Qualität
- ESLint für Code-Linting
- TypeScript für Typsicherheit
- Prettier für Code-Formatierung
- Husky für Git-Hooks

## 🔒 Sicherheit

- CSP (Content Security Policy)
- CORS-Konfiguration
- Input-Validierung
- XSS-Schutz

## 📱 Responsive Design

Das Frontend ist vollständig responsive und optimiert für:
- Desktop (1920px+)
- Tablet (768px - 1919px)
- Mobile (320px - 767px)

## 🌍 Internationalisierung

Derzeit unterstützt das System Deutsch als Hauptsprache. Internationalisierung ist für zukünftige Versionen geplant.

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.
