# Frontend Redesign Implementation Plan & Code Review

## 🎯 Projekt-Überblick
Vollständige Umstellung des Neuronode-Frontends auf das professionelle Tabler-Design-System mit detaillierter Code-Review und Implementierungsleitfaden.

## 📋 Aktueller Status-Überblick

### ✅ Bereits implementiert
- **TablerAppLayout**: Professionelle Sidebar-Navigation mit Tabler-Design
- **TablerGraphDashboard**: Vollständig im neuen Design
- **Tabler-Theme**: Konsistentes Design-System definiert
- **Layout-Integration**: Neues Layout bereits in der App integriert

### ❌ Noch zu implementieren
- **HomePage**: Komplett überarbeiten mit Tabler-Widgets
- **ChatPage**: Professional Chat-Interface mit Tabler-Design
- **UploadPage**: Moderne Upload-Zone mit Tabler-Styling
- **StatusPage**: Dashboard-Style Status-Übersicht
- **SettingsPage**: Tabler-Form-Design
- **DebugPage**: Konsistente Debug-Oberfläche

---

## 🔄 PHASE 1: Core Design System Standardisierung

### 1.1 Theme-System Vervollständigung
**Priorität: KRITISCH**

#### 1.1.1 Tabler-Theme erweitern
```typescript
// Erweiterte Komponenten-Definitionen hinzufügen
- MuiDataGrid Styling
- MuiAccordion Tabler-Style
- MuiAlert mit Tabler-Farben
- MuiDialog modernisieren
- MuiTabs Tabler-Style
- MuiStepper Design
```

#### 1.1.2 Utility-Styles erweitern
```typescript
// Zusätzliche Utility-Styles
- Dashboard-Widgets (widgets)
- Metriken-Karten (metrics)
- Status-Indikatoren (status)
- Form-Layouts (forms)
- Datenvisualisierung (charts)
```

### 1.2 React StrictMode Aktivierung
**Priorität: KRITISCH**

#### 1.2.1 StrictMode Implementation
**Problem**: Potenzielle Bugs durch impure Rendering-Funktionen bleiben unentdeckt.

**Lösung**: Sofortige Aktivierung in `app/layout.tsx`
```typescript
// OBLIGATORISCH: StrictMode für gesamte App
import { StrictMode } from 'react'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <StrictMode>
      <html lang="de">
        <head>
          {/* ... existing head content ... */}
        </head>
        <body className={inter.className}>
          {/* ... existing body content ... */}
        </body>
      </html>
    </StrictMode>
  )
}
```

**Validierung**: 
- [ ] Alle Komponenten rendern doppelt ohne Fehler
- [ ] Keine useEffect-Cleanup-Warnings
- [ ] Keine deprecated API-Warnungen

#### 1.2.2 StrictMode Compliance Testing
```typescript
// Test-Kriterien für StrictMode:
1. Komponenten müssen idempotent sein
2. useEffect-Cleanups müssen vollständig implementiert sein
3. Keine direkten DOM-Manipulationen außerhalb von Refs
4. Keine veralteten React-APIs (findDOMNode, etc.)
```

### 1.3 CSS-Architektur Standardisierung
**Priorität: KRITISCH**

#### 1.3.1 globals.css Refactoring
**Problem**: Veraltete CSS-Variablen kollidieren mit Tabler-Theme.

**Obligatorische Änderungen**:
```css
/* ENTFERNEN - Veraltete Variablen */
:root {
  --foreground-rgb: 0, 0, 0; /* ❌ LÖSCHEN */
  --background-start-rgb: 214, 219, 220; /* ❌ LÖSCHEN */
  --background-end-rgb: 255, 255, 255; /* ❌ LÖSCHEN */
}

/* BEHALTEN - Nur globale Utilities */
:root {
  /* Scrollbar-Styling */
  /* Reset-Styles */
  /* Print-Styles */
}
```

**Strikte Regel**: Keine theme-bezogenen Werte in `globals.css` - ausschließlich aus `tabler-theme.ts`

#### 1.3.2 API-Typsicherheit durch Codegen
**Priorität: KRITISCH**

**Problem**: Manuelle Type-Definitionen führen zu Runtime-Fehlern.

**Obligatorische Implementierung**:
```json
// package.json - Neue Scripts
{
  "scripts": {
    "generate:api-types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/api.generated.ts",
    "dev": "npm run generate:api-types && next dev",
    "build": "npm run generate:api-types && next build"
  }
}
```

**Dependencies hinzufügen**:
```bash
npm install -D openapi-typescript
```

**Validierung**:
- [ ] Alle API-Calls verwenden generierte Typen
- [ ] CI/CD Pipeline generiert Types vor Build
- [ ] Keine manuellen API-Type-Definitionen

### 1.4 Farb-Konsistenz etablieren
**Priorität: HOCH**

#### 1.4.1 Primäre Farbpalette
```css
--tabler-primary: #206bc4     /* Hauptfarbe */
--tabler-primary-light: #4dabf7
--tabler-primary-dark: #1862ab
--tabler-success: #2fb344     /* Erfolgsmeldungen */
--tabler-warning: #f59f00     /* Warnungen */
--tabler-error: #d63384      /* Fehler */
--tabler-info: #17a2b8       /* Informationen */
```

#### 1.4.2 Semantische Farben
```css
--tabler-text-primary: #2c3e50
--tabler-text-secondary: #6c757d
--tabler-text-muted: #adb5bd
--tabler-border: #e9ecef
--tabler-background: #f8f9fa
--tabler-surface: #ffffff
--tabler-surface-hover: #f8f9fa
```

---

## 🔄 PHASE 2: Seiten-spezifische Implementierung

### 2.1 State Management Architektur
**Priorität: KRITISCH**

#### 2.1.1 Vereinheitlichte State-Strategie
**Problem**: Inkonsistente Verwendung von Zustand, Context API und lokalem State.

**Obligatorische Hierarchie-Definition**:
```typescript
// 1. GLOBAL STATE (Zustand) - Nur für App-weite, häufig geänderte Daten
interface GlobalStateUsage {
  chatStore: "✅ Korrekt - Chat-Sitzungen werden app-weit geteilt"
  userAuth: "✅ Korrekt - Authentifizierung ist global"
  appConfig: "✅ Korrekt - Demo/Prod-Modus ist global"
}

// 2. CONTEXT API - Für thematische Daten, selten geändert
interface ContextUsage {
  ThemeContext: "✅ Korrekt - Theme ändert sich selten"
  ApiErrorContext: "✅ Korrekt - Error-Handling ist thematisch"
  ApiClientContext: "✅ Neu - Dependency Injection"
}

// 3. LOKALER STATE - Für Komponenten-spezifische UI-Zustände
interface LocalStateUsage {
  formInputs: "✅ Korrekt - Nur für spezifische Formulare"
  modalOpen: "✅ Korrekt - Nur für spezifische Modals"
  loadingStates: "✅ Korrekt - Nur für spezifische API-Calls"
}
```

**Validierung**:
- [ ] Kein globaler State für UI-spezifische Daten
- [ ] Kein lokaler State für App-weite Daten
- [ ] Context nur für Dependency Injection oder selten geänderte Daten

#### 2.1.2 Data-Fetching Modernisierung
**Priorität: KRITISCH**

**Problem**: Custom Hooks ohne Caching, Revalidierung oder dediziertes State-Management.

**Obligatorische TanStack Query Integration**:
```bash
# Dependencies hinzufügen
npm install @tanstack/react-query @tanstack/react-query-devtools
```

```typescript
// Neue Query Client Konfiguration
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 Minuten
      gcTime: 10 * 60 * 1000,   // 10 Minuten (früher cacheTime)
      retry: (failureCount, error) => {
        // Keine Retries bei 4xx Fehlern
        if (error instanceof Error && error.message.includes('4')) return false
        return failureCount < 3
      },
      refetchOnWindowFocus: false, // Verhindert übermäßige Requests
    },
  },
})
```

**Refactoring-Plan für bestehende Hooks**:
```typescript
// VORHER (useChatApi) - ENTFERNEN
const { isLoading, executeWithErrorHandling } = useChatApi()

// NACHHER - TanStack Query
import { useQuery, useMutation } from '@tanstack/react-query'

const { data: chatHistory, isLoading } = useQuery({
  queryKey: ['chat', chatId],
  queryFn: () => apiClient.getChatHistory(chatId)
})

const sendMessageMutation = useMutation({
  mutationFn: apiClient.sendMessage,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['chat'] })
  }
})
```

**Validierung**:
- [ ] Alle API-Calls verwenden TanStack Query
- [ ] Kein manuelles Loading/Error State Management
- [ ] Query Keys sind standardisiert
- [ ] Optimistic Updates implementiert

### 2.2 HomePage Redesign
**Priorität: KRITISCH**

#### 2.2.1 Identifizierte Probleme
```typescript
// Aktuelle Probleme:
- Inkonsistente Card-Designs
- Veraltete Material-UI-Komponenten
- Fehlende Tabler-Widget-Struktur
- Nicht-responsive Layout-Probleme
- Inkonsistente Farbverwendung
```

#### 2.2.2 Neue Komponenten-Struktur
```typescript
// Neue Komponenten benötigt:
- TablerWelcomeHero: Professioneller Hero-Bereich
- TablerFeatureGrid: Moderne Feature-Karten
- TablerMetricsOverview: System-Metriken-Dashboard
- TablerQuickActions: Schnellzugriff-Buttons
- TablerNotifications: Status-Benachrichtigungen
```

#### 2.2.3 Implementierungsschritte
1. **Hero-Section**: Tabler-Dashboard-Style Header
2. **Feature-Grid**: Konsistente Icon-Karten mit Hover-Effekten
3. **Metrics-Cards**: Live-System-Status-Widgets
4. **Quick-Chat**: Integration in Dashboard-Layout
5. **Responsive**: Mobile-First-Ansatz implementieren

### 2.3 ChatPage Redesign
**Priorität: KRITISCH**

#### 2.3.1 Identifizierte Probleme
```typescript
// Aktuelle ChatInterface-Probleme:
- Veraltetes Material-UI-Layout
- Inkonsistente Sidebar-Navigation
- Fehlende Tabler-Button-Styles
- Nicht-optimierte Mobile-Ansicht
- Uneinheitliche Farb-Palette
```

#### 2.3.2 Neue Chat-Komponenten
```typescript
// Neue Komponenten:
- TablerChatInterface: Professionelles Chat-Layout
- TablerChatSidebar: Konsistente Sidebar
- TablerMessageBubble: Moderne Chat-Nachrichten
- TablerChatInput: Professionelle Eingabe-Zone
- TablerChatControls: Einheitliche Steuerelemente
```

#### 2.3.3 Design-Spezifikationen
```css
/* Chat-spezifische Styles */
.tabler-chat-container {
  background: var(--tabler-background);
  border: 1px solid var(--tabler-border);
  border-radius: 8px;
}

.tabler-message-bubble {
  background: var(--tabler-surface);
  border-radius: 12px;
  padding: 12px 16px;
  margin: 8px 0;
}

.tabler-chat-input {
  background: var(--tabler-surface);
  border: 1px solid var(--tabler-border);
  border-radius: 8px;
}
```

### 2.4 UploadPage Redesign
**Priorität: HOCH**

#### 2.4.1 Identifizierte Probleme
```typescript
// FileUploadZone-Probleme:
- Veraltetes Drag-Drop-Design
- Inkonsistente Progress-Indikatoren
- Fehlende Tabler-Styling
- Nicht-responsive Datei-Liste
- Veraltete Icon-Verwendung
```

#### 2.4.2 Neue Upload-Komponenten
```typescript
// Neue Komponenten:
- TablerFileUploadZone: Moderne Drop-Zone
- TablerFileList: Tabler-styled Datei-Liste
- TablerUploadProgress: Konsistente Progress-Bars
- TablerFilePreview: Datei-Vorschau-Karten
- TablerUploadActions: Einheitliche Aktions-Buttons
```

### 2.5 StatusPage Redesign
**Priorität: HOCH**

#### 2.5.1 Identifizierte Probleme
```typescript
// StatusPage-Probleme:
- Uneinheitliche Metric-Cards
- Veraltete Grid-Layouts
- Inkonsistente Status-Indikatoren
- Fehlende Dashboard-Struktur
- Nicht-optimierte Datenvisualisierung
```

#### 2.5.2 Neue Status-Komponenten
```typescript
// Neue Komponenten:
- TablerSystemOverview: Dashboard-Header
- TablerMetricCard: Einheitliche Metriken-Karten
- TablerStatusIndicator: Konsistente Status-Anzeigen
- TablerPerformanceChart: Tabler-styled Charts
- TablerSystemAlerts: Professionelle Warnungen
```

### 2.6 SettingsPage Redesign
**Priorität: MITTEL**

#### 2.6.1 Identifizierte Probleme
```typescript
// SettingsPage-Probleme:
- Inkonsistente Form-Layouts
- Veraltete Switch-Komponenten
- Uneinheitliche Card-Structures
- Fehlende Tabler-Form-Styling
- Nicht-optimierte Gruppierung
```

#### 2.6.2 Neue Settings-Komponenten
```typescript
// Neue Komponenten:
- TablerSettingsLayout: Strukturierte Settings-Seite
- TablerSettingsCard: Einheitliche Einstellungs-Karten
- TablerFormGroup: Konsistente Formular-Gruppen
- TablerToggleSwitch: Tabler-styled Switches
- TablerSettingsActions: Einheitliche Aktions-Bereiche
```

### 2.7 DebugPage Redesign
**Priorität: NIEDRIG**

#### 2.7.1 Identifizierte Probleme
```typescript
// DebugPage-Probleme:
- Nur in Development verfügbar
- Inkonsistente Error-Anzeige
- Fehlende Tabler-Code-Blocks
- Veraltete List-Komponenten
- Keine strukturierte Darstellung
```

---

## 🔄 PHASE 3: Komponenten-Optimierung

### 3.1 Strikte Komponenten-Kapselung
**Priorität: KRITISCH**

#### 3.1.1 Styling-Kapselung Regeln
**Problem**: Styling-Logik "leakt" aus wiederverwendbaren Komponenten.

**Obligatorische Regeln**:
```typescript
// ❌ VERBOTEN - Styling in Seiten-Komponenten
<Button sx={{ backgroundColor: '#206bc4', padding: '8px 16px' }}>
  Save
</Button>

// ✅ ERLAUBT - Nur über Tabler-Komponenten
<TablerButton variant="primary" size="medium">
  Save
</TablerButton>

// ❌ VERBOTEN - Theme-Werte direkt verwenden
const theme = useTheme()
<Card sx={{ backgroundColor: theme.palette.primary.main }} />

// ✅ ERLAUBT - Tabler-Wrapper verwenden
<TablerCard variant="primary" />
```

**Validierung**:
- [ ] Keine `sx`-Props in Seiten-Komponenten für Styling
- [ ] Keine direkten Theme-Zugriffe für Farben/Spacing
- [ ] Alle Styling-Logik in `Tabler*`-Komponenten gekapselt

#### 3.1.2 Komponenten-Interface-Standards
**Obligatorische Prop-Struktur für alle Tabler-Komponenten**:
```typescript
// Standard Tabler-Komponenten Interface
interface TablerComponentProps {
  // Basis-Props (immer verfügbar)
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  
  // Styling-Props (nur wenn semantisch sinnvoll)
  rounded?: boolean
  elevated?: boolean
  
  // Standard React Props
  children?: React.ReactNode
  className?: string
  onClick?: () => void
  
  // Niemals erlaubt in Tabler-Komponenten
  sx?: never  // Verhindert sx-Prop-Weitergabe
  style?: never // Verhindert inline-Styles
}
```

### 3.2 Legacy-Komponenten-Cleanup
**Priorität: KRITISCH**

#### 3.2.1 Zu entfernende Komponenten
```typescript
// Obsolete Komponenten:
- components/layout/AppLayout.tsx (durch TablerAppLayout ersetzt)
- components/graph/GraphVisualization.tsx (durch TablerGraphDashboard ersetzt)
- Veraltete Error-Boundary-Styles
- Alte Material-UI-Card-Wrapper
```

#### 3.2.2 Zu aktualisierende Komponenten
```typescript
// Komponenten-Updates:
- ErrorBoundary: Tabler-Alert-Styling
- InlineErrorDisplay: Konsistente Error-Darstellung
- GlobalErrorToast: Tabler-Notification-System
- ChatErrorBoundary: Einheitliche Chat-Fehler
```

### 3.3 Neue Shared-Komponenten
**Priorität: HOCH**

#### 3.3.1 Basis-Komponenten
```typescript
// Neue Shared-Komponenten:
- TablerCard: Einheitliche Karten-Komponente
- TablerButton: Konsistente Button-Styles
- TablerInput: Einheitliche Eingabefelder
- TablerModal: Professionelle Dialoge
- TablerTooltip: Konsistente Tooltips
- TablerBadge: Einheitliche Badges
- TablerAvatar: Konsistente Avatar-Darstellung
```

#### 3.3.2 Layout-Komponenten
```typescript
// Layout-Komponenten:
- TablerPageHeader: Einheitliche Seiten-Header
- TablerPageContainer: Konsistente Seiten-Container
- TablerSidebar: Flexible Sidebar-Komponente
- TablerToolbar: Einheitliche Toolbars
- TablerFooter: Konsistente Footer
```

### 3.4 Icon-System Standardisierung
**Priorität: MITTEL**

#### 3.4.1 Icon-Konsistenz
```typescript
// Icon-Standardisierung:
- Einheitliche Icon-Größen (16px, 20px, 24px, 32px)
- Konsistente Icon-Farben
- Standardisierte Icon-Mappings
- Responsive Icon-Skalierung
```

---

## 🔄 PHASE 4: Responsive Design & Mobile Optimierung

### 4.1 Breakpoint-Standardisierung
**Priorität: HOCH**

#### 4.1.1 Tabler-Breakpoints
```typescript
// Breakpoint-System:
xs: 0px      // Mobile
sm: 576px    // Small tablets
md: 768px    // Tablets
lg: 992px    // Desktops
xl: 1200px   // Large desktops
xxl: 1400px  // Extra large screens
```

#### 4.1.2 Mobile-First-Ansatz
```typescript
// Mobile-First-Implementierung:
- Sidebar-Kollaps bei < md
- Touch-optimierte Buttons
- Responsive Grid-Layouts
- Mobile-optimierte Navigation
- Touch-freundliche Formulare
```

### 4.2 Performance-Analyse & Bundle-Optimierung
**Priorität: HOCH**

#### 4.2.1 Next.js Bundle Analyzer Setup
**Problem**: Keine Sichtbarkeit über Bundle-Zusammensetzung und Größe.

**Obligatorische Konfiguration**:
```bash
# Dependencies hinzufügen
npm install -D @next/bundle-analyzer
```

```typescript
// next.config.ts erweitern
import bundleAnalyzer from '@next/bundle-analyzer'

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})

const nextConfig = {
  // ... existing config
}

export default withBundleAnalyzer(nextConfig)
```

```json
// package.json Scripts erweitern
{
  "scripts": {
    "analyze": "ANALYZE=true npm run build",
    "dev:analyze": "ANALYZE=true npm run dev"
  }
}
```

**Validierung**:
- [ ] Bundle-Größe < 5MB total
- [ ] Keine doppelten Dependencies
- [ ] Icon-Imports sind optimiert
- [ ] MUI Tree-Shaking funktioniert

#### 4.2.2 Performance-Metriken Tracking
**Obligatorische Implementierung**:
```typescript
// src/lib/performance.ts
export class PerformanceMonitor {
  static trackPageLoad(pageName: string) {
    if (typeof window !== 'undefined') {
      // Core Web Vitals Tracking
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const metrics = {
        page: pageName,
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
        largestContentfulPaint: performance.getEntriesByName('largest-contentful-paint')[0]?.startTime,
      }
      
      console.log('Performance Metrics:', metrics)
      // In Production: Send to analytics
    }
  }
  
  static trackComponentRender(componentName: string, renderTime: number) {
    if (process.env.NODE_ENV === 'development') {
      console.log(`${componentName} rendered in ${renderTime}ms`)
    }
  }
}
```

#### 4.2.3 Gezielte Bundle-Optimierungen
```typescript
// Performance-Verbesserungen:
- Tree-shaking für MUI-Komponenten
- Lazy-Loading für große Komponenten
- Code-Splitting für Seiten
- Optimierte Icon-Imports
- Minimierte CSS-Bundles

// Spezifische Optimierungen basierend auf Bundle-Analyse:
1. Material-UI Icons: Import nur verwendete Icons
2. Cytoscape: Lazy-Loading für Graph-Komponenten
3. Date-Libraries: Verwende date-fns statt moment.js
4. Lodash: Import nur verwendete Funktionen
```

**Performance-Ziele**:
- [ ] Initial Bundle < 1MB
- [ ] Page Load Time < 3s
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s

---

## 🔄 PHASE 5: Testing & Quality Assurance

### 5.1 Component-Testing
**Priorität: KRITISCH**

#### 5.1.1 Unit-Tests
```typescript
// Test-Bereiche:
- Komponenten-Rendering
- Props-Validierung
- User-Interaktionen
- Responsive-Verhalten
- Accessibility-Compliance
```

#### 5.1.2 Integration-Tests
```typescript
// Integration-Tests:
- Seiten-Navigation
- Theme-Switching
- API-Integration
- Error-Handling
- Mobile-Responsive
```

### 5.2 Accessibility (a11y) Compliance
**Priorität: KRITISCH**

#### 5.2.1 Semantisches HTML Framework
**Problem**: Unstrukturierte HTML-Semantik verhindert Screen-Reader-Navigation.

**Obligatorische HTML-Struktur**:
```typescript
// app/layout.tsx - Semantische Grundstruktur
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <StrictMode>
      <html lang="de">
        <body>
          <header role="banner">
            {/* App-Header */}
          </header>
          <div className="app-container">
            <nav role="navigation" aria-label="Hauptnavigation">
              {/* TablerAppLayout Sidebar */}
            </nav>
            <main role="main" id="main-content">
              {children}
            </main>
          </div>
        </body>
      </html>
    </StrictMode>
  )
}
```

**Seiten-spezifische Semantik**:
```typescript
// Jede Seite muss folgende Struktur haben:
<main>
  <header>
    <h1>Seitentitel</h1>
    <nav aria-label="Breadcrumb">{/* Breadcrumbs */}</nav>
  </header>
  <section aria-label="Hauptinhalt">
    {/* Seiteninhalt */}
  </section>
  <aside aria-label="Zusätzliche Informationen">
    {/* Sidebar-Content wenn vorhanden */}
  </aside>
</main>
```

#### 5.2.2 Fokus-Management System
**Obligatorische Implementierung**:
```typescript
// src/lib/focusManagement.ts
export class FocusManager {
  static skipToContent() {
    const mainContent = document.getElementById('main-content')
    if (mainContent) {
      mainContent.focus()
      mainContent.scrollIntoView()
    }
  }
  
  static trapFocus(containerElement: HTMLElement) {
    const focusableElements = containerElement.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement
    
    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          lastElement.focus()
          e.preventDefault()
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          firstElement.focus()
          e.preventDefault()
        }
      } else if (e.key === 'Escape') {
        // Close modal/dialog
        containerElement.dispatchEvent(new CustomEvent('close'))
      }
    }
    
    containerElement.addEventListener('keydown', handleTabKey)
    firstElement.focus()
    
    return () => containerElement.removeEventListener('keydown', handleTabKey)
  }
}
```

**Skip-Link Implementation**:
```css
/* globals.css - Skip Link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--tabler-primary);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: 4px;
  z-index: 1000;
}

.skip-link:focus {
  top: 6px;
}
```

#### 5.2.3 ARIA-Attribute Standards
**Obligatorische ARIA-Implementierung**:
```typescript
// Dynamische Komponenten MÜSSEN ARIA-Attribute haben:

// Loading States
<div aria-busy="true" aria-live="polite">
  Daten werden geladen...
</div>

// Status Updates
<div aria-live="assertive" role="status">
  Nachricht gesendet
</div>

// Interactive Elements
<button 
  aria-expanded={isOpen}
  aria-controls="menu-items"
  aria-label="Hauptmenü öffnen"
>
  Menü
</button>

// Form Validation
<input 
  aria-invalid={hasError}
  aria-describedby={hasError ? "error-message" : undefined}
/>
{hasError && (
  <div id="error-message" role="alert">
    Pflichtfeld ausfüllen
  </div>
)}
```

#### 5.2.4 Automated Accessibility Testing
**Obligatorische axe-core Integration**:
```bash
npm install -D @axe-core/playwright @axe-core/react
```

```typescript
// tests/a11y/accessibility.test.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility Tests', () => {
  test('Homepage should be accessible', async ({ page }) => {
    await page.goto('/')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })
  
  test('Chat page should be accessible', async ({ page }) => {
    await page.goto('/chat')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })
  
  test('Keyboard navigation should work', async ({ page }) => {
    await page.goto('/')
    
    // Test Tab navigation
    await page.keyboard.press('Tab')
    let focusedElement = await page.locator(':focus')
    await expect(focusedElement).toBeVisible()
    
    // Test Skip Link
    await page.keyboard.press('Tab')
    await page.keyboard.press('Enter')
    const mainContent = page.locator('#main-content')
    await expect(mainContent).toBeFocused()
  })
})
```

**Validierung**:
- [ ] Alle Seiten bestehen axe-core Tests
- [ ] Vollständige Keyboard-Navigation möglich
- [ ] Screen-Reader-Tests bestanden
- [ ] Farbkontrast-Ratio ≥ 4.5:1

### 5.3 Visual-Testing
**Priorität: HOCH**

#### 5.3.1 Screenshot-Tests
```typescript
// Visual-Regression-Tests:
- Alle Seiten in verschiedenen Auflösungen
- Theme-Variationen
- Interaktions-States
- Error-States
- Loading-States
```

---

## 🔄 PHASE 6: Erweiterte Architektur-Implementierung

### 6.1 QueryClient & Provider Setup
**Priorität: KRITISCH**

#### 6.1.1 Root Layout QueryClient Integration
**Obligatorische Implementierung**:
```typescript
// app/layout.tsx - QueryClient Provider hinzufügen
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/queryClient'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <StrictMode>
      <html lang="de">
        <body>
          <QueryClientProvider client={queryClient}>
            <ThemeProvider theme={tablerTheme}>
              <ApiErrorProvider>
                <TablerAppLayout>
                  {children}
                </TablerAppLayout>
              </ApiErrorProvider>
            </ThemeProvider>
            <ReactQueryDevtools initialIsOpen={false} />
          </QueryClientProvider>
        </body>
      </html>
    </StrictMode>
  )
}
```

#### 6.1.2 API Client Context
**Obligatorische Dependency Injection**:
```typescript
// src/contexts/ApiClientContext.tsx
import { createContext, useContext } from 'react'
import { ApiClient } from '@/lib/apiClient'

const ApiClientContext = createContext<ApiClient | null>(null)

export function ApiClientProvider({ children }: { children: React.ReactNode }) {
  const apiClient = new ApiClient({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 10000,
  })

  return (
    <ApiClientContext.Provider value={apiClient}>
      {children}
    </ApiClientContext.Provider>
  )
}

export function useApiClient() {
  const client = useContext(ApiClientContext)
  if (!client) {
    throw new Error('useApiClient must be used within ApiClientProvider')
  }
  return client
}
```

### 6.2 Hooks Migration zu TanStack Query
**Priorität: KRITISCH**

#### 6.2.1 useChatApi Refactoring
**Vor (zu entfernen)**:
```typescript
// hooks/useChatApi.ts - LÖSCHEN
export function useChatApi() {
  const [isLoading, setIsLoading] = useState(false)
  // ... manual loading/error handling
}
```

**Nach (neu implementieren)**:
```typescript
// hooks/useChatQueries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useApiClient } from '@/contexts/ApiClientContext'

export function useChatHistory(chatId?: string) {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['chat', 'history', chatId],
    queryFn: () => apiClient.getChatHistory(chatId!),
    enabled: !!chatId,
    staleTime: 5 * 60 * 1000, // 5 Minuten
  })
}

export function useSendMessage() {
  const apiClient = useApiClient()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: apiClient.sendMessage,
    onSuccess: (data, variables) => {
      // Optimistic Update - Verwendet generierte API-Typen
      queryClient.setQueryData(
        ['chat', 'history', variables.chatId],
        (oldData: ChatMessage[]) => [...(oldData || []), data]
      )
    },
    onError: (error, variables) => {
      // Rollback auf Fehler
      queryClient.invalidateQueries({ queryKey: ['chat', 'history', variables.chatId] })
    }
  })
}
```

#### 6.2.2 Status Page Polling Refactoring
**Vor (zu entfernen)**:
```typescript
// Manuelles Polling - LÖSCHEN
useEffect(() => {
  const interval = setInterval(() => {
    fetchSystemStatus()
  }, 5000)
  return () => clearInterval(interval)
}, [])
```

**Nach (neu implementieren)**:
```typescript
// hooks/useSystemStatus.ts
export function useSystemStatus() {
  const apiClient = useApiClient()
  
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: apiClient.getSystemStatus,
    refetchInterval: 5000, // Automatisches Polling
    refetchIntervalInBackground: true,
    staleTime: 0, // Immer als "stale" behandeln für Live-Updates
  })
}
```

### 6.3 Performance Monitoring Implementation
**Priorität: HOCH**

#### 6.3.1 Page-Level Performance Tracking
**Obligatorische Implementierung in jeder Seite**:
```typescript
// app/page.tsx (HomePage)
'use client'
import { useEffect } from 'react'
import { PerformanceMonitor } from '@/lib/performance'

export default function HomePage() {
  useEffect(() => {
    PerformanceMonitor.trackPageLoad('HomePage')
  }, [])
  
  // ... rest of component
}
```

#### 6.3.2 Component-Level Performance Tracking
**Für kritische Komponenten**:
```typescript
// components/graph/TablerGraphDashboard.tsx
export function TablerGraphDashboard() {
  const renderStart = performance.now()
  
  useEffect(() => {
    const renderTime = performance.now() - renderStart
    PerformanceMonitor.trackComponentRender('TablerGraphDashboard', renderTime)
  }, [])
  
  // ... rest of component
}
```

### 6.4 Strikte TypeScript Konfiguration
**Priorität: KRITISCH**

#### 6.4.1 tsconfig.json Verschärfung
**Obligatorische Konfiguration**:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": false
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": [
    "node_modules",
    ".next",
    "out"
  ]
}
```

**Validierung**:
- [ ] Keine TypeScript-Fehler
- [ ] Keine `any`-Types außer bei Third-Party-Libraries
- [ ] Alle Props sind typisiert
- [ ] API-Responses verwenden generierte Typen

---

## 🔬 ZUSÄTZLICHE ANALYSE & ERWEITERTE EMPFEHLUNGEN

Dieser Abschnitt ergänzt den oben stehenden Plan um strategische und technische Empfehlungen, die auf einer Tiefenanalyse des Codes und moderner Frontend-Best-Practices basieren.

### A. Strategische Architekturentscheidungen

#### A.1 Vereinheitlichte State-Management-Strategie
**Problem**: Die App nutzt derzeit eine Mischung aus Zustand, Context API und lokalem State ohne klare Abgrenzung. Dies kann zu inkonsistentem State-Handling und schwierigem Debugging führen.

**Empfehlung**: Definition einer klaren Hierarchie für das State Management:
-   **Zustand (Global State)**: Ausschließlich für globalen, App-weiten State, der häufig von nicht direkt verwandten Komponenten modifiziert und abonniert wird.
    -   **Beispiele**: Benutzerauthentifizierung, Chat-Sitzungen (`chatStore`), App-weite Konfigurationen (`useAppConfig`).
-   **React Context API (Thematischer State)**: Für thematisch zusammengehörende Daten, die an einen Sub-Tree von Komponenten weitergegeben werden, sich aber nicht häufig ändern. Ideal für Dependency Injection.
    -   **Beispiele**: `ThemeContext`, `ApiErrorContext`, Bereitstellung eines API-Client-Objekts.
-   **Lokaler State (`useState`, `useReducer`)**: Für jeglichen State, der auf eine einzelne Komponente oder eine kleine Gruppe von direkt verwandten Komponenten beschränkt ist.
    -   **Beispiele**: Zustand von Formular-Inputs, Öffnen/Schließen eines Modals, UI-State einer einzelnen Karte.

#### A.2 Etablierung einer robusten Data-Fetching-Schicht
**Problem**: Das Daten-Fetching ist derzeit in Custom Hooks (`useChatApi`) implementiert, die kein Caching, keine automatische Revalidierung oder dediziertes Loading-/Error-State-Management bieten. Dies führt zu Boilerplate-Code und suboptimaler Performance (z.B. "Hardcoded-Polling-Intervalle" in der `StatusPage`).

**Empfehlung**: Einführung einer dedizierten Data-Fetching-Bibliothek wie **TanStack Query (React Query)** oder **SWR**.
-   **Vorteile**:
    -   **Caching & Revalidierung**: Reduziert die Anzahl der API-Anfragen drastisch.
    -   **Automatisches State-Management**: Vereinfacht die Handhabung von `isLoading`, `isError`, `data`.
    -   **Hintergrund-Synchronisation**: Hält die Daten auf dem neuesten Stand, ohne die UI zu blockieren.
    -   **Performance**: Bietet Features wie `stale-while-revalidate` und Abfrage-Deduplizierung.
-   **Aktion**: Refactoring der bestehenden API-Hooks, um TanStack Query zu nutzen. Dies würde die Komplexität auf den Seiten (z.B. `StatusPage`, `GraphPage`) erheblich reduzieren.

### B. Code-Qualität und Developer Experience

#### B.1 Aktivierung von React StrictMode
**Problem**: Die Anwendung nutzt derzeit nicht den `<StrictMode>` von React. Dadurch werden potenzielle Fehler, die durch impure Rendering-Funktionen oder fehlende Effekt-Cleanups entstehen, nicht während der Entwicklung aufgedeckt.

**Empfehlung**: Umgehende Aktivierung von `<StrictMode>` im `app/layout.tsx`, um das gesamte Projekt abzudecken.
```typescript
// in app/layout.tsx
// ...
import { StrictMode } from 'react';

export default function RootLayout({ children }) {
  return (
    <StrictMode>
      <html lang="de">
        {/* ... restlicher Code ... */}
      </html>
    </StrictMode>
  );
}
```
**Vorteil**: Hilft, schwer zu reproduzierende Bugs proaktiv während der Entwicklung zu finden und zu beheben, was die Stabilität der Anwendung erhöht.

#### B.2 API-Typsicherheit durch Codegen
**Problem**: Die Typen für API-Antworten werden manuell in TypeScript definiert. Dies ist fehleranfällig und führt zu Inkonsistenzen, wenn sich das Backend ändert.

**Empfehlung**: Einrichtung eines Codegen-Prozesses, der TypeScript-Typen automatisch aus der OpenAPI/Swagger-Spezifikation des Backends generiert.
-   **Tools**: `openapi-typescript` oder `openapi-generator`.
-   **Workflow**: Ein Skript im `package.json` (`npm run generate:api-types`) wird ausgeführt, das die aktuelle API-Spezifikation vom Backend abruft und die Typdefinitionen im Frontend aktualisiert.
-   **Vorteil**: 100%ige Typsicherheit zwischen Frontend und Backend, Reduzierung manueller Arbeit und Vermeidung von Laufzeitfehlern.

#### B.3 Gezielte Performance-Analyse
**Problem**: Der Plan erwähnt Performance-Optimierung, aber es fehlt eine konkrete Strategie zur Identifizierung von Engpässen.

**Empfehlung**: Einsatz von `@next/bundle-analyzer` zur Visualisierung der Bundle-Zusammensetzung.
-   **Aktion**: Konfiguration des `next.config.ts`, um den Bundle Analyzer zu aktivieren.
-   **Ziel**: Identifizierung großer Abhängigkeiten (z.B. vollständige Importe von Icon-Bibliotheken statt Tree-Shaking) und gezielte Optimierung.

### C. Komponenten-Architektur und Styling

#### C.1 Strikte Komponenten-Kapselung
**Problem**: Es besteht die Gefahr, dass Styling-Logik (`sx`-Prop) aus den wiederverwendbaren Komponenten in die Seiten-Komponenten "leakt".

**Empfehlung**: Etablierung einer strikten Regel: Die neuen `Tabler*`-Komponenten (z.B. `TablerCard`, `TablerButton`) sind die **einzige Quelle für das Tabler-Styling**.
-   **Regel**: Seiten-Komponenten sollten **keine `sx`-Props** zur Definition von Farben, Abständen oder Schriften verwenden. Sie orchestrieren die `Tabler*`-Komponenten und übergeben nur Daten und Logik-Props.
-   **Beispiel**: Ein Button auf einer Seite wird immer `<TablerButton variant="primary">...</TablerButton>` sein, niemals `<Button sx={{ backgroundColor: 'blue', ... }}>...`.

#### C.2 Aufräumen von `globals.css`
**Problem**: Die Datei `globals.css` enthält veraltete CSS-Variablen (`--foreground-rgb`) und generische Utility-Klassen, die mit dem neuen Theme-System kollidieren könnten.

**Empfehlung**: Refactoring der `globals.css` im Rahmen der Umstellung.
-   **Aktion**: Alle themenbezogenen Werte (Farben, Schriftarten) entfernen und ausschließlich aus dem `tabler-theme.ts` beziehen.
-   **Ziel**: `globals.css` sollte nur noch minimale Basis-Resets und wirklich globale Stile (z.B. Scrollbar-Styling) enthalten.

### D. Konkreter Plan für Barrierefreiheit (Accessibility, a11y)

**Problem**: Das Ziel "WCAG 2.1 AA-Compliance" ist gut, aber es fehlen konkrete, umsetzbare Schritte.

**Empfehlung**: Integration der folgenden konkreten a11y-Praktiken:
1.  **Semantisches HTML**: Verwendung von `<nav>`, `<main>`, `<header>`, `<aside>` im `TablerAppLayout` und auf den Seiten.
2.  **Fokus-Management**: Sicherstellen, dass alle interaktiven Elemente (Buttons, Links, Inputs) klare und konsistente `:focus`- und `:focus-visible`-Stile aus dem Tabler-Theme erhalten.
3.  **Tastatur-Navigation**: Alle Funktionen müssen ausschließlich per Tastatur bedienbar sein.
4.  **ARIA-Attribute**: Korrekte Verwendung von `aria-*`-Attributen für dynamische Komponenten (z.B. `aria-busy` für ladende Bereiche, `aria-live` für Benachrichtigungen).
5.  **Automatisierte Tests**: Integration von `axe-core` in die Entwicklungs- und Test-Pipeline, um Barrierefreiheitsprobleme frühzeitig zu erkennen.

---

## 📊 IMPLEMENTIERUNGS-TIMELINE

### Woche 1-2: Foundation
- [ ] Theme-System vervollständigen
- [ ] Basis-Komponenten erstellen
- [ ] Legacy-Cleanup starten

### Woche 3-4: Critical Pages
- [ ] HomePage komplett redesignen
- [ ] ChatPage Tabler-Migration
- [ ] StatusPage Dashboard-Style

### Woche 5-6: Remaining Pages
- [ ] UploadPage modernisieren
- [ ] SettingsPage Tabler-Forms
- [ ] DebugPage konsistent stylen

### Woche 7-8: Polish & Testing
- [ ] Mobile-Optimierung
- [ ] Performance-Optimierung
- [ ] Extensive Testing
- [ ] Dokumentation

---

## 🎯 ERFOLGS-METRIKEN

### Design-Konsistenz
- [ ] 100% Tabler-Theme-Compliance
- [ ] Einheitliche Komponenten-Bibliothek
- [ ] Konsistente Farb-Palette
- [ ] Standardisierte Spacing-System

### Performance
- [ ] <3s Initial-Load-Time
- [ ] <1s Page-Transition-Time
- [ ] <50ms Interaction-Response-Time
- [ ] <5MB Bundle-Size

### User Experience
- [ ] 100% Mobile-Responsive
- [ ] WCAG 2.1 AA-Compliance
- [ ] Intuitive Navigation
- [ ] Konsistente Interactions

### Code Quality
- [ ] 100% TypeScript-Coverage
- [ ] 0 ESLint-Errors
- [ ] 100% Test-Coverage
- [ ] Moderne React-Patterns

---

## 🔧 TOOLS & TECHNOLOGIEN

### Development
- React 18+ (bereits vorhanden)
- TypeScript (bereits vorhanden)
- Next.js 14+ (bereits vorhanden)
- Material-UI 5+ (bereits vorhanden)

### Design System
- Tabler-Theme (bereits implementiert)
- Inter-Font (bereits integriert)
- Professionelle Icon-Bibliothek
- Konsistente Spacing-System

### Testing
- Jest + React Testing Library
- Playwright für E2E-Tests
- Storybook für Komponenten
- Visual-Regression-Tests

### Build & Deploy
- Webpack-Optimierungen
- Code-Splitting
- Tree-Shaking
- Performance-Monitoring

---

## 📝 NÄCHSTE SCHRITTE

1. **Freigabe abwarten**: Warten auf Bestätigung zur Implementierung
2. **Priorisierung**: Kritische Probleme zuerst angehen
3. **Schrittweise Migration**: Seite für Seite migrieren
4. **Kontinuierliche Tests**: Parallele Qualitätssicherung
5. **Dokumentation**: Laufende Dokumentation der Änderungen

---

**📌 WICHTIGER HINWEIS**: Dieses Dokument dient als Masterplan für die Frontend-Modernisierung. Alle Änderungen sollten schrittweise implementiert werden, um die Stabilität der Anwendung zu gewährleisten.

**🚀 BEREIT FÜR IMPLEMENTIERUNG**: Sobald die Freigabe erteilt wird, kann die Umsetzung gemäß diesem Plan beginnen. 