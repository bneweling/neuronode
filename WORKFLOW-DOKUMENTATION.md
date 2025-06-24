# KI-Wissenssystem: Vollständiger Workflow-Guide

## Übersicht: Vom Dokument zum Wissensgraph

Dieser Guide zeigt den kompletten Workflow von der Dokumentenerkennung bis zur interaktiven Visualisierung im Obsidian Plugin.

## 🔄 Workflow-Übersicht

```mermaid
graph TD
    A[Dokument Upload] → B[Dateityp-Erkennung]
    B → C[Dokumentklassifizierung]
    C → D{Strukturiertes Dokument?}
    D →|Ja| E[Control-Extraktion]
    D →|Nein| F[Chunk-Verarbeitung]
    E → G[Qualitätsprüfung]
    G → H[Neo4j Speicherung]
    F → H
    H → I[ChromaDB Vektorisierung]
    I → J[Beziehungsanalyse]
    J → K[Graph-Gardening]
    K → L[Plugin-Visualisierung]
    L → M[Benutzer-Feedback]
```

## 📋 Phase 1: Dokumentenupload und Erkennung

### 1.1 Upload-Prozess
```bash
# CLI Upload
./ki-cli.sh process dokument.pdf

# API Upload
curl -X POST "http://localhost:8080/documents/upload" \
  -F "file=@dokument.pdf" \
  -F "validate=true"
```

### 1.2 Automatische Dateityp-Erkennung
**Ort:** `src/document_processing/document_processor.py`

```python
def _detect_file_type(self, file_path: Path) -> FileType:
    """Automatische Erkennung basierend auf Dateiendung"""
    extension = file_path.suffix.lower().lstrip('.')
    mapping = {
        'pdf': FileType.PDF,
        'docx': FileType.DOCX,
        'xlsx': FileType.XLSX,
        'pptx': FileType.PPTX,
        'txt': FileType.TXT,
        'xml': FileType.XML
    }
    return mapping.get(extension, FileType.TXT)
```

**Erkannte Dateitypen:**
- ✅ PDF (via PyPDF2)
- ✅ Word-Dokumente (via python-docx)
- ✅ Excel-Tabellen (via openpyxl)
- ✅ PowerPoint (via python-pptx)
- ✅ Text-Dateien
- ✅ XML-Dateien

### 1.3 Dokumentklassifizierung
**Ort:** `src/document_processing/classifier.py`

Das System erkennt automatisch:
- **BSI IT-Grundschutz** Dokumente
- **BSI C5** Cloud Compliance
- **ISO 27001** Standards
- **NIST CSF** Framework
- **Whitepaper** von Herstellern
- **Technische Dokumentation**
- **FAQ** Dokumente

**Erkennungslogik:**
1. **Regel-basiert:** Suche nach charakteristischen Begriffen
2. **LLM-basiert:** Intelligente Klassifizierung unklarer Fälle

```python
# Beispiel der automatischen Erkennung
if "IT-Grundschutz" in sample_text:
    return DocumentType.BSI_GRUNDSCHUTZ
elif "Cloud Computing Compliance" in sample_text:
    return DocumentType.BSI_C5
# ... weitere Regeln
else:
    # LLM-Klassifizierung für unklare Fälle
    response = self.llm.invoke(classification_prompt)
```

## 📊 Phase 2: Intelligente Verarbeitung

### 2.1 Strukturierte Dokumente (Compliance-Standards)

**Für BSI, ISO, NIST Dokumente:**

1. **Control-Extraktion**
   ```python
   controls = await self.structured_extractor.extract_controls(
       content["full_text"],
       document_type,
       source
   )
   ```

2. **Qualitätsprüfung**
   ```python
   if validate:
       validated_controls, reports = await self.validator.validate_controls(
           controls, document_type.value
       )
   ```

3. **Chunk-Erstellung für Vektorsuche**
   ```python
   chunks = await self.unstructured_processor.process_document(
       content["full_text"], source, document_type.value
   )
   ```

### 2.2 Unstrukturierte Dokumente

**Für Whitepaper, Technische Docs:**

1. **Intelligente Segmentierung**
   ```python
   chunks = await self.unstructured_processor.process_document(
       content["full_text"], source, document_type.value
   )
   ```

2. **Entitäts-Extraktion**
   - Technologien (z.B. "Microsoft Azure", "Kubernetes")
   - Personen und Organisationen
   - Konzepte und Schlüsselbegriffe

3. **Beziehungsanalyse**
   ```python
   analysis = self._analyze_chunk(chunk_text)
   # Ergebnis: Zusammenfassung, Keywords, Entitäten, Beziehungen
   ```

## 🗄️ Phase 3: Datenspeicherung und Verknüpfung

### 3.1 Neo4j Knowledge Graph
**Ort:** `src/storage/neo4j_client.py`

**Gespeicherte Entitäten:**
- **ControlItem:** Compliance-Controls mit Metadaten
- **KnowledgeChunk:** Textblöcke mit Kontext
- **Technology:** Erkannte Technologien
- **Entity:** Personen, Organisationen, Konzepte

**Beziehungstypen:**
- `IMPLEMENTS` - Technologie implementiert Control
- `SUPPORTS` - Dokument unterstützt Control
- `REFERENCES` - Verweis zwischen Dokumenten
- `MAPS_TO` - Mapping zwischen Standards
- `MENTIONS` - Erwähnung von Entitäten

### 3.2 ChromaDB Vektorspeicher
**Ort:** `src/storage/chroma_client.py`

**Collections:**
- `compliance` - Compliance-bezogene Inhalte
- `technical` - Technische Dokumentation

```python
# Vektorisierung für semantische Suche
await self.chroma.add_chunk(
    chunk.dict(),
    collection_name
)
```

## 🔍 Phase 4: Transparente Beziehungsanalyse

### 4.1 Automatische Verbindungserkennung

**Graph Gardener** (`src/orchestration/graph_gardener.py`) überwacht kontinuierlich:

1. **Orphan-Knoten finden**
   ```python
   orphans = self.neo4j.get_orphan_nodes(min_connections=2)
   ```

2. **Ähnlichkeitsbasierte Verbindungen**
   ```python
   similar_chunks = self.chroma.search_similar(
       search_query, n_results=10
   )
   ```

3. **LLM-basierte Beziehungsvalidierung**
   ```python
   relationship = await self._validate_relationship(
       source_text, target_text
   )
   # Ergebnis: IMPLEMENTS, SUPPORTS, REFERENCES, CONFLICTS, NONE
   ```

### 4.2 Cross-Standard Mappings

**Automatische Erkennung von Mappings zwischen Standards:**
```python
# Beispiel: BSI Grundschutz ↔ ISO 27001
result = session.run("""
    MATCH (c1:ControlItem)-[:MAPS_TO]->(c2:ControlItem)
    WHERE c1.source CONTAINS 'BSI' AND c2.source CONTAINS 'ISO'
    RETURN c1, c2
""")
```

## 🎯 Phase 5: Plugin-Integration und Visualisierung

### 5.1 Obsidian Plugin Architecture

**Hauptkomponenten:**
- `DocumentUploadView` - **NEU**: Transparenter Upload mit Echtzeit-Analyse
- `KnowledgeChatView` - Chat-Interface mit Kontext
- `KnowledgeGraphView` - Graph-Visualisierung
- `DocumentUploadInterface` - **NEU**: Drag & Drop Upload-Komponente
- `GraphVisualization` - D3.js-basierte Darstellung
- `ApiClient` - Erweiterte Backend-Kommunikation

### 5.1.1 Neue Upload-Features

**Transparenter Upload-Workflow:**
```typescript
// Echtzeit-Analyse vor Upload
const analysisResult = await this.apiClient.analyzeDocumentPreview(file);
this.showAnalysisResults(analysisResult);

// Upload mit Fortschrittsanzeige
const uploadResult = await this.apiClient.uploadDocumentWithProgress(
    file, 
    (progress) => this.updateProgressBar(progress)
);
```

**Plugin-Zugriff:**
- **Ribbon-Icons**: 📤 Upload, 💬 Chat, 🕸️ Graph
- **Command Palette**: Strg+P/Cmd+P → "Open Document Upload/Chat/Graph"
- **Hotkeys**: Konfigurierbare Tastenkombinationen

### 5.2 Echtzeitvisualisierung

**Chat-Integration:**
```typescript
// Bei jeder Antwort wird der Kontext-Graph aktualisiert
private async updateContextGraph(response: any) {
    const nodeIds = this.extractNodeIds(response);
    const graphData = await this.plugin.apiClient.getGraphContext(
        nodeIds, this.plugin.settings.graphDepth
    );
    this.graphViz.updateGraph(graphData.nodes, graphData.edges, nodeIds);
}
```

**Graph-Interaktionen:**
- **Klick auf Knoten:** Zeigt Details und verwandte Knoten
- **Hover:** Tooltip mit Metadaten
- **Zoom/Pan:** Navigation im Graph
- **Filter:** Nach Knotentyp, Beziehungstyp, Quelle

## 📈 Phase 6: Kontinuierliche Verbesserung

### 6.1 Monitoring und Metriken
**Ort:** `src/monitoring/metrics.py`

**Überwachte Metriken:**
- Verarbeitungszeiten pro Dokumenttyp
- Qualitätsbewertungen der Extraktion
- Beziehungsgenauigkeit
- Benutzerinteraktionen

### 6.2 Feedback-Integration

**Benutzer-Feedback wird verwendet für:**
- Verbesserung der Klassifizierung
- Korrektur von Beziehungen
- Anpassung der Extraktionslogik

## 🔧 Praktische Anwendung

### Workflow für neues Dokument:

1. **Upload starten:**
   ```bash
   ./ki-cli.sh process "BSI_Grundschutz_Kompendium.pdf"
   ```

2. **Verarbeitung verfolgen:**
   ```bash
   # Echtzeit-Logs
   tail -f logs/processing.log
   
   # Status abfragen
   ./ki-cli.sh stats
   ```

3. **Ergebnisse inspizieren:**
   ```bash
   # Control-Details anzeigen
   ./ki-cli.sh show-control "OPS.1.1.2"
   
   # Graph-Statistiken
   ./ki-cli.sh stats
   ```

4. **Plugin-Visualisierung:**
   - Öffne Obsidian
   - Aktiviere "Knowledge Graph" View
   - Stelle Frage im Chat: "Zeige mir OPS.1.1.2 Implementierungen"
   - Graph wird automatisch mit relevanten Knoten aktualisiert

### Transparenz-Features:

**Im Plugin sichtbar:**
- ✅ Dokumenttyp-Klassifizierung mit Konfidenz
- ✅ Extrahierte Controls mit Qualitätsbewertung
- ✅ Erkannte Beziehungen mit Begründung
- ✅ Ähnlichkeits-Scores bei Suchen
- ✅ Quellenangaben für alle Informationen

**Beispiel Chat-Antwort:**
```
Gefunden: 3 relevante Controls für "Patch Management"

🎯 OPS.1.1.3 - Patch- und Änderungsmanagement
   Quelle: BSI IT-Grundschutz (Seite 247)
   Beziehung: IMPLEMENTS → Microsoft WSUS (Konfidenz: 0.89)
   
🔗 Verwandte Standards:
   • ISO 27001 A.12.6.1 (Mapping-Konfidenz: 0.94)
   • NIST CSF PR.IP-12 (Ähnlichkeit: 0.87)

📊 Implementierungen gefunden:
   • 5 Technische Dokumente
   • 12 Whitepaper
   • 3 FAQ-Einträge
```

## 🚀 Erweiterte Features

### Hot Reload für Entwicklung:
```bash
# Backend Hot Reload
./dev-mode.sh
# Option 1: Backend Hot Reload

# Plugin Hot Reload
cd ../obsidian-ki-plugin
npm run dev
# Dann Cmd+R in Obsidian
```

### Batch-Verarbeitung:
```bash
./ki-cli.sh batch ./documents/ --pattern "*.pdf" --max-concurrent 3
```

### API-Integration:
```bash
# Dokument via API hochladen
curl -X POST "http://localhost:8080/documents/upload" \
  -F "file=@dokument.pdf" \
  -F "force_type=BSI_GRUNDSCHUTZ" \
  -F "validate=true"

# Graph durchsuchen
curl "http://localhost:8080/knowledge-graph/search?query=Patch%20Management&node_type=ControlItem"
```

Dieser Workflow stellt sicher, dass jeder Schritt transparent und nachvollziehbar ist - von der automatischen Dokumentenerkennung bis zur interaktiven Visualisierung im Plugin. 