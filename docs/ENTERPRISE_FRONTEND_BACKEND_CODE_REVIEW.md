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
| **`GET /api/graph`** | REST | Liefert kompletten Graph „auf einen Schlag“ (Nodes + Edges) – kein Paging, keine Filter. | Hoher RAM- & Net-Traffic, Browser-Freeze bei > 20k Nodes | 1. Chunking (`skip`/`limit`) + Streaming (`yield`)  2. Versionierte Graph-Snapshots 3. Compression (`gzip`, `brotli`). |
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

* Implementiert in `src/monitoring/…` – sendet „graph_optimized“, „node_added“ Events.  
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

## 4  Guided Fix Roadmap

1. **Build stabilisieren**
   ```bash
   # Temporär ohne Turbopack
   NEXT_TELEMETRY_DISABLED=1 npm run dev -- --turbo=false
   ```
2. **Cache-Bug fixen** (`useGraphState`)
3. **Cytoscape Lazy Load** & Component-Split
4. **Persist-Store Migration**
5. **SSR-Safety Pass** (`grep -R "window." src | xargs sed -n '…'`)
6. **Automatisierte Tests**
   * Playwright E2E für `/graph`
   * Jest + React-Testing-Library für `useGraphState`
7. **CI-Pipeline** (ESLint, `next build`, `docker build`, `pytest`).

---

## 5  Dokumentations-Links & Best-Practices

* **Next.js**
  * App-Router Installation ▶️ <https://nextjs.org/docs/app/getting-started/installation>
  * Root Layout Pflicht ▶️ <https://nextjs.org/docs/app/building-your-application/upgrading/from-vite#step-4-create-the-root-layout>
  * Debugging Server-Side ▶️ <https://nextjs.org/docs/13/pages/building-your-application/configuring/debugging>
  * `src`-Directory Best-Practices ▶️ <https://nextjs.org/docs/14/app/building-your-application/configuring/src-directory>
* **Material UI v5** — Performance & DX ▶️ <https://mui.com/material-ui/guides/performance/>
* **Cytoscape.js** — Large Graph Optimisation ▶️ <https://js.cytoscape.org/#getting-started/performance>
* **TypeScript** Guides ▶️ <https://www.typescriptlang.org/docs/>

---

## 6  Zusammenfassung

Durch gezieltes **Refactoring**, konsequente **SSR-Sicherheit** sowie **Lazy-Loading** schwerer Bibliotheken (Cytoscape) können die Build- und Runtime-Probleme nachhaltig behoben werden. Die vorliegenden Empfehlungen ermöglichen einen **verlässlich kompilierenden** und **hochperformanten** Enterprise-Tech-Stack.

> **Nächste Schritte**: Priorität 1 = Cache-Fix & Turbopack-Deaktivierung, anschließend Component-Splitting & Store-Migration. 