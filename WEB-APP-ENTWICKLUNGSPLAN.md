# 🎨 KI-Wissenssystem Web-App - Entwicklungsplan

## 🎯 Projekt-Ziele

**Funktionsfähiger Prototyp mit:**
- ✅ Material Design 3 (Google's neueste Design-Sprache)
- ✅ Chat-Interface mit WebSocket-Verbindung
- ✅ Interactive Graph-Visualisierung 
- ✅ File-Upload mit Drag & Drop
- ✅ Responsive Design (Desktop + Mobile)
- ✅ Integration mit bestehendem FastAPI Backend

## 🛠️ Tech-Stack

### Frontend-Framework
```json
{
  "name": "ki-wissenssystem-webapp",
  "framework": "Next.js 14 (App Router)",
  "ui_library": "Material Web Components 1.0",
  "styling": "CSS Modules + Material Tokens",
  "typescript": "5.0+",
  "state_management": "Zustand",
  "websockets": "WebSocket API (native)",
  "visualization": "D3.js + Cytoscape.js",
  "build_tool": "Vite (via Next.js)",
  "package_manager": "npm"
}
```

### Material Design 3 Setup
```javascript
// Material Web Components
import '@material/web/all.js';
import { Material3Theme } from '@material/material-color-utilities';

// Theme Configuration
const theme = {
  colorScheme: 'dynamic', // Adaptive Farben
  typography: 'Roboto',   // Material Typography
  elevation: 'Material3', // Neue Schatten-System
  motion: 'Emphasized'    // Material Motion
};
```

## 📁 Projekt-Struktur

```
ki-wissenssystem-webapp/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root Layout mit Material Theme
│   │   ├── page.tsx           # Dashboard (Hauptseite)
│   │   ├── chat/              # Chat-Route
│   │   ├── graph/             # Graph-Route
│   │   └── upload/            # Upload-Route
│   ├── components/            # Wiederverwendbare Komponenten
│   │   ├── ui/               # Material UI Basis-Komponenten
│   │   ├── chat/             # Chat-spezifische Komponenten
│   │   ├── graph/            # Graph-Komponenten
│   │   └── upload/           # Upload-Komponenten
│   ├── lib/                  # Utilities & API
│   │   ├── api.ts            # Backend-Integration
│   │   ├── websocket.ts      # WebSocket-Client
│   │   └── theme.ts          # Material Theme Config
│   ├── styles/               # Globale Styles
│   │   ├── globals.css       # Material Design Tokens
│   │   └── material.css      # Material Web Overrides
│   └── types/                # TypeScript Definitionen
└── public/                   # Statische Assets
```

## 🎨 Material Design 3 Implementierung

### Design-Tokens & Theming
```css
/* Material Design 3 Color System */
:root {
  /* Primary Colors */
  --md-sys-color-primary: #6750A4;
  --md-sys-color-on-primary: #FFFFFF;
  --md-sys-color-primary-container: #EADDFF;
  
  /* Surface Colors */
  --md-sys-color-surface: #FEF7FF;
  --md-sys-color-surface-variant: #E7E0EC;
  
  /* Dynamic Color Support */
  color-scheme: light dark;
}

@media (prefers-color-scheme: dark) {
  :root {
    --md-sys-color-primary: #D0BCFF;
    --md-sys-color-surface: #141218;
  }
}
```

### Component-Hierarchie
```typescript
// Layout-Komponenten
- AppShell (Navigation + Sidebar)
- TopAppBar (Material Top App Bar)
- NavigationDrawer (Material Navigation Drawer)
- BottomSheet (Mobile-optimiert)

// Feature-Komponenten  
- ChatInterface (Material Cards + Lists)
- GraphVisualization (Canvas + Material Controls)
- FileUploadZone (Material File Input + Progress)
- SearchPanel (Material Search + Chips)
```

## 🚀 Entwicklungsphase 1: Basis-Setup (30 min)

### 1.1 Projekt-Initialisierung
```bash
# Next.js App mit TypeScript
npx create-next-app@latest ki-wissenssystem-webapp --typescript --app --src-dir

# Material Design Dependencies
npm install @material/web
npm install @material/material-color-utilities
npm install @material/tokens

# Zusätzliche Dependencies
npm install zustand axios d3 @types/d3
npm install cytoscape cytoscape-d3-force @types/cytoscape
```

### 1.2 Material Theme Setup
```typescript
// src/lib/theme.ts
import { applyTheme } from '@material/web/theming/theme.js';
import { argbFromHex, themeFromSourceColor } from '@material/material-color-utilities';

const setupMaterialTheme = () => {
  const sourceColor = argbFromHex('#6750A4'); // Primary Brand Color
  const theme = themeFromSourceColor(sourceColor);
  applyTheme(document, theme);
};
```

### 1.3 Layout-Grundstruktur
```tsx
// src/app/layout.tsx - Root Layout
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="material-theme">
        <MaterialThemeProvider>
          <AppShell>{children}</AppShell>
        </MaterialThemeProvider>
      </body>
    </html>
  );
}
```

## 🚀 Entwicklungsphase 2: Kern-Komponenten (45 min)

### 2.1 Chat-Interface
```tsx
// src/components/chat/ChatInterface.tsx
- Material Cards für Nachrichten
- Material Text Fields für Input
- Material FAB für Send-Button
- WebSocket-Integration
- Auto-Scroll Behavior
- Typing Indicators
```

### 2.2 Graph-Visualisierung
```tsx
// src/components/graph/GraphVisualization.tsx
- D3.js für Graph-Rendering
- Cytoscape.js für Interaktionen
- Material Controls (Zoom, Filter)
- Material Bottom Sheets für Node-Details
- Responsive Canvas-Sizing
```

### 2.3 File-Upload
```tsx
// src/components/upload/FileUploadZone.tsx
- Material File Input
- Drag & Drop mit Material Design
- Material Progress Indicators
- Material Snackbars für Feedback
- File-Preview Components
```

## 🚀 Entwicklungsphase 3: Backend-Integration (15 min)

### 3.1 API-Client
```typescript
// src/lib/api.ts
class KIWissenssystemAPI {
  constructor(baseURL = 'http://localhost:8080') {
    this.baseURL = baseURL;
  }
  
  // Chat APIs
  async sendMessage(message: string) { ... }
  
  // Graph APIs  
  async getGraphStats() { ... }
  async searchGraph(query: string) { ... }
  
  // Upload APIs
  async uploadDocument(file: File) { ... }
}
```

### 3.2 WebSocket-Client
```typescript
// src/lib/websocket.ts
class WebSocketChat {
  connect() { 
    this.ws = new WebSocket('ws://localhost:8080/ws/chat');
    this.setupEventHandlers();
  }
}
```

## 🎨 Design-Spezifikationen

### Material Design 3 Prinzipien
1. **Dynamic Color**: Adaptive Farbpalette basierend auf Nutzer-Präferenzen
2. **Personal**: Anpassbare UI-Elemente
3. **Accessible**: WCAG 2.1 AA Konformität
4. **Expressive**: Moderne Material You Ästhetik

### Responsive Breakpoints
```css
/* Material Design Breakpoints */
.mobile { max-width: 599px; }      /* Compact */
.tablet { min-width: 600px; }      /* Medium */
.desktop { min-width: 840px; }     /* Expanded */
.wide { min-width: 1200px; }       /* Large */
```

### Component-Spezifikationen

#### Chat-Interface
- **Material Cards** für Nachrichten-Bubbles
- **Dynamic Color** für Benutzer-/Bot-Unterscheidung
- **Material Motion** für Nachrichten-Animationen
- **Bottom Navigation** für Mobile

#### Graph-Visualisierung
- **Material Surface** als Graph-Hintergrund
- **FAB-Collection** für Graph-Controls
- **Material Dialogs** für Node-Details
- **Adaptive Layout** für verschiedene Bildschirmgrößen

#### File-Upload
- **Material File Input** mit Custom Styling
- **Drag & Drop Overlays** mit Material Effects
- **Progress Indicators** nach Material Specs
- **Snackbars** für Upload-Feedback

## ⚡ Performance-Optimierungen

### Code-Splitting
```typescript
// Lazy Loading für große Komponenten
const GraphVisualization = lazy(() => import('./components/graph/GraphVisualization'));
const FileUploadZone = lazy(() => import('./components/upload/FileUploadZone'));
```

### Material Web Bundle-Optimierung
```javascript
// Selektive Material Component Imports
import '@material/web/button/filled-button.js';
import '@material/web/textfield/outlined-text-field.js';
import '@material/web/card/elevated-card.js';
// Nicht alle Komponenten laden
```

## 🔍 Qualitätssicherung

### Testing-Strategie
- **Unit Tests**: Jest + React Testing Library
- **Integration Tests**: Playwright
- **Accessibility Tests**: axe-core
- **Performance Tests**: Lighthouse CI

### Browser-Kompatibilität
- **Chrome/Edge**: 100% (Primär-Ziel)
- **Firefox**: 95% (Secondary)
- **Safari**: 90% (Mobile wichtig)

## 📱 Mobile-First Considerations

### Touch-Optimierung
- **48dp Touch-Targets** (Material Standard)
- **Swipe-Gesten** für Navigation
- **Pull-to-Refresh** für Daten-Updates
- **Viewport-Meta** für korrekte Skalierung

### Progressive Web App (PWA)
```json
// public/manifest.json
{
  "name": "KI-Wissenssystem",
  "short_name": "KI-System",
  "theme_color": "#6750A4",
  "background_color": "#FEF7FF",
  "display": "standalone",
  "start_url": "/",
  "icons": [...]
}
```

## 🚀 Deployment-Vorbereitung

### Build-Optimierung
```javascript
// next.config.js
module.exports = {
  experimental: {
    appDir: true,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  images: {
    domains: ['localhost'],
  },
};
```

### Environment-Konfiguration
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8080/ws/chat
```

## ✅ Fertigstellungs-Checkliste

### Funktionalität
- [ ] Chat sendet/empfängt Nachrichten
- [ ] Graph zeigt Knoten und Verbindungen
- [ ] File-Upload funktioniert mit Backend
- [ ] Responsive Design auf allen Geräten
- [ ] Dark/Light Mode funktioniert

### Material Design 3
- [ ] Alle Komponenten folgen Material-Specs
- [ ] Dynamic Color System implementiert
- [ ] Material Motion korrekt
- [ ] Accessibility-Standards erfüllt

### Performance
- [ ] Initial Load < 3 Sekunden
- [ ] Lighthouse Score > 90
- [ ] Bundle Size < 500KB (gzipped)

**Geschätzte Entwicklungszeit: 1.5-2 Stunden für vollen Prototyp**

**Soll ich mit der Implementierung beginnen?** 🚀 