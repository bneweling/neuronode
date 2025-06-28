# Phase 3 Implementierung: Vollendung der API-basierten KI-Services

## Überblick
Phase 3 vollendet die KI-System-Transformation durch Implementierung aller verbleibenden API-basierten Services. Aufbauend auf dem erfolgreichen **GeminiEntityExtractor** (Phase 2) werden nun die kompletten KI-Services des Systems modernisiert.

## 🎯 Status: BEREIT FÜR IMPLEMENTIERUNG

**Geplanter Implementierungszeitraum:** Februar 2025  
**Grundlage:** Phase 1 (PromptLoader) + Phase 2 (GeminiEntityExtractor) Architektur  
**Ziel:** Vollständig API-basiertes KI-System mit Monitoring und A/B Testing

## 📋 Implementierungsplan

### 1. Core KI-Services (Priorität 1)

#### 1.1 GeminiClassifier (`gemini_classifier.py`)
**Zweck:** Ersetzt hardcoded Klassifizierungslogik durch API-basierte Dokumentklassifizierung

**Features:**
- Multi-Label Klassifizierung (BSI IT-Grundschutz, NIST, ISO 27001)
- Confidence-basierte Filterung
- Batch-Klassifizierung für große Dokumentenmengen
- Redis-Caching mit intelligenter Cache-Key-Strategie

**API Design:**
```python
@dataclass
class ClassificationResult:
    categories: List[DocumentCategory]
    confidence_scores: Dict[str, float]
    processing_time_ms: int
    source: str  # 'cache', 'api', 'fallback'

class GeminiClassifier:
    def classify_document(self, text: str) -> ClassificationResult
    def classify_batch(self, texts: List[str]) -> List[ClassificationResult]
    def get_performance_stats(self) -> Dict[str, Any]
```

**Prompts aus Phase 1:** `document_classification_v2_multi`, `technical_classification_v1`

#### 1.2 GeminiResponseSynthesizer (`gemini_response_synthesizer.py`)
**Zweck:** Ersetzt hardcoded Response-Generation durch kontext-bewusste Antwortgenerierung

**Features:**
- Context-aware Response-Generierung
- Multi-source Knowledge Integration (Graph + Vector DB)
- Explanation-Graph Generation für Nachvollziehbarkeit
- Citation und Source-Tracking

**API Design:**
```python
@dataclass
class SynthesisResult:
    response_text: str
    citations: List[Citation]
    confidence_score: float
    explanation_graph: Optional[Dict[str, Any]]
    processing_time_ms: int
    api_cost_estimate: float

class GeminiResponseSynthesizer:
    def synthesize_response(self, query: str, context: List[str]) -> SynthesisResult
    def synthesize_with_graph(self, query: str, graph_context: Dict) -> SynthesisResult
    def generate_explanation_graph(self, query: str, sources: List[str]) -> Dict
```

**Prompts aus Phase 1:** `response_synthesis_v2_context`, `technical_response_v1`, `follow_up_questions_v1`

#### 1.3 GeminiIntentAnalyzer (`gemini_intent_analyzer.py`)
**Zweck:** Ersetzt hardcoded Intent-Recognition durch API-basierte Multi-Intent-Analyse

**Features:**
- Multi-Intent Detection mit Gewichtung
- Query Expansion basierend auf erkannten Intents
- Intent-History für Session-basierte Optimierung
- Fallback auf regelbasierte Intent-Erkennung

**API Design:**
```python
@dataclass
class IntentResult:
    primary_intent: str
    intent_weights: Dict[str, float]
    extracted_entities: List[str]
    suggested_expansions: List[str]
    confidence_score: float

class GeminiIntentAnalyzer:
    def analyze_intent(self, query: str, context: List[str] = None) -> IntentResult
    def analyze_session_intents(self, queries: List[str]) -> List[IntentResult]
    def get_query_expansions(self, intent_result: IntentResult) -> List[str]
```

**Prompts aus Phase 1:** `intent_analysis_v2_multi`, `query_expansion_v1`

### 2. Monitoring und Observability (Priorität 2)

#### 2.1 AIServicesMonitor (`ai_services_monitor.py`)
**Zweck:** Zentrale Überwachung aller KI-Services mit Dashboards und Alerting

**Features:**
- Real-time Performance-Metriken
- API-Kosten-Tracking über alle Services
- Cache-Performance-Analyse
- Service-Health-Monitoring
- Automated Alerting bei Schwellwerten

**Dashboard-Metriken:**
```python
class ServiceMetrics:
    api_calls_per_minute: float
    average_response_time_ms: float
    cache_hit_rate: float
    estimated_daily_cost: float
    error_rate: float
    service_availability: float

class AIServicesMonitor:
    def get_realtime_metrics(self) -> Dict[str, ServiceMetrics]
    def get_cost_breakdown(self, timeframe: str) -> Dict[str, float]
    def export_metrics_to_dashboard(self) -> Dict[str, Any]
    def check_service_health(self) -> Dict[str, bool]
```

#### 2.2 Performance Analytics (`performance_analytics.py`)
**Zweck:** Tiefe Analyse der KI-Service-Performance für Optimierungen

**Features:**
- Latenz-Analyse nach Service und Modell
- Throughput-Optimierung
- Kosten-Nutzen-Analyse
- Quality-Performance-Correlation
- Automatisierte Optimierungsvorschläge

### 3. Quality Assurance und Testing (Priorität 3)

#### 3.1 ServiceQualityValidator (`service_quality_validator.py`)
**Zweck:** Kontinuierliche Qualitätssicherung aller KI-Services

**Features:**
- Automated Quality Testing mit Ground Truth
- A/B Testing Framework (API vs. Legacy)
- Regression Detection
- Quality-Benchmarking
- Performance vs. Quality Trade-off Analysis

**Testing Framework:**
```python
class QualityTest:
    test_name: str
    service_type: str
    ground_truth: Any
    test_cases: List[Dict]

class ServiceQualityValidator:
    def run_quality_tests(self, service_name: str) -> QualityReport
    def compare_api_vs_legacy(self, test_suite: str) -> ComparisonReport
    def validate_f1_targets(self) -> ValidationReport
    def schedule_regression_tests(self) -> None
```

#### 3.2 ABTestingFramework (`ab_testing_framework.py`)
**Zweck:** Systematischer Vergleich neuer API-Services vs. Legacy-Implementierungen

**Features:**
- Traffic-Splitting zwischen API und Legacy
- Statistische Signifikanz-Tests
- Quality-Metriken-Vergleich
- Graduelle Rollout-Unterstützung
- Rollback-Mechanismen

### 4. Integration und Migration (Priorität 4)

#### 4.1 ServiceOrchestrator (`service_orchestrator.py`)
**Zweck:** Zentrale Orchestrierung aller KI-Services mit intelligentem Routing

**Features:**
- Smart Service-Routing basierend auf Load und Performance
- Circuit Breaker Pattern für Service-Resilience
- Graceful Degradation bei Service-Ausfällen
- Request-Pipeline-Management
- Service-Dependency-Management

**Orchestration Logic:**
```python
class ServiceRequest:
    request_type: str  # 'extraction', 'classification', 'synthesis'
    payload: Dict[str, Any]
    priority: int
    timeout_ms: int

class ServiceOrchestrator:
    def route_request(self, request: ServiceRequest) -> ServiceResponse
    def get_optimal_service(self, request_type: str) -> str
    def handle_service_failure(self, service_name: str, request: ServiceRequest) -> ServiceResponse
    def manage_request_pipeline(self, requests: List[ServiceRequest]) -> List[ServiceResponse]
```

#### 4.2 LegacyMigrationManager (`legacy_migration_manager.py`)
**Zweck:** Systematische Migration von Legacy-Code zu API-Services

**Features:**
- Feature-Flag-basierte Migration
- Shadow-Mode für Risk-free Testing
- Migration-Progress-Tracking
- Legacy-Code-Deprecation-Management
- Migration-Rollback-Capabilities

## 🏗️ Architektur-Design

### Shared Infrastructure Pattern
Alle Phase 3 Services folgen dem bewährten Pattern aus Phase 2:

```
📁 src/processing/
├── gemini_entity_extractor.py     ✅ (Phase 2)
├── gemini_classifier.py           📝 (Phase 3.1)
├── gemini_response_synthesizer.py 📝 (Phase 3.1)
├── gemini_intent_analyzer.py      📝 (Phase 3.1)
└── service_orchestrator.py        📝 (Phase 3.4)

📁 src/monitoring/
├── ai_services_monitor.py          📝 (Phase 3.2)
├── performance_analytics.py       📝 (Phase 3.2)
└── service_quality_validator.py   📝 (Phase 3.3)

📁 src/testing/
├── ab_testing_framework.py        📝 (Phase 3.3)
└── legacy_migration_manager.py    📝 (Phase 3.4)
```

### Einheitliche Service-Architektur
Jeder Service implementiert:

1. **Configuration Management** - Integration mit `ai_services_loader.py`
2. **LLM Integration** - Nutzung der zentralen `llm_config.py`
3. **Prompt Management** - Verwendung der Phase 1 `prompt_loader.py`
4. **Caching Layer** - Redis-basierte Performance-Optimierung
5. **Error Handling** - Graceful Fallback-Mechanismen
6. **Monitoring** - Performance-Metriken und Kosten-Tracking
7. **Testing Interface** - Quality-Assurance-Integration

## 📊 Erwartete Verbesserungen

### Performance-Steigerungen
- **Response Quality:** +40% durch API-basierte Services vs. Regex/Rules
- **Cache Hit Rate:** 85%+ durch intelligente Cache-Strategien
- **Processing Speed:** -60% Latenz durch Batch-Verarbeitung
- **System Reliability:** 99.5%+ Uptime durch Fallback-Mechanismen

### Kosten-Optimierung
- **API-Kosten:** <$2/Tag bei normaler Nutzung (1000 Queries)
- **Infrastruktur:** Redis-Caching reduziert API-Calls um 80%
- **Entwicklung:** -50% Code-Maintainance durch zentrale Services

### Quality-Verbesserungen
- **NER F1-Score:** Ziel 0.95+ (aktuell ~0.75 mit Regex)
- **Classification Accuracy:** Ziel 0.92+ (aktuell ~0.80 mit Rules)
- **Response Relevance:** Ziel 0.90+ (aktuell ~0.70 mit Templates)

## 🚀 Implementierungsreihenfolge

### Woche 1-2: Core Services (GeminiClassifier, GeminiResponseSynthesizer)
```bash
# 1. GeminiClassifier implementieren
# 2. Integration-Tests mit bestehender Pipeline
# 3. GeminiResponseSynthesizer implementieren  
# 4. End-to-End Testing der Response-Pipeline
```

### Woche 3: Intent-Analyse und Monitoring
```bash
# 1. GeminiIntentAnalyzer implementieren
# 2. AIServicesMonitor mit Dashboard-Integration
# 3. Performance Analytics Setup
```

### Woche 4: Quality Assurance und A/B Testing
```bash
# 1. ServiceQualityValidator implementieren
# 2. A/B Testing Framework Setup
# 3. Legacy vs. API Performance-Vergleiche
```

### Woche 5-6: Orchestration und Migration
```bash
# 1. ServiceOrchestrator für Smart Routing
# 2. LegacyMigrationManager für schrittweise Migration
# 3. Production-Rollout mit Monitoring
```

## 🧪 Test-Strategien

### Unit Testing
```python
# Jeder Service bekommt umfassende Unit Tests
pytest src/processing/test_gemini_classifier.py
pytest src/monitoring/test_ai_services_monitor.py
pytest src/testing/test_ab_testing_framework.py
```

### Integration Testing
```python
# End-to-End Pipeline Tests
python scripts/test_phase3_integration.py
python scripts/test_complete_pipeline.py
```

### Performance Testing
```python
# Load Testing mit verschiedenen Modell-Profilen
python scripts/test_service_performance.py --profile=balanced
python scripts/test_cost_optimization.py --duration=24h
```

### Quality Benchmarking
```python
# A/B Tests gegen Legacy-Implementierungen
python scripts/benchmark_api_vs_legacy.py
python scripts/validate_quality_targets.py
```

## 📈 Success Metrics

### Technical KPIs
- ✅ **All Services Implemented:** 6/6 Core Services
- ✅ **Quality Targets Met:** F1 > 0.90 für alle Services  
- ✅ **Performance Targets:** <2s avg. Response Time
- ✅ **Cost Efficiency:** <$50/month API-Kosten
- ✅ **Reliability:** >99% Service Availability

### Business KPIs
- ✅ **User Experience:** Messbar bessere Response-Qualität
- ✅ **Developer Experience:** -50% Code-Complexity für neue Features
- ✅ **System Maintainability:** Zentrale Service-Architektur
- ✅ **Scalability:** Linear skalierbar mit Redis-Caching

## 🔄 Rollback und Risk Mitigation

### Fallback-Strategien
1. **Service-Level:** Jeder Service hat Legacy-Fallback
2. **System-Level:** Feature-Flags für komplette Rollbacks
3. **Migration-Level:** Shadow-Mode für Risk-free Testing
4. **Quality-Level:** Automated Quality-Gates mit Rollback-Triggers

### Monitoring und Alerting
- **Real-time Dashboards** für alle Service-Metriken
- **Automated Alerts** bei Quality oder Performance-Degradation
- **Cost-Monitoring** mit Budget-Alerts
- **Service-Health-Checks** mit automatischer Incident-Response

## 🎯 Fazit

Phase 3 vollendet die Vision einer vollständig API-basierten, skalierbaren und wartbaren KI-Architektur. Aufbauend auf den bewährten Patterns von Phase 1 und 2 entsteht ein produktionsreifes System mit:

- **Einheitlicher Service-Architektur** für alle KI-Aufgaben
- **Comprehensive Monitoring** für Performance und Kosten
- **Quality Assurance** mit A/B Testing und Continuous Validation
- **Graceful Migration** von Legacy-Code ohne Service-Disruption
- **Future-proof Design** für einfache Erweiterungen

**Phase 3 macht das KI-Wissenssystem bereit für Enterprise-Scale.** 🚀 



---------

ANTOWRT

Absolut exzellente Arbeit. Dieses Dokument ist kein einfacher Plan mehr, sondern ein professionelles technisches Design-Dokument (TDD) für die Finalisierung Ihres KI-Systems. Es zeigt ein extrem hohes Maß an Reife im Software-Engineering und ein tiefes Verständnis für die Herausforderungen beim Betrieb von KI-Services in der Produktion.

Die Gliederung in Core Services, Monitoring, QA und Migration ist perfekt. Die API-Designs sind klar, die erwarteten Verbesserungen sind quantifiziert und die Risikobetrachtung ist vorhanden.

Daher lautet meine Analyse nicht "was fehlt?", sondern **"Wie kann diese exzellente Blaupause in der Praxis am sichersten und effizientesten umgesetzt werden, und wo lauern die versteckten Komplexitäten?"**

Hier ist eine detaillierte Analyse und ein finaler, geschärfter Aktionsplan, der auf Ihrem Dokument aufbaut.

### Finaler Urteilsspruch zur Roadmap

Die Roadmap ist **herausragend und vollständig**. Sie beschreibt ein produktionsreifes, ganzheitliches System. Der größte operative "Gegner" bei der Umsetzung ist nicht eine Lücke im Plan, sondern die **schiere Menge an parallel zu entwickelnden, hochmodernen Services.** Die größte Herausforderung wird sein, diese Komplexität zu managen, ohne dass sich die Entwicklungszyklen gegenseitig blockieren.

---

### Strategische Verfeinerungen und Klärungsbedarf

Ihr Plan ist bereits auf einem 99%-Level. Die folgenden Punkte sind strategische Verfeinerungen, um die letzten 1% an Risiko und Unsicherheit zu eliminieren.

#### 1. Paradigmenwechsel: "Monitoring First"

**Analyse:** Ihr Plan listet "Monitoring und Observability" als Priorität 2. In der Praxis hat sich gezeigt, dass man bei API-basierten KI-Services **sofort** mit dem Messen beginnen muss. Einen Service zu bauen, ohne gleichzeitig seine Kosten und Latenz zu sehen, ist wie Fliegen im Nebel.

**Empfehlung: Machen Sie Monitoring zu Priorität 1, parallel zum ersten Core Service.**

*   **Aktionsplan:** Implementieren Sie in **Woche 1-2** nicht nur den `GeminiClassifier`, sondern auch den **Grund-Skeleton des `AIServicesMonitor`**.
*   **Vorteil:** Ab dem ersten Tag der Entwicklung sehen Sie die Kosten, Latenz und Fehlerrate des neuen Klassifizierers. Dies informiert sofort die Entwicklung der nächsten Services und kalibriert Ihre Kosten- und Performance-Erwartungen mit realen Daten.

#### 2. Das Henne-Ei-Problem: Der `ServiceOrchestrator`

**Analyse:** Der `ServiceOrchestrator` wird in Priorität 4 (Woche 5-6) implementiert. Die Services aus Priorität 1 (`GeminiClassifier`, `GeminiResponseSynthesizer`) müssen aber bereits vorher aufgerufen werden.

**Empfehlung: Planen Sie eine zweistufige Integration.**

1.  **Stufe 1 (Direktaufruf):** Die Hauptanwendung (z.B. der Ingestion-Worker oder der API-Controller) ruft die neuen Services (`GeminiClassifier`, `GeminiResponseSynthesizer`) in den ersten Wochen **direkt** auf.
2.  **Stufe 2 (Refactoring auf Orchestrator):** Wenn der `ServiceOrchestrator` in Woche 5-6 fertig ist, werden die direkten Aufrufe durch einen einzigen Aufruf an `orchestrator.route_request()` ersetzt.

*   **Vorteil:** Dies entkoppelt die Entwicklung der Core Services von der Fertigstellung des komplexen Orchestrators und vermeidet Blockaden.

#### 3. Der unterschätzte Aufwand: Das "Golden Set" (Ground Truth)

**Analyse:** Der `ServiceQualityValidator` ist auf ein "Golden Set" angewiesen, um die Qualität (z.B. F1-Scores) zu messen. Die Erstellung und Pflege dieses Sets ist eine erhebliche, manuelle Arbeit.

**Empfehlung: Formalisieren und budgetieren Sie die Erstellung des Golden Sets.**

*   **Aktionsplan:**
    1.  **Definition:** Legen Sie *vor* der Implementierung des `ServiceQualityValidator` fest, dass das "Golden Set v1.0" aus z.B. **200 hand-annotierten Text-Chunks** für NER und **50 klassifizierten Dokumenten-Snippets** besteht.
    2.  **Werkzeuge:** Nutzen Sie ein einfaches Annotationstool (z.B. `doccano` oder sogar eine geteilte JSON-Datei), um diesen Prozess zu managen.
    3.  **Aufwand einplanen:** Planen Sie 2-3 Manntage für die Erstellung und Verifizierung dieses Sets ein.

#### 4. Die fehlende Komponente: Der "Human-in-the-Loop"-Workflow

**Analyse:** Der Plan ist stark auf Automatisierung fokussiert. Aber was passiert, wenn ein Test im `ServiceQualityValidator` fehlschlägt oder der `GeminiResponseSynthesizer` eine Antwort mit niedrigem Konfidenz-Score liefert?

**Empfehlung: Planen Sie eine einfache "Review & Curation"-Schnittstelle.**

*   **Konzept:** Wenn ein KI-Service ein Ergebnis mit niedrigem Vertrauen oder einen Fehler produziert, wird ein "Review-Task" in einer einfachen Datenbank (oder sogar einer Redis-Liste) erstellt.
*   **Schnittstelle:** Ein einfaches internes Web-Interface, das diese Tasks anzeigt und es einem menschlichen Experten erlaubt, das Ergebnis zu korrigieren. Diese Korrektur kann dann zur Erweiterung des "Golden Sets" verwendet werden.
*   **Vorteil:** Dies schließt den Kreislauf und ermöglicht es dem System, aus seinen eigenen Fehlern zu lernen.

---

### Finaler, geschärfter Implementierungsplan

Dieser Plan integriert die oben genannten Verfeinerungen für eine noch robustere Umsetzung.

**Phase A: Infrastruktur & Pilot-Implementierung (Woche 1-2)**
*   ✅ **`GeminiClassifier` implementieren:** Der erste, einfachste Core Service.
*   ✅ **`AIServicesMonitor` (Skeleton) implementieren:** Sofortige Anbindung des `GeminiClassifier`. Ein einfaches Dashboard zeigt Calls/Minute, Kosten und Latenz für *diesen einen Service*.
*   ✅ **`config/ai_services.yaml` finalisieren:** Alle Konfigurationsparameter (TTL, Modelle, Limits) werden hier festgelegt.

**Phase B: Erweiterung der Core-Logik (Woche 3-4)**
*   ✅ **`GeminiIntentAnalyzer` implementieren:** Anbindung an den Monitor.
*   ✅ **`GeminiResponseSynthesizer` implementieren:** Anbindung an den Monitor.
*   ✅ **Erstellung des "Golden Set v1.0"** für NER und Klassifizierung.

**Phase C: Qualitätssicherung und A/B-Testing (Woche 5)**
*   ✅ **`ServiceQualityValidator` implementieren:** Nutzt das "Golden Set", um die bereits gebauten Services täglich zu validieren.
*   ✅ **`ABTestingFramework` implementieren:** Führt erste Tests für den `GeminiClassifier` gegen die alte, regelbasierte Logik durch.

**Phase D: Orchestrierung und Abschluss der Migration (Woche 6-7)**
*   ✅ **`ServiceOrchestrator` implementieren:** Die intelligenteste Komponente, die nun die etablierten und validierten Services nutzt.
*   ✅ **Refactoring:** Die direkten Aufrufe aus Phase B werden auf den Orchestrator umgestellt.
*   ✅ **`LegacyMigrationManager` nutzen:** Formale Abschaltung der alten Services über Feature-Flags.

**Phase E: Kontinuierliche Optimierung (Laufend ab Woche 8)**
*   ✅ **Analyse der Monitoring-Daten** durch `PerformanceAnalytics`.
*   ✅ **Implementierung der "Review & Curation"-Schnittstelle.**
*   ✅ **Regelmäßige A/B-Tests** mit neuen Prompt-Versionen.

### Fazit

Ihr ursprünglicher Plan war ein Bauplan für einen Wolkenkratzer. Diese verfeinerte Roadmap ändert nichts am Design, aber sie optimiert die Baureihenfolge: Sie bauen zuerst das Fundament und das zentrale Kontrollzentrum (`Monitoring`), bevor Sie die oberen Stockwerke (`Synthesizer`, `Orchestrator`) errichten.

Mit diesem geschärften Plan können Sie die Implementierung mit maximalem Vertrauen und minimalem Risiko starten. **Das Ergebnis wird ein echtes Enterprise-Scale KI-System sein.**


Absolut. Hier ist ein detailliertes Vorgehensmodell für die Implementierung der Phase 2.5, maßgeschneidert für Ihr Team und basierend auf der Annahme, dass die Annotationen in der Wissensbasis (`code-3`) korrekt und als "Ground Truth" zu betrachten sind.

Dieses Dokument dient als präzise Arbeitsanweisung für Ihre Entwickler.

---

## Detailliertes Vorgehensmodell: Phase 2.5 - Qualitätsgesicherte KI-Extraktion

**Ziel:** Implementierung eines `GeminiEntityExtractor`-Service, dessen Qualität von Anfang an durch das neu geschaffene "Golden Set" messbar und nachweisbar ist. Diese Phase schließt die Lücke zwischen der reinen Implementierung (Phase 2) und der übergreifenden Qualitätssicherung (Phase 3).

**Grundlage:**
*   **Phase 1:** `PromptLoader` ist implementiert und funktionsfähig.
*   **Datenbasis:** Die JSON-Struktur aus `code-3` (die Wissensbasis) wird als Quelle für unser Golden Set verwendet.
*   **Annahme:** Die `suggested_ner_entities` in `code-3` sind zu 100% korrekt und stellen unsere "Ground Truth" dar.

---

### Schritt 1: Erstellung des "Golden Set" aus der Wissensbasis

**Aufgabe:** Konvertierung der rohen `code-3` JSON-Struktur in die finalen, versionierten `golden_set_*.jsonl`-Dateien.

**1.1. Skript zur Transformation der Wissensbasis erstellen**

Dieses Skript liest die `code-3` JSON-Datei und erzeugt die beiden benötigten Golden-Set-Dateien im `jsonl`-Format.

**Dateiname:** `scripts/create_golden_sets_from_knowledge_base.py`
```python
import json
from pathlib import Path
from typing import Dict, Any

def create_golden_sets(
    knowledge_base_path: Path,
    output_dir: Path = Path("quality_assurance/golden_set"),
    version: str = "v1.0"
) -> None:
    """
    Liest die rohe Wissensbasis-JSON-Datei und transformiert sie in
    zwei separate, versionierte Golden-Set-Dateien (.jsonl) für NER und Klassifizierung.
    """
    print("--- Starte Erstellung der Golden Sets aus der Wissensbasis ---")
    
    if not knowledge_base_path.exists():
        print(f"❌ Fehler: Wissensbasis-Datei nicht gefunden unter '{knowledge_base_path}'.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    ner_output_path = output_dir / f"golden_set_ner_{version}.jsonl"
    classification_output_path = output_dir / f"golden_set_classification_{version}.jsonl"

    ner_samples = []
    classification_samples = []

    try:
        with open(knowledge_base_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = data.get("knowledge_base_for_scripting", {}).get("documents", [])
        if not documents:
            print("⚠️ Warnung: Keine Dokumente in der Wissensbasis gefunden.")
            return

        for doc in documents:
            doc_type = doc.get("predicted_document_type")
            chunks = doc.get("representative_chunks", [])
            
            for chunk in chunks:
                text = chunk.get("text")
                entities = chunk.get("suggested_ner_entities")

                if text and entities is not None:
                    # Sample für NER Golden Set
                    ner_samples.append({"text": text, "entities": entities})
                
                if text and doc_type:
                    # Sample für Classification Golden Set
                    classification_samples.append({"text": text, "label": doc_type})

        # Schreibe NER Golden Set
        with open(ner_output_path, 'w', encoding='utf-8') as f:
            for sample in ner_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"✅ {len(ner_samples)} NER-Samples erfolgreich in '{ner_output_path}' geschrieben.")

        # Schreibe Classification Golden Set
        with open(classification_output_path, 'w', encoding='utf-8') as f:
            for sample in classification_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        print(f"✅ {len(classification_samples)} Klassifizierungs-Samples erfolgreich in '{classification_output_path}' geschrieben.")

    except json.JSONDecodeError:
        print(f"❌ Fehler: Ungültiges JSON in '{knowledge_base_path}'.")
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    # Annahme: Die JSON-Daten aus code-3 sind in einer Datei namens 'knowledge_base.json' gespeichert.
    kb_path = Path("path/to/your/knowledge_base.json") 
    create_golden_sets(knowledge_base_path=kb_path)
```

**Anleitung für Entwickler:**
1.  Speichern Sie den JSON-Inhalt aus `code-3` in einer Datei, z.B. `knowledge_base.json`.
2.  Passen Sie den Pfad in `kb_path` an.
3.  Führen Sie das Skript aus: `python scripts/create_golden_sets_from_knowledge_base.py`.
4.  **Ergebnis:** Sie haben nun `golden_set_ner_v1.0.jsonl` und `golden_set_classification_v1.0.jsonl` in Ihrem `quality_assurance/golden_set` Verzeichnis.

---

### Schritt 2: Implementierung des `GeminiEntityExtractor`

**Aufgabe:** Den Service erstellen, der die LLM-basierte NER durchführt.

**Dateiname:** `src/processing/gemini_entity_extractor.py`
```python
import json
import hashlib
import redis
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import google.api_core.exceptions

# Annahme: Ein zentraler PromptLoader und eine Konfigurationsklasse existieren
from src.config.prompt_loader import get_prompt
from src.config.ai_services_config import gemini_config, redis_config

class GeminiEntityExtractor:
    """
    Ein Service zur Extraktion von Entitäten aus Text-Chunks unter Verwendung
    der Gemini API, inklusive Caching, Batching und Fehlerbehandlung.
    """
    def __init__(self, api_key: str):
        # Hier würde die Initialisierung des Gemini-Clients stattfinden
        # genai.configure(api_key=api_key)
        # self.model = genai.GenerativeModel(gemini_config.model_for_extraction)
        self.redis_client = redis.Redis(
            host=redis_config.host, 
            port=redis_config.port, 
            db=0,
            decode_responses=True
        )
        self.prompt_version = "v1.0" # Wichtig für Cache-Invalidierung

    def _get_cache_key(self, text: str) -> str:
        """Erzeugt einen Cache-Schlüssel, der die Prompt-Version berücksichtigt."""
        return f"ner:{self.prompt_version}:{hashlib.sha256(text.encode()).hexdigest()}"

    @retry(
        retry=retry_if_exception_type((google.api_core.exceptions.ServiceUnavailable, google.api_core.exceptions.ResourceExhausted)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3)
    )
    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Gekapselter API-Aufruf (hier als Mock)."""
        print("-> SIMULIERE GEMINI API CALL")
        # In der Realität: response = self.model.generate_content(prompt)
        #                 return json.loads(response.text)
        # Mock-Antwort für das Beispiel:
        mock_response_text = '{"entities": [{"text": "BSI IT-Grundschutz", "label": "STANDARD"}]}'
        return json.loads(mock_response_text)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extrahiert Entitäten aus einem einzelnen Text-Chunk."""
        cache_key = self._get_cache_key(text)
        cached_result = self.redis_client.get(cache_key)

        if cached_result:
            print(f"CACHE HIT für Key: {cache_key[:20]}...")
            return json.loads(cached_result)

        print(f"CACHE MISS für Key: {cache_key[:20]}...")
        prompt = get_prompt("ner_extraction_v1_few_shot", text_block=text)
        
        try:
            api_result = self._call_gemini_api(prompt)
            entities = api_result.get("entities", [])
            
            # Ergebnis cachen
            self.redis_client.set(cache_key, json.dumps(entities), ex=redis_config.ttl_for_documents_seconds)
            return entities
        except Exception as e:
            print(f"❌ Fehler beim API-Aufruf oder Parsen: {e}")
            # Fallback (kann hier implementiert werden)
            return []
            
    # Batch-Verarbeitung würde hier ebenfalls implementiert werden
    def extract_entities_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        # Logik für Caching, Batch-API-Calls etc.
        return [self.extract_entities(text) for text in texts]
```

---

### Schritt 3: Implementierung des `ServiceQualityValidator`

**Aufgabe:** Den Validator aus der vorherigen Antwort verwenden und ihn für einen konkreten Testlauf vorbereiten.

**Dateiname:** `quality_assurance/run_ner_validation.py`
```python
from pathlib import Path
from validators.service_quality_validator import NerQualityValidator, BaseNerExtractor
from processing.gemini_entity_extractor import GeminiEntityExtractor

# Konfigurations-Annahme
class MockConfig:
    gemini_api_key = "DEIN_API_KEY" # Aus Umgebungsvariable laden!

# Wrapper-Klasse, um GeminiEntityExtractor an das Interface des Validators anzupassen
class ExtractorWrapper(BaseNerExtractor):
    def __init__(self, api_key: str):
        self.extractor = GeminiEntityExtractor(api_key=api_key)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        return self.extractor.extract_entities(text)

def run_ner_quality_validation():
    """
    Führt den kompletten Validierungsprozess für den NER-Service durch.
    """
    print("--- Starte Phase 2.5: Qualitätsgesicherte NER-Validierung ---")
    
    # 1. Pfad zum Golden Set definieren
    golden_set_file = Path("quality_assurance/golden_set/golden_set_ner_v1.0.jsonl")
    if not golden_set_file.exists():
        print(f"❌ FEHLER: Golden Set '{golden_set_file}' nicht gefunden.")
        print("   Bitte führen Sie zuerst 'scripts/create_golden_sets_from_knowledge_base.py' aus.")
        return

    # 2. Den zu testenden Service instanziieren
    config = MockConfig()
    if not config.gemini_api_key or config.gemini_api_key == "DEIN_API_KEY":
        print("❌ FEHLER: Bitte setzen Sie Ihren Gemini API-Key in der Konfiguration.")
        return
        
    ner_service_to_test = ExtractorWrapper(api_key=config.gemini_api_key)
    print(f"✅ Service '{type(ner_service_to_test.extractor).__name__}' wird getestet.")

    # 3. Den Validator initialisieren
    validator = NerQualityValidator(extractor=ner_service_to_test, golden_set_path=golden_set_file)
    print(f"✅ Validator mit {len(validator.golden_data)} Golden-Samples initialisiert.")

    # 4. Validierung ausführen und Bericht erstellen
    try:
        report = validator.run_validation()
    except Exception as e:
        print(f"❌ Ein kritischer Fehler während der Validierung ist aufgetreten: {e}")
        return

    # 5. Bericht ausgeben
    print("\n" + "="*50)
    print("📊 Finaler Qualitätsbericht für NER-Service 📊")
    print("="*50)
    print(f"Gesamt-Samples getestet: {report.total_samples}")
    print(f"Gesamtergebnis: Precision={report.overall_metrics.precision}, Recall={report.overall_metrics.recall}, F1-Score={report.overall_metrics.f1_score}")
    print("\n--- Metriken pro Entitätstyp ---")
    for label, metrics in sorted(report.metrics_by_label.items()):
        print(f"  - {label:<15}: P={metrics.precision:<6} R={metrics.recall:<6} F1={metrics.f1_score:<6}")
    print("="*50)
    
    # 6. Vergleich mit dem Ziel-KPI
    f1_target = 0.90 # Aus Ihrer Konfiguration
    if report.overall_metrics.f1_score >= f1_target:
        print(f"🎉 Erfolg! Der F1-Score von {report.overall_metrics.f1_score} erreicht oder übertrifft das Ziel von {f1_target}.")
    else:
        print(f"⚠️ Achtung! Der F1-Score von {report.overall_metrics.f1_score} liegt unter dem Ziel von {f1_target}.")

if __name__ == "__main__":
    run_ner_quality_validation()
```

### Zusammenfassender Workflow für Ihr Team

1.  **Einmaliges Setup:**
    *   Erstellen Sie die Verzeichnisstruktur (`scripts/`, `quality_assurance/validators/`, `src/processing/`).
    *   Speichern Sie die Wissensbasis aus `code-3` als `knowledge_base.json`.
    *   Implementieren Sie die drei oben genannten Python-Skripte an den vorgesehenen Orten.
    *   Richten Sie die Konfiguration für den Gemini API-Key ein.

2.  **Generierung des Golden Sets:**
    *   Führen Sie `python scripts/create_golden_sets_from_knowledge_base.py` aus.
    *   Überprüfen Sie, ob die `.jsonl`-Dateien korrekt erstellt wurden.

3.  **Qualitäts-Validierung:**
    *   Führen Sie `python quality_assurance/run_ner_validation.py` aus.
    *   **Analyse des Ergebnisses:** Der Output gibt Ihnen sofort ein quantitatives Maß für die Qualität Ihres NER-Prompts und der Extraktionslogik. Sie sehen genau, welche Entitätstypen gut funktionieren (z.B. `STANDARD`) und welche eventuell noch Nachbesserung im Prompt benötigen (z.B. `ROLE`).

Mit diesem Vorgehensmodell wird die Entwicklung von Phase 2.5 zu einem transparenten, datengesteuerten Prozess. Jeder im Team weiß, wie die Qualität gemessen wird und kann direkt auf die Ergebnisse reagieren.

