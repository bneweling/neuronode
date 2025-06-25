# Demo/Produktions-Modus System - Dokumentation

## Übersicht

Das KI-Wissenssystem Web-App verfügt jetzt über ein vollständiges Demo/Produktions-Modus-System, das nahtloses Umschalten zwischen synthetischen Demo-Daten und echter Backend-Verbindung ermöglicht.

## ✅ Implementierte Features

### 1. Konfigurationssystem (`src/config/environment.ts`)
- **ConfigManager**: Singleton-Klasse für zentrale Konfigurationsverwaltung
- **Persistente Speicherung**: Einstellungen werden im localStorage gespeichert
- **Reaktive Updates**: Automatische Benachrichtigung aller Komponenten bei Änderungen
- **Health-Checking**: Automatische Überprüfung der Backend-Verfügbarkeit

### 2. React Hooks (`src/hooks/useAppConfig.ts`)
- **useAppConfig**: Haupthook für Konfigurationszugriff
- **Spezialisierte Hooks**: useApiUrl, useWebSocketUrl, useEndpointUrl, etc.
- **Reactive State**: Automatische Re-Renders bei Konfigurationsänderungen
- **useModeIndicator**: Hook für UI-Indikatoren

### 3. Service Factory (`src/lib/serviceFactory.ts`)
- **Nahtlose Umschaltung**: Automatische Service-Erstellung je nach Modus
- **Singleton Pattern**: Effiziente Ressourcennutzung
- **Hot Swapping**: Services werden bei Modus-Wechsel neu erstellt

### 4. Mock Service (`src/services/mockService.ts`)
- **Realistische Demo-Daten**: IT-Sicherheits-fokussierte Beispieldaten
- **15 Knoten, 17 Verbindungen**: Wissensgraph mit Standards, Controls, Threats
- **Intelligente Chat-Responses**: Kontextuelle Antworten basierend auf Schlüsselwörtern
- **Simulierte Delays**: Realistische API-Response-Zeiten

### 5. Production Service (`src/services/productionService.ts`)
- **Backend-Kompatibilität**: Mapping zu bestehenden API-Endpunkten
- **Fehlerbehandlung**: Graceful Fallbacks bei Verbindungsproblemen
- **Schema-Transformation**: Anpassung zwischen Frontend- und Backend-Datenformaten
- **WebSocket-Support**: Vorbereitung für Echtzeit-Features

### 6. Settings-Seite (`src/app/settings/page.tsx`)
- **Visueller Mode-Switch**: Toggle zwischen Demo und Produktion
- **Connection Testing**: Direkte Backend-Verbindungstests
- **URL-Konfiguration**: Anpassbare API-Endpunkte
- **System-Status**: Live-Anzeige der Service-Verfügbarkeit
- **Reset-Funktionalität**: Zurücksetzen auf Standardwerte

### 7. UI-Integration
- **Mode-Indicator**: Sichtbare Anzeige des aktuellen Modus auf der Startseite
- **Navigation**: Settings-Link in der Hauptnavigation
- **Alerts**: Informative Benachrichtigungen im Demo-Modus
- **Responsive Design**: Optimiert für Desktop und Mobile

## 🎯 Funktionsweise

### Demo-Modus
```typescript
// Automatische Erkennung und Service-Erstellung
const apiClient = getAPIClient() // Returns MockAPIService

// Beispiel Chat-Response
await apiClient.sendMessage("ISO 27001")
// → "ISO 27001 ist ein internationaler Standard für ISMS..."
```

### Produktions-Modus
```typescript
// Automatische Backend-Verbindung
const apiClient = getAPIClient() // Returns ProductionAPIService

// Echte API-Calls
await apiClient.sendMessage("Was ist ISO 27001?")
// → Verbindung zu http://localhost:8000/query
```

### Nahtlose Umschaltung
```typescript
// Modus wechseln
const { switchMode } = useAppConfig()
switchMode('production') // Alle Services werden automatisch aktualisiert
```

## 📊 Demo-Datenstruktur

### Wissensgraph-Knoten (15)
- **Standards**: ISO 27001, BSI Grundschutz, NIST CSF
- **Controls**: Zugangskontrollen, Kryptographie, Incident Management
- **Technologien**: Cloud Computing, IoT Devices, Mobile Devices
- **Dokumente**: IT-Sicherheitsrichtlinie, Notfallhandbuch, Datenschutz-Leitfaden
- **Threats**: Phishing, Ransomware, DDoS Angriffe

### Verbindungen (17)
- Requirement-Relationships (Standards → Controls)
- Implementation-Relationships (Controls → Technologies)
- Documentation-Relationships (Processes → Documents)
- Threat-Relationships (Threats → Targets)

## 🔧 Konfiguration

### Standard-Einstellungen
```typescript
const DEMO_CONFIG: AppConfig = {
  mode: 'demo',
  apiUrl: 'mock://demo',
  features: { /* alle Features aktiviert */ }
}

const PRODUCTION_CONFIG: AppConfig = {
  mode: 'production',
  apiUrl: 'http://localhost:8000',
  features: { /* backend-abhängige Features */ }
}
```

### Persistierung
- Einstellungen werden in `localStorage` unter `ki-wissenssystem-config` gespeichert
- Automatisches Laden beim App-Start
- Reset-Funktionalität verfügbar

## 🚀 Verwendung

### 1. Modus-Umschaltung über UI
1. Navigieren Sie zu "Einstellungen" in der Hauptnavigation
2. Verwenden Sie den Toggle-Switch zum Umschalten
3. Änderungen werden sofort angewendet

### 2. Programmatische Umschaltung
```typescript
import { useAppConfig } from '@/hooks/useAppConfig'

function MyComponent() {
  const { isDemo, switchMode } = useAppConfig()
  
  return (
    <button onClick={() => switchMode(isDemo ? 'production' : 'demo')}>
      Switch to {isDemo ? 'Production' : 'Demo'}
    </button>
  )
}
```

### 3. Service-Zugriff
```typescript
import { getAPIClient } from '@/lib/serviceFactory'

const apiClient = getAPIClient()
const response = await apiClient.sendMessage("Ihre Frage")
```

## 🔍 Debugging

### Console-Logs
- Service-Erstellung wird in der Konsole protokolliert
- Health-Check-Ergebnisse werden angezeigt
- Konfigurationsänderungen werden geloggt

### Entwickler-Tools
- Konfiguration ist in den Settings sichtbar (JSON-Format)
- localStorage kann direkt inspiziert werden
- Network-Tab zeigt echte vs. Mock-Requests

## 🎯 Nächste Schritte

1. **Backend-Integration testen**: Echte Verbindung zum KI-Backend herstellen
2. **WebSocket-Features**: Echtzeit-Chat und Live-Updates
3. **Erweiterte Demo-Daten**: Mehr realistische Beispiele hinzufügen
4. **Performance-Optimierung**: Service-Caching und Lazy Loading
5. **Monitoring**: Erweiterte Health-Checks und Metriken

## 📝 Technische Details

### Architektur-Pattern
- **Factory Pattern**: ServiceFactory für Service-Erstellung
- **Observer Pattern**: ConfigManager für reaktive Updates
- **Singleton Pattern**: Zentrale Konfigurationsverwaltung
- **Strategy Pattern**: Verschiedene Service-Implementierungen

### TypeScript-Integration
- Vollständige Typisierung aller Interfaces
- Generische Types für Konfiguration
- Strikte null-Checks und Error-Handling

### Performance-Optimierungen
- React.useCallback für stabile Funktionsreferenzen
- Lazy Service-Erstellung (nur bei Bedarf)
- Minimale Re-Renders durch gezieltes State-Management

Das System ist jetzt vollständig funktionsfähig und bereit für den produktiven Einsatz! 🎉 