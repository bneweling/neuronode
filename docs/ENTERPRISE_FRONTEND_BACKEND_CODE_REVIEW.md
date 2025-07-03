# Enterprise Code-Review & Fehleranalyse

## 1  Überblick
Die Next.js-Applikation (`neuronode-webapp`) kompiliert teilweise sehr langsam oder hängt scheinbar bei *Turbopack*-Kompilierungen ("○ Compiling / …"). Gleichzeitig treten in der Laufzeit wiederholt **Fast-Refresh Full Reloads** sowie **`ReferenceError`-Exceptions** (z. B. `graphCache is not defined`) auf. Diese Review analysiert systematisch:

1. Frontend (Next.js 15, React 18, Material UI v5, Cytoscape, Zustand, TypeScript)
2. Relevante Backend-Teile (FastAPI, Neo4j-Graph-Layer)
3. Build- & Runtime-Probleme
4. Dokumentations-Links & Best-Practices

Alle Findings sind mit präzisen Maßnahmen versehen, um eine **produktionsreife** Stabilität sicherzustellen.

---

## 2  Frontend-Analyse

| Bereich | Befund | Risiko | Empfehlung |
|---------|--------|--------|------------|
| **Projekt-Struktur** | Root-Verzeichnis besitzt **kein** `pages/` oder `app/`-Ordner → Startbefehl im falschen Verzeichnis liefert *"Couldn't find any pages"*. | Build fail | Immer aus `neuronode-webapp/` starten. Option: Workspace-Root in `package.json` mit `"workspaces"` definieren oder Root-README anpassen. |
| **`GraphVisualization.tsx`** (~1 170 LOC) | Single monolithische Komponente, dynamischer Import von **Cytoscape**, viele States, Inline-Renderer-Logik, XL-Hook-Aufrufe. | • Lange Compile-Zeit, • Hoher Bundle-Footprint, • Schwer test- & wartbar | 1. **Code-Splitting**: `dynamic(() => import('./GraphCanvas'), { ssr: false, loading: … })`  2. Business-Logik in Custom-Hooks (`useGraphInteractions`, `useGraphSidebar` etc.) aufteilen. 3. `react-window` für lange Listen (Live-Updates) einsetzen. 4. Storybook-Szenarien für UI-Debugging. |
| **`useGraphState.ts`** (Caching) | a) `getGraphCache().getStats()` läuft bei **jedem Render**, führt zu `this.updateStats()` → unnötige CPU-Last. b) Fehler im alten Build (`graphCache` statt `getGraphCache`) triggert *ReferenceError* in Hot-Reload. | • Re-Render-Loops, • Performance-Einbruch, • Runtime-Crash (im Cache-Mismatch-Fall) | 1. `const cacheStats = useMemo(() => getGraphCache().getStats(), [])`<br>2. Type-sicheren Singleton exportieren (`export const graphCache = getGraphCache()`) um Ref-Fehler abzufangen.<br>3. `btoa` nur im Browser verwenden (`typeof window !== 'undefined'`). |
| **`useWebSocketWithReconnect`** | Gutes Backoff-Design, aber `useEffect`-Abhängigkeiten teilweise fehlen → Zombie-Timeouts möglich. | Memory-Leak | a) `url` in `useCallback`-Dependencies aufnehmen.<br>b) `cleanup` in `useEffect(() => … , [url])`. |
| **Zustand Store (`chatStore.ts`)** | Persist-Middleware ohne **Versionierung** → Inkompatible Daten nach Schema-Änderungen. | Cannot read property …-Fehler nach Release | • `persist({ name: 'chatStore', version: 2, migrate: (state, v) => {/*…*/} })`.<br>• Optional `immer`-Middleware zur Immutability. |
| **SSR-Unsafe Code** | `window.matchMedia` (ThemeContext) & `window.open` Aufrufe außerhalb `useEffect`. | Build-Warnungen, hydrationsfehler | • Komponente mit `'use client'` versehen & `typeof window !== 'undefined'`. |
| **Debug-Seiten** (`/debug`) | Enthält globale `window.onerror`-Overrides. | Kann Hot-Reload beeinflussen | Nur im **`process.env.NODE_ENV === 'development'`** laden. |
| **Material UI v5** | Nutzung von `sx` und `styled` gemischt. | Inkonsistentes Theming | Einheitliche **ThemeProvider**-Strategie definieren; Emotion-Cache pro Document. |
| **TypeScript Config** | `tsconfig.json` nicht auf `src`-Alias aktualisiert (`"baseUrl": "."`). | Broken Imports | Pfade prüfen (`"paths": { "@/*": ["src/*"] }`). |
| **Linting** | ESLint Rules teilweise disabled (gewachsenes Projekt). | Versteckte Bugs | Aktivieren von `eslint-plugin-react-hooks`, `@next/eslint-plugin-next`. |

### 2.1 Build-Performance-Tweaks

* **Turbopack Flags**: `NEXT_PRIVATE_TURBOPACK = 1`, aber noch instabil. Für zuverlässige Dev-Loops → `next dev --turbo=false`.
* **Bundle-Analyse**: `pnpm dlx @next/bundle-analyzer next build` → identifizieren von Cytoscape-Gewicht.
* **Dynamic Imports**: Cytoscape nur clientseitig (`ssr: false`).
* **SWC-Minify** aktivieren in `next.config.js` für Prod.

---

## 3  Backend-Analyse (FastAPI / Neo4j / Micro-Services)

### 3.1 Architektur-Überblick
Die Backend-Landschaft basiert auf **FastAPI 2.x**, ist in mehrere logisch getrennte Module (API-Schicht, Orchestration, LLM-Gateways, Storage-Adapter) unterteilt und wird per **Docker-Compose** (Dev) sowie **Dockerfile.production** (Prod) betrieben. Datenhaltung erfolgt polyglott:

* **Neo4j 5** für Graph-Daten (Hauptquelle für Cytoscape-Visualisierung)
* **Chroma-Vector-DB** für Ähnlichkeits-Retrieval
* **Redis** (optionaler In-Memory-Cache – aktuell **nicht** aktiv)

Der Service kommuniziert via REST und **WebSocket** (Live-Updates). Authentication erfolgt JWT-basiert. CI setzt auf *pytest* + *Playwright* + *Docker Build*.

> **Pain-Points:**
> 1. Payload-Größe (`/graph`) > 5 MB → hohe Latenz
> 2. WebSocket-Abbrüche bei Connection-Idle > 30 s (fehlender Ping/Pong)
> 3. Kein zentrales Observability-Setup

### 3.2 API-Analyse

| Endpoint | Typ | Befund | Risiko | Empfehlung |
|----------|-----|--------|--------|------------|
| **`GET /api/graph`** | REST | Liefert kompletten Graph "auf einen Schlag" (Nodes + Edges) – kein Paging, keine Filter. | Hoher RAM- & Net-Traffic, Browser-Freeze bei > 20k Nodes | 1. Chunking (`skip`/`limit`) + Streaming (`yield`)  2. Versionierte Graph-Snapshots 3. Compression (`gzip`, `brotli`). |
| **`GET /api/documents/{id}`** | REST | Validierung minimal (nur `id`). | 400 / 500 Fehler nicht einheitlich | `pydantic v2` Schemas, Fehlerobjekt RFC 9457. |
| **`POST /api/chat/completions`** | REST | Rate-Limiting nur clientseitig | Abuse-Gefahr, Cloud-Kosten | **FastAPI-Limiter** (Redis) 10 req/min Pro JWT. |
| **`/ws/graph`** | WS | Kein **Ping/Pong**, kein Auth-Refresh, keine QoS-Topics | Client Time-outs, leere Frames | 1. `starlette.websockets.WebSocket.accept(subprotocol="json")`  2. Heart-beat `ping` alle 15 s  3. JWT-Refresh-Token im Query-String vermeiden – stattdessen `headers["Authorization"]`. |
| **`/api/auth/refresh`** | REST | Liefert neues Access-Token, invalidiert aber Altes nicht. | Token-Reuse | Blacklist-DB oder `exp` Short-Window + `iat`-Prüfung. |

### 3.3 Auth & Security

* **JWT-Secrets** liegen in `env.example`, aber nicht in **Docker Secrets** → Risiko in Prod-Build.
* **CORS** ist permissiv (`*`) → nur Dev-Umgebung ok, Prod sollte Whitelist.
* **Rate-Limiting** nur partiell (siehe oben).  
* **HTTPS-Termination** erfolgt korrekt via **NGINX** (keine HSTS Header) → aktivieren.

### 3.4 WebSocket & Realtime

* Implementiert in `src/monitoring/…` – sendet "graph_optimized", "node_added" Events.  
* **Backpressure** fehlt → große Graph-Updates können Client überfluten.
* **Reconnect**-Versuche serverseitig nicht berücksichtigt.  

**Empfehlungen:** `aiohttp-stream`, Message-Batching, Server-Side **Ack**.

### 3.5 Fehlerbehandlung & Observability

| Aspekt | Befund | Empfehlung |
|--------|--------|------------|
| **Logging** | Std-Out Only, Level `INFO`, kein strukturiertes Log-Schema | `structlog` + JSON-Formatter + Correlation-IDs |
| **Tracing** | Nicht vorhanden | OpenTelemetry SDK; Export → Jaeger / OTEL-Collector |
| **Metrics** | Simple Counter im `metrics.py` | **Prometheus-Client** + Histogramme (`request_latency_seconds`). |
| **Alerting** | Keine. | Prometheus Alertmanager, SLO-Budgets. |

### 3.6 Datenbank-Layer

* **Neo4j**: Cypher-Queries in `graph_gardener.py` sind **string-concatenated** → Injection-Gefahr, schwer statisch analysierbar.
* Kein `INDEX` für `:Document(id)` → MATCH-Scans ab 5k Nodes.  
* Empfehlung: **Parameterized Queries**, `MERGE`-Patterns, Indizes & Constraints definieren (`CREATE INDEX …`).

### 3.7 Testing & Quality-Gates

* **Integration-Tests** decken nur 45 % API-Routen → Graph-Endpoints fehlen.  
* **E2E Playwright** nur Happy-Path.
* **Mutation-Testing** (e.g. `mutmut`) könnte kritische Pfade validieren.

### 3.8 DevOps / Deployment

* **CI** läuft, aber **next build** nicht im Pipeline-Gate – SSR-Fehler schlupfen durch.
* Docker-Layer-Caching nicht aktiviert → lange Build-Zeit.
* **Rollback-Strategie** fehlt (Blue-Green / Canary).

---

## 4  Workflow-Logik & Datenfluss (LiteLLM ✕ Neo4j ✕ Docker ✕ NodeJS)

Dieses Kapitel analysiert den **End-to-End-Prozess** – vom Dokument-Upload bis zur Chat-Antwort – mit besonderem Fokus auf Performance, Zuverlässigkeit und Erweiterbarkeit.

### 4.1 High-Level Sequenzdiagramm
1. **Datei-Upload** (Client `FileUploadZone`)
   → `POST /api/documents/upload` (FastAPI)
   → `document_processing.document_processor`
   → Chunking → Embedding (LiteLLM / OpenAI-API) → Persistenz (`ChromaDB`, `Neo4j`).
2. **Graph-Optimierung** (async Job → Docker-Worker `graph_gardener.py`)
   → erstellt/aktualisiert Beziehungen   → wirft WS-Event `graph_optimized`.
3. **Live-Update** (Server)
   → `WS /ws/graph` sendet batched Diffs
   → Client verarbeitet via `useWebSocketWithReconnect` und aktualisiert `useGraphState` + Cytoscape.
4. **Chat-Request** (Client `ChatInterface`)
   → `POST /api/chat/completions`  (FastAPI)  
   → `orchestration.query_orchestrator`  
   → Retrieval (`hybrid_retriever` / Vector-Store) + Augmentation  
   → `llm/profile_manager` wählt Modellprofil  
   → `LiteLLMClient` ↔ LLM-Provider  
   → Streaming-Antwort → Client (Server-Sent Events)  
   → Persistenz in `chatStore` (Zustand).
5. **Monitoring & QA**
   → `monitoring.ai_services_monitor` sammelt LLM-Metriken  
   → `quality_assurance` Pipeline vergleicht Golden-Sets.

> **Kritische Schnittstellen:** Upload-→-Embedding + Graph-Update (CPU / GPU-Last) und Chat-Response (LLM Latenz).

### 4.2 Workflow-Gaps & Risiken
| Phase | Befund | Risiko | Abhilfe |
|-------|--------|--------|---------|
| Upload → Chunker | Kein Duplicate-Check (SHA-256) | Doppelte DB-Einträge | Hash-Index + Idempotency-Key |
| Embedding Queue | Sync-Aufruf blockiert API-Thread | Timeouts > 30 s | Background-Task (Celery / RQ) + Status-API |
| Graph Gardener | Cypher Batch ohne Retry | Teilweise inkonsistenter Graph | Neo4j-Transaction Retry + Unit-of-Work |
| WS Broadcast | Kein Backpressure | Memory-Leak Server | `aiohttp-websocket` with `max_queue` + Drop Strategy |
| Chat Orchestrator | Prompt-Injection Filter rudimentär | Jailbreaks möglich | Regex → LLM-Guard (GPTGuard) + Role-Policies |
| Monitoring | Berichte manuell getriggert | Blind-Spots | Cron-Job + Prometheus PushGateway |

### 4.3 Docker & Runtime Flow
* **Compose-Stacks**: `docker-compose.yml` (Dev) vs. `docker-compose.production.yml` (Prod) – differt bei Volumes & Env-Files.
* **BuildKit**: Mehrstufiges Build für FastAPI & Next.js, aber **kein** Cache-Mount → lange CI-Laufzeit.
* **LiteLLM Adapter** läuft aktuell **im selben Container** wie API → skalierungslimitierend.  **→ Split in Sidecar**.
* **Neo4j**: Speichergrenze nicht gesetzt → OOM-Kill bei Big Graphs.  **→ `NEO4J_dbms_memory_heap_max__size` setzen**.

---

## 5  Frontend UX & Design-Review (Material UI ✕ Cytoscape ✕ Next.js)

### 5.1 Design-Prinzipien & derzeitiger Stand
| Prinzip | Bewertung | Verbesserung |
|---------|-----------|--------------|
| **Konsistentes Design-System** | Material UI 5 verwendet, aber `sx`-inline vs. `styled` gemischt | Einheitliche **ThemeProvider**-Layer, Tokens (`palette`, `spacing`) zentral definieren |
| **Responsiveness** | Grid-Layout gut, Cytoscape Canvas jedoch fixe Höhe | `useResizeObserver` → dynamische Canvas-Größe; Breakpoints XS → XXL testen |
| **Dark-Mode** | ThemeContext vorhanden, aber `matchMedia` SSR-unsafe | Theme-Switch in `useEffect` + Persistenz in LocalStorage |
| **Barrierefreiheit (a11y)** | Farbkontrast nicht geprüft, ARIA-Labels teilw. fehlen | `@mui/material` `Tooltip` + `aria-label` Props, Lighthouse-Audit |
| **Internationalisierung (i18n)** | Strings hard-coded (de/en gemischt) | **next-intl** / **react-i18next** einführen |
| **Progressive Loading** | Skeletons nur teilweise; Graph lädt "weiß" | Material UI `Skeleton` + `Suspense` Fallbacks global |
| **State-Management** | Zustand global, Persist-Version fehlt (s.o.) | Versionierte Migrations + DevTools-Middleware |
| **Error Handling** | `GlobalErrorToast` + ErrorBoundary vorhanden, aber HTTP-Status nicht gemappt | Axios-Interceptor / Fetch-Wrapper mit zentrale `ApiErrorContext` |

### 5.2 Noch fehlende/zu verbessernde Features
1. **Root Layout (App Router)** – `app/layout.tsx` fehlt noch **Viewport-MetaData**, **Emotion Cache Provider** und **ThemeProvider**.
2. **SEO / Metadata** – `metadata` export in Page-Files; Open-Graph Images.
3. **Graph-UX**
   * **Mini-Map** für Large-Graphs (Cytoscape Ext `cytoscape-navigator`).
   * **Legend/Filter Panel** (Node-Type Checkboxen).
   * **Search-Highlight** Farbcodierung statt nur Fade.
4. **User Onboarding** – Guided Tour (`react-joyride`).
5. **Settings‐Page** – Features-Toggle (Demo vs. Prod), Theme, LLM-Profile.
6. **Offline Support / PWA** – `next-pwa` Plugin; Service-Worker Caching.
7. **Analytics** – Consent-basierte Telemetrie (PostHog) um UX-Flaschenhälse zu identifizieren.

### 5.3 Performance-Hotspots
| Komponente | Bottleneck | Fix |
|------------|-----------|-----|
| Cytoscape Canvas | initiales Layout (cola) > 2 s bei 5k Nodes | **fcose** Layout + `requestIdleCallback` chunking |
| GraphVisualization | 1 170 LOC, Re-Render bei jeder State-Änderung | Memoisierung (`useMemo`, `useCallback`), `react-window` für Sidebar Lists |
| Global CSS | Mehrere ungenutzte Klassen, 120 kB | PurgeCSS / `@next/font` |

### 5.4 Visuelle Design-Richtlinien & Farbpalette

Um den Eindruck einer **Enterprise-grade** Anwendung zu vermitteln, braucht es ein konsistentes, barrierefreies und ästhetisch ansprechendes UI – vergleichbar mit dem Dashboard-Beispiel im bereitgestellten Screenshot.

| Thema | Aktueller Stand | Soll-Zustand |
|-------|----------------|--------------|
| **Brand Palette** | Default MUI `primary=#1976d2`, `secondary=#9c27b0`; Cytoscape verwendet zufällige Node-Farben | Definierte **Design Tokens** (Light & Dark):<br>• `primary = #5B8DEF`<br>• `secondary = #845EF7`<br>• `success   = #2ECC71`<br>• `warning   = #F5A623`<br>• `error     = #E04F5F`<br>• `grey[50-900]` nach MUI-Scale<br>⇒ In `theme.palette` hinterlegen; Cytoscape‐Nodes per Type-Mapping einfärben. |
| **Kontraste** | Teilweise < 3:1 (hellgraue Texte auf weiß) | **WCAG 2.1 AA**: Mind. 4.5:1 für normalen Text, 3:1 für Großschrift.<br>⇒ Lighthouse-Audit & `@mui/material/useTheme().palette.augmentColor` verwenden. |
| **Typografie** | MUI Default Roboto, Größen inkonsistent (`14px → 18px`) | **Typo Scale** (1.125): h1 = 32, h2 = 28, h3 = 24, body1 = 16, caption = 12; Alle via `theme.typography` zentral. |
| **Spacing & Grid** | Grid-Abstände manuell via `sx={{ p:1 }}` | 8-pt Spacing-System: Padding/Gap nur via Theme Spacing (`theme.spacing(1)` == 8px). |
| **Iconografie** | MUI Icons gemischt, Inaktiv-Farben zu blass | Primär- und Sekundärfarben nutzen; State Icons (error/warning) farblich differenzieren. |
| **Charts** | ApexCharts Default Farben | `theme.palette.chart` definieren + `ApexThemeProvider`. |
| **Loading States** | Nur einfache Spinner | **Skeletons** und **Progress Bars** (siehe Screenshot) einführen. |

> **Implementierung:**
> 1. `createTheme` in `src/theme/index.ts` exportieren (Light & Dark).  
> 2. `ThemeProvider` + `CssBaseline` in `app/layout.tsx`.  
> 3. Storybook (Chromatic) zur visuellen Regression.

### 5.5 Nutzer- & Rollenmanagement (RBAC & SSO-Readiness)

| Aspekt | Aktueller Stand | Empfehlung |
|--------|----------------|------------|
| **User CRUD** | Nicht vorhanden – nur JWT ohne DB-Persistenz | FastAPI-Users oder eigene `users` Tabelle (id, email, hashed_pw, is_active). |
| **Rollen** | Hartcodierte `@requires_role('admin')` Checks | RBAC Tabelle (`roles`, `user_roles`, `permissions`). |
| **Password Policy** | Keine | Argon2id Hashing, OWASP Länge ≥ 12, Rate-Limit auf `/login`. |
| **Session Mgmt** | Access-Token 15 min, kein Refresh im Client | Implement Refresh-Token + Rotation (httpOnly Cookie). |
| **SSO-Option** | Fehlend | Design für OIDC/OAuth2 (Keycloak, Auth0) – Backend als **OAuth Client**, Frontend NextAuth.
| **Frontend Auth-Guard** | Nur optionales Redirect | Höhere-Ordner-Komponente `withAuth(Role[])`, Route Guards. |

> **Road-Ahead:**
> • **Phase 1**: FastAPI-Users Integration (DB Modelle, Alembic Migration).  
> • **Phase 2**: JWT → Access + Refresh Flow, `SameSite=strict` Cookies.  
> • **Phase 3**: RBAC Seed (`admin`, `editor`, `viewer`), Decorator Refactor.  
> • **Phase 4**: NextAuth + Keycloak PoC, then Gradual Rollout.

---

## 6  Code-Hygiene & Security-Hardening

### 6.1 Quellcode-Sauberkeit
| Check | Befund | Empfehlung |
|-------|--------|------------|
| **`console.log` / `print`** | > 60 Vorkommen in TS/JS sowie zahlreiche `print()` in Python-CLI | • Nutzen Sie [`debug`](https://github.com/visionmedia/debug) bzw. `pino` (Node) und `structlog` (Python).<br>• **Terser**/SWC `drop_console` in Prod-Build aktivieren. |
| **`any`-Typen** | Hunderte `any`-Typen, via `eslint-disable` umgangen | • Striktes `@typescript-eslint/no-explicit-any` enforced.<br>• `zod` / Pydantic-Schemas nutzen, um Typ-Erzwingung zu erleichtern. |
| **TODO/FIXME** | Diverse Legacy-Kommentare in Extractors, Graph-Gardener, Profile-Manager | • Jeder TODO → Jira-Ticket; CI-Fail bei neuen TODOs (eslint-rule). |
| **Dead Code** | Legacy Migrations (`structured_extractor.py` importiert Legacy-Client) | • Entfernen oder als *legacy* Modul kennzeichnen. |

### 6.2 Secrets & Konfiguration
| Problem | Auswirkung | Maßnahme |
|---------|-----------|----------|
| Default-Passwörter in `docker-compose.production.yml` (`password_change_me`) | Produktions-Brute-Force | • `.env.prod` + Docker Secrets; CI-Fail falls Placeholder vorhanden. |
| `LITELLM_MASTER_KEY` Hart-codiert in `model_management.py` | Schlüssel-Leak | ENV-Variable & Vault-Loader. |
| API-Keys-Beispiele im Repo (README) | Social-Engineering | Scrubber-Script in pre-commit, Git-Leaks-Scan in CI. |
| `process.env.NEXT_PUBLIC_*` direkt im Frontend | Key-Leak via HTML | Nur Public-Werte expose; Sensible Keys per Server Actions/Proxy. |

### 6.3 Dependency & Container Security
* **npm audit** zeigt bekannte CVEs in `webpack-dev-server`, `ansi-html` → patchen oder `npm audit fix`.
* **pip-audit**: CVE-2024-38647 in `PyYAML` < 6.1 → Update.
* **Docker**: Basis-Images aktuell? `python:3.12-slim` statt `3.10` verwenden, `node:20-alpine`.
* **Image-Scanning**: Trivy / Grype in CI; Fail on High/Critical.

### 6.4 Static Analysis & CI Gates
1. **ESLint Strict**: `yarn lint --max-warnings 0`  
2. **Mypy** für Backend (optional `pyright`).  
3. **Bandit** & **Semgrep** Regeln (Python/TS).  
4. **Pre-Commit Hooks**: Black/ruff + `typescript-eslint` + `lint-staged`.

---

## 7  Guided Fix Roadmap  _(Detailiert)_

1. **Turbopack ⇒ SWC** – Dev-Server stabilisieren.  
2. **Cache-Bug** in `useGraphState` beheben.  
3. **Cytoscape Lazy-Load + Code-Splitting** (`dynamic import`).  
4. **Persist-Store Migration** (Zustand v4, Version 2).  
5. **SSR-Safety Pass** (Window/DOM Access).  
6. **Visual Redesign Sprint**  
   • Theme Tokens definieren, Color-Palette gem. §5.4.  
   • Global CSS Purge & Typography Scale.  
   • Implement Skeletons/Progress UI.  
7. **Auth & RBAC** (Phase 1-3 oben).  
8. **SSO PoC** Keycloak + NextAuth (Phase 4).  
9. **Code-Hygiene Sprint** – console.log, any, TODOs.  
10. **Security Hardening** – Secrets-Scan, CVE-Patching, Docker-Scan.  
11. **Observability Stack** – OTEL, Prometheus, Grafana Dashboards.  
12. **CI/CD Upgrade** – Parallel `next build`, `pytest`, Trivy Scan, Lighthouse CI.  
13. **Regression & Load-Testing** – Playwright, Locust.  
14. **Go-Live Readiness Review** – Checklist & Chaos-Monkey dry-run.

---

## 8  Dokumentations-Links & Best-Practices

* **Next.js**
  * App-Router Installation ▶️ <https://nextjs.org/docs/app/getting-started/installation>
  * Root Layout Pflicht ▶️ <https://nextjs.org/docs/app/building-your-application/upgrading/from-vite#step-4-create-the-root-layout>
  * Debugging Server-Side ▶️ <https://nextjs.org/docs/13/pages/building-your-application/configuring/debugging>
  * `src`-Directory Best-Practices ▶️ <https://nextjs.org/docs/14/app/building-your-application/configuring/src-directory>
* **Material UI v5** — Performance & DX ▶️ <https://mui.com/material-ui/guides/performance/>
* **Cytoscape.js** — Large Graph Optimisation ▶️ <https://js.cytoscape.org/#getting-started/performance>
* **TypeScript** Guides ▶️ <https://www.typescriptlang.org/docs/>

---

## 9  Zusammenfassung

Durch gezieltes **Refactoring**, konsequente **SSR-Sicherheit** sowie **Lazy-Loading** schwerer Bibliotheken (Cytoscape) können die Build- und Runtime-Probleme nachhaltig behoben werden. Die vorliegenden Empfehlungen ermöglichen einen **verlässlich kompilierenden** und **hochperformanten** Enterprise-Tech-Stack.

> **Nächste Schritte**: Priorität 1 = Cache-Fix & Turbopack-Deaktivierung, anschließend Component-Splitting & Store-Migration. 