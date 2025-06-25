# Frontend-Backend-Integration & Demo/Produktions-Modus Plan

## 🎯 Ziele
- Vollständige Kompatibilität zwischen Frontend und Backend sicherstellen
- Umschaltmöglichkeit zwischen Demo-Modus (synthetische Daten) und Produktions-Modus (echte API)
- Nahtlose Integration wie beim Obsidian Plugin
- Einfache Konfiguration für Entwicklung und Produktion

## 📋 Ist-Zustand Analyse

### Aktuelle API-Integration
- ✅ API-Client in `src/lib/api.ts` implementiert
- ✅ Dummy-Daten für Offline-Betrieb vorhanden  
- ✅ WebSocket-Client für Real-time Chat
- ❓ Backend-Kompatibilität ungeklärt
- ❓ Keine Umschaltmöglichkeit zwischen Modi

### Backend-Endpoints (zu prüfen)
- `/api/chat` - Chat-Nachrichten senden
- `/api/documents/upload` - Dokumente hochladen  
- `/api/graph` - Wissensgraph abrufen
- `/api/system/status` - Systemstatus
- `/ws/chat` - WebSocket für Real-time Chat

## 🔧 Implementierungsplan

### Phase 1: Backend-Kompatibilität prüfen
1. **Backend-Analyse durchführen**
   - [ ] Bestehende API-Endpoints im Backend identifizieren
   - [ ] Request/Response-Schemas vergleichen
   - [ ] WebSocket-Implementation prüfen
   - [ ] Authentication/Authorization-Mechanismen checken

2. **API-Schema-Mapping**
   - [ ] Frontend-Interfaces mit Backend-DTOs abgleichen
   - [ ] Transformation-Layer implementieren falls nötig
   - [ ] Error-Handling harmonisieren

### Phase 2: Konfigurationssystem implementieren
1. **Environment-Management**
   ```typescript
   // src/config/environment.ts
   export interface AppConfig {
     mode: 'demo' | 'production'
     apiUrl: string
     wsUrl: string
     features: {
       mockData: boolean
       realTimeChat: boolean
       fileUpload: boolean
     }
   }
   ```

2. **Modus-Umschaltung**
   - [ ] Settings-Seite erstellen (`/settings`)
   - [ ] Persistent Storage für Konfiguration (localStorage)
   - [ ] Runtime-Umschaltung ohne Page-Reload
   - [ ] Visual Indicator für aktuellen Modus

### Phase 3: Demo-Modus ausbauen
1. **Erweiterte Mock-Daten**
   - [ ] Realistische Wissensgraph-Daten
   - [ ] Chat-Conversation-Samples
   - [ ] System-Performance-Metriken
   - [ ] Upload-Progress-Simulation

2. **Mock-Services**
   ```typescript
   // src/services/mockServices.ts
   class MockAPIService implements KIWissenssystemAPI {
     // Vollständige Demo-Implementation
   }
   ```

### Phase 4: Produktions-Integration
1. **Backend-Connection-Testing**
   - [ ] Health-Check-Endpoints
   - [ ] Connection-Retry-Logic
   - [ ] Fallback-Mechanismen
   - [ ] Error-Recovery

2. **Authentication-Integration**
   - [ ] JWT-Token-Handling (falls erforderlich)
   - [ ] Session-Management
   - [ ] Automatic-Refresh-Logic

### Phase 5: Seamless-Switching-Implementation
1. **Service-Factory-Pattern**
   ```typescript
   // src/lib/serviceFactory.ts
   export function createAPIClient(mode: 'demo' | 'production'): KIWissenssystemAPI {
     return mode === 'demo' 
       ? new MockAPIService() 
       : new ProductionAPIService()
   }
   ```

2. **State-Management**
   - [ ] Global State für aktuellen Modus
   - [ ] Service-Instance-Caching
   - [ ] Data-Persistence zwischen Modi

### Phase 6: UI/UX-Verbesserungen
1. **Modus-Indicator**
   - [ ] Header-Badge für aktuellen Modus
   - [ ] Color-Scheme-Unterschiede (Demo vs Production)
   - [ ] Status-Informationen in Footer

2. **Settings-Interface**
   - [ ] Toggle-Switch für Modus-Wechsel
   - [ ] API-URL-Konfiguration
   - [ ] Feature-Flags-Management
   - [ ] Reset-to-Defaults-Option

## 🧪 Testing-Strategie

### Automatisierte Tests
1. **API-Compatibility-Tests**
   - [ ] Mock vs Real API Response-Schemas
   - [ ] Error-Handling-Consistency
   - [ ] Performance-Benchmarks

2. **Integration-Tests**
   - [ ] Mode-Switching ohne Data-Loss
   - [ ] WebSocket-Connection-Stability
   - [ ] File-Upload-End-to-End

### Manuelle Tests
1. **Demo-Modus-Validierung**
   - [ ] Alle Features funktional ohne Backend
   - [ ] Realistische Daten-Darstellung
   - [ ] Performance-Simulation

2. **Produktions-Modus-Validierung**
   - [ ] Echte Backend-Verbindung
   - [ ] Obsidian-Plugin-Kompatibilität
   - [ ] Real-time-Features

## 📦 Deliverables

### Code-Komponenten
- [ ] `src/config/environment.ts` - Konfigurationssystem
- [ ] `src/services/mockService.ts` - Demo-Daten-Service
- [ ] `src/services/productionService.ts` - Produktions-API-Service
- [ ] `src/lib/serviceFactory.ts` - Service-Factory
- [ ] `src/components/settings/` - Settings-UI-Komponenten
- [ ] `src/hooks/useAppConfig.ts` - Configuration-Hook

### UI-Komponenten
- [ ] Settings-Seite mit Modus-Umschaltung
- [ ] Modus-Indicator in Header/Footer
- [ ] Connection-Status-Anzeige
- [ ] Error-Boundary für API-Fehler

### Dokumentation
- [ ] API-Integration-Guide
- [ ] Deployment-Anweisungen
- [ ] Troubleshooting-Guide
- [ ] Feature-Toggle-Dokumentation

## 🚀 Rollout-Plan

### Phase 1 (Sofort) - Backend-Analyse
- Backend-Endpoints dokumentieren
- Schema-Kompatibilität prüfen
- Connection-Tests durchführen

### Phase 2 (Tag 1) - Basis-Konfiguration
- Environment-System implementieren
- Erste Modus-Umschaltung
- Mock-Service ausbauen

### Phase 3 (Tag 2) - UI-Integration
- Settings-Seite erstellen
- Visual-Indicators hinzufügen
- User-Experience polieren

### Phase 4 (Tag 3) - Testing & Finalisierung
- Alle Tests durchführen
- Documentation vervollständigen
- Production-Ready-Status erreichen

## ⚠️ Risiken & Mitigation

### Backend-Inkompatibilität
- **Risiko**: API-Schemas stimmen nicht überein
- **Mitigation**: Adapter-Pattern für Schema-Transformation

### Performance-Issues
- **Risiko**: Mode-Switching verursacht Delays
- **Mitigation**: Lazy-Loading und Service-Caching

### Data-Loss beim Switching
- **Risiko**: User-Daten gehen beim Modus-Wechsel verloren
- **Mitigation**: State-Persistence-Layer implementieren

## 📊 Success-Criteria

- ✅ Nahtloser Wechsel zwischen Demo und Produktion
- ✅ Vollständige Backend-Kompatibilität
- ✅ Keine Funktions-Einschränkungen in beiden Modi
- ✅ Intuitive User-Experience
- ✅ Obsidian-Plugin-Level-Integration
- ✅ Zero-Downtime-Mode-Switching

---

**Nächste Schritte:** Phase 1 starten mit Backend-Analyse und Kompatibilitätsprüfung. 