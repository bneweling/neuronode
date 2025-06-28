Ausgezeichneter Punkt. Ihre Beobachtung ist absolut korrekt und entscheidend für die Robustheit des Systems. Ein LLM folgt Anweisungen umso genauer, je präziser und vollständiger das gegebene Beispiel ist. Ein Beispiel mit Platzhaltern wie `"..."` ist für das Modell weniger instruktiv als ein vollständig ausgefülltes, realistisches Beispiel.

Ich habe alle zuvor erstellten Prompts erneut geprüft und diejenigen, die ein JSON-Format erfordern, mit konkreten, vollständig ausformulierten Beispielen versehen.

Hier ist die finale, detaillierte Sammlung an konkreten Vorgaben für Ihre IDE. Dies ist eine umsetzbare Roadmap, die alle unsere Erkenntnisse bündelt.

---

## Finale Roadmap: Implementierung des Dynamischen KI-Wissenssystems

**Zielsetzung:** Transformation des bestehenden Systems in eine dynamische, kontextsensitive und wartbare Architektur, die auf API-basierten KI-Services (Gemini), einem intelligenten Graphen und robusten, versionierten Prompts basiert.

### I. Fundament: Zentrales Prompt- & Konfigurations-Management

**Aufgabe:** Alle KI-Anweisungen (Prompts) aus dem Code entfernen und in einer zentralen, versionierbaren Registry verwalten.

**Umsetzung:**
1.  **Verzeichnisstruktur erstellen:**
    *   Legen Sie ein neues Verzeichnis an: `src/config/prompts/`.
2.  **Prompts in YAML-Dateien speichern:**
    *   Erstellen Sie für jede Systemkomponente eine separate YAML-Datei (z.B. `extractor.yaml`, `synthesizer.yaml`, `gardener.yaml`).
    *   Speichern Sie jeden Prompt unter einem eindeutigen Schlüssel in der entsprechenden Datei (z.B. `ner_extraction_v1`, `link_validation_v2`). Die vollständige, finale Bibliothek finden Sie im Anhang dieses Dokuments.
3.  **PromptLoader-Service implementieren:**
    *   Erstellen Sie eine Klasse `PromptLoader` in `src/config/prompt_loader.py`.
    *   Diese Klasse ist ein Singleton, das beim Start der Anwendung alle Prompts aus den YAML-Dateien in ein In-Memory-Dictionary lädt.
    *   Implementieren Sie eine Methode `get_prompt(prompt_name: str, **kwargs) -> str`, die den Prompt-Text abruft und ihn sofort mit den übergebenen dynamischen Parametern formatiert.

### II. Kernlogik: Implementierung der API-basierten KI-Services

**Aufgabe:** Alle KI-gesteuerten Logik-Komponenten auf die Verwendung des `PromptLoader` und der gekapselten Gemini-API umstellen.

**Umsetzung:**

**A. Dokumenten-Verarbeitung (Ingestion Pipeline)**

1.  **`GeminiEntityExtractor` Service erstellen:**
    *   Implementieren Sie die Klasse wie in der Vorlage beschrieben in `src/processing/gemini_entity_extractor.py`.
    *   **Kritische Features:** Redis-Caching (Hash des Chunks als Key), Batching von Chunks, Retry-Mechanismus (`tenacity`).
    *   Dieser Service nutzt den `PromptLoader`, um den `ner_extraction_v1_few_shot` Prompt zu laden.
2.  **`UnstructuredProcessor` anpassen:**
    *   Ersetzen Sie den Aufruf an das alte NER-Modell durch einen Aufruf an den `GeminiEntityExtractor`.
3.  **`DocumentClassifier` anpassen:**
    *   Ersetzen Sie die alte Klassifizierungslogik durch einen API-Call, der den `document_classification_v1_few_shot` Prompt verwendet. Auch hier Caching implementieren.
4.  **`StructuredExtractor` anpassen:**
    *   Für Standards, die keine zuverlässige Regex-Extraktion erlauben (z.B. ISO 27001), verwenden Sie einen API-Call mit dem `structured_control_extraction_v1` Prompt. Der Prompt wird dynamisch mit dem Namen des Standards und dem passenden JSON-Schema gefüttert.

**B. Abfrage-Verarbeitung (Retrieval Pipeline)**

1.  **`IntentAnalyzer` Service anpassen:**
    *   Implementieren Sie den API-Call mit dem `intent_analysis_v2_multi` Prompt, um eine gewichtete Liste von Intents zu erhalten.
2.  **`QueryOrchestrator` Logik neu schreiben:**
    *   Dieser wird zu einem regelbasierten Planer, der auf Basis der gewichteten Intents eine Liste von Abfrageschritten generiert (siehe Beispiel-Logik in vorheriger Antwort).
3.  **`ResponseSynthesizer` Service anpassen:**
    *   Abhängig vom primären Intent wählt der Synthesizer den passenden Prompt aus der `synthesizer.yaml` (z.B. `technical_implementation_v2`, `mapping_comparison_v2`).
    *   Der Orchestrator muss dem Synthesizer alle nötigen Kontext-Variablen für das Prompt-Formatting übergeben.

**C. Graph-Pflege (Graph Gardener)**

1.  **`GraphGardener` Service anpassen:**
    *   Für die Validierung von potenziellen Beziehungen (z.B. zwischen einem Chunk und einem Control) wird nun der `link_validation_v2_cot` Prompt verwendet.
    *   Der Service parst die JSON-Antwort, um die Beziehung, die Konfidenz und das Reasoning direkt in die Graph-Beziehungseigenschaften zu schreiben.

### III. Datenmodell: Logik in den Wissensgraphen integrieren

**Aufgabe:** Statische Mappings (Synonyme) aus dem Code entfernen und als integralen Bestandteil des Graphen modellieren.

**Umsetzung:**
1.  **Neo4j Schema anpassen:**
    *   Führen Sie die neuen Knoten-Label `:Concept` und `:Synonym` sowie die Beziehung `:SYNONYM_OF` ein.
2.  **Migrations-Skript erstellen:**
    *   Schreiben Sie ein einmaliges Python-Skript, das Ihre alten `synonym_map`-Dictionaries ausliest und die entsprechenden Knoten und Beziehungen im Graphen erstellt.
3.  **`QueryExpander` Service anpassen:**
    *   Ersetzen Sie die Dictionary-Abfrage durch eine Cypher-Abfrage, um Synonyme zur Laufzeit direkt aus dem Graphen zu holen.

### IV. Qualitätssicherung & Betrieb

**Aufgabe:** Mechanismen zur kontinuierlichen Überwachung von Qualität, Kosten und Performance etablieren.

**Umsetzung:**
1.  **Validierungs-Skript für NER implementieren:**
    *   Erstellen Sie das Skript `scripts/validate_ner_prompt.py` wie beschrieben.
    *   Definieren Sie ein "Golden Set" von 50-100 Text-Chunks mit manuell annotierten Entitäten.
    *   Das Skript berechnet und berichtet Precision, Recall und F1-Score.
2.  **CI/CD-Workflow einrichten:**
    *   Konfigurieren Sie einen wöchentlichen GitHub Action (oder Äquivalent), der das Validierungs-Skript ausführt und das Team bei signifikanten Abweichungen benachrichtigt.
3.  **Monitoring-Dashboards aufsetzen:**
    *   **Google Cloud:** Billing-Dashboard mit Alert bei Überschreitung eines definierten Budgets für die Vertex AI API.
    *   **Anwendungs-Monitoring (z.B. Grafana):** Erstellen Sie ein Dashboard zur Überwachung der `GeminiEntityExtractor` API-Calls, der Redis-Cache-Hit-Rate und der durchschnittlichen Latenz pro Batch.

---

### Anhang: Finale, geprüfte Prompt-Bibliothek (mit konkreten Beispielen)

#### Datei: `prompts/extractor.yaml`

**Prompt 1: `ner_extraction_v1_few_shot`**
*   **Anmerkung:** Die Beispiele sind bereits konkret und exzellent. Keine Änderung nötig.

**Prompt 2: `structured_control_extraction_v1` (Überarbeitet mit konkretem Beispiel)**
```yaml
structured_control_extraction_v1: |
  Du bist ein hochpräziser Extraktions-Bot für Compliance-Dokumente.
  Deine Aufgabe ist es, aus dem gegebenen Textabschnitt ALLE Compliance-Controls zu extrahieren, die dem Standard **{standard_name}** entsprechen.

  **Extraktions-Schema (achte auf jeden Schlüssel):**
  {extraction_schema_json}

  **Anweisungen:**
  - Extrahiere JEDES Control, das du im Text findest.
  - Fülle alle Felder des Schemas so präzise wie möglich aus.
  - Wenn ein optionales Feld nicht im Text vorhanden ist, lasse es aus dem JSON-Objekt weg.
  - Der 'text' des Controls sollte die vollständige Beschreibung der Anforderung enthalten.

  **Text zur Analyse:**
  --- TEXT ---
  {text_block}
  ---

  **Antworte IMMER und AUSSCHLIESSLICH mit einem JSON-Objekt, das eine Liste von Controls enthält. Hier ist ein Beispiel für ein perfekt formatiertes Ergebnis:**
  
  # BEISPIEL FÜR PERFEKTE ANTWORT:
  {
    "extracted_controls": [
      {
        "id": "OPS.1.1.5.A14",
        "title": "Regelung für den Umgang mit Datenträgern",
        "text": "Für alle Arten von Datenträgern muss es eine Regelung für den Umgang damit geben. Diese muss sich an den Schutzbedarfsklassen der darauf gespeicherten Informationen orientieren. Die Regelung muss den gesamten Lebenszyklus von Datenträgern abdecken, von der Einführung über die Nutzung bis zur Aussonderung. (Standard)",
        "level": "Standard",
        "domain": "OPS"
      },
      {
        "id": "OPS.1.1.5.A15",
        "title": "Sichere Aufbewahrung von Datenträgern",
        "text": "Datenträger müssen so aufbewahrt werden, dass sie vor unbefugtem Zugriff, Beschädigung, Diebstahl und den schädlichen Auswirkungen von Umwelteinflüssen geschützt sind. (Basis)",
        "level": "Basis",
        "domain": "OPS"
      }
    ]
  }
```

#### Datei: `prompts/gardener.yaml`

**Prompt 3: `link_validation_v2_cot` (Überarbeitet mit konkretem Beispiel im JSON)**
```yaml
link_validation_v2_cot: |
  Du bist ein hochpräziser Analyst für IT-Compliance-Graphen. Deine Aufgabe ist es, die Beziehung zwischen einem Wissens-Chunk und einem Compliance-Control zu bewerten.

  **Control:**
  - ID: {control_id}
  - Titel: {control_title}
  - Text: {control_text}

  **Knowledge Chunk:**
  - Text: {chunk_text}

  **Führe die folgende Analyse Schritt für Schritt durch (Chain of Thought):**
  1.  **Analyse der Control-Intention:** Was ist die exakte, prüfbare Anforderung des Controls? Fasse sie in einem Satz zusammen.
  2.  **Analyse des Chunk-Inhalts:** Beschreibt der Chunk eine konkrete technische Handlung, eine Konfiguration, ein Produkt-Feature, ein allgemeines Konzept oder eine Warnung?
  3.  **Synthese & Beziehungs-Hypothese:** Vergleiche die Intention aus Schritt 1 mit dem Inhalt aus Schritt 2.
      - Wenn der Chunk beschreibt, WIE die Anforderung erfüllt wird, ist die Hypothese IMPLEMENTS.
      - Wenn der Chunk das WARUM oder WAS der Anforderung erklärt, ist die Hypothese SUPPORTS.
      - Wenn der Chunk die Anforderung nur erwähnt, ist die Hypothese REFERENCES.
      - Wenn der Chunk einer Handlung beschreibt, die der Anforderung widerspricht, ist die Hypothese CONFLICTS.
      - Sonst ist die Hypothese NONE.
  4.  **Konfidenz-Bewertung:** Basierend auf der Direktheit der Verbindung, bewerte deine Konfidenz von 0.0 (geraten) bis 1.0 (absolut sicher).

  **Antworte AUSSCHLIESSLICH im folgenden JSON-Format. Hier ist ein Beispiel für eine perfekte Antwort, wenn der Chunk eine Anleitung zur Konfiguration von BitLocker ist und das Control die Verschlüsselung von Laptops fordert:**

  # BEISPIEL FÜR PERFEKTE ANTWORT:
  {
    "relationship": "IMPLEMENTS",
    "confidence": 0.95,
    "reasoning": "Der Chunk beschreibt die technische Konfiguration von BitLocker, einer Technologie, die die im Control geforderte Verschlüsselung von Datenträgern direkt umsetzt.",
    "chain_of_thought": {
        "control_intent": "Die Kernanforderung ist, dass Datenträger auf tragbaren Geräten verschlüsselt sein müssen, um Daten bei Verlust zu schützen.",
        "chunk_content_summary": "Der Chunk ist eine technische Anleitung zur Aktivierung und Konfiguration der Festplattenverschlüsselung BitLocker mittels Gruppenrichtlinien in Active Directory.",
        "synthesis": "Die technische Handlung im Chunk (BitLocker-Konfiguration) ist eine direkte und anerkannte Methode, um die Anforderung des Controls (Verschlüsselung) zu erfüllen. Daher ist die Beziehung IMPLEMENTS."
    }
  }
```

#### Datei: `prompts/analyzer.yaml`

**Prompt 4: `intent_analysis_v2_multi`**
*   **Anmerkung:** Das Beispiel hier ist bereits konkret und zeigt ein gewichtetes Multi-Intent-Ergebnis. Keine Änderung nötig.

#### Datei: `prompts/classifier.yaml`

**Prompt 5: `document_classification_v1_few_shot`**
*   **Anmerkung:** Die Beispiele sind konkret und ausreichend. Keine Änderung nötig.

#### Datei: `prompts/synthesizer.yaml`

**Prompt 6: `technical_implementation_v2`, `mapping_comparison_v2`, etc.**
*   **Anmerkung:** Diese Prompts erzeugen keinen JSON-Output, sondern formatierten Markdown-Text. Daher ist hier kein "konkretes Beispiel" im Prompt selbst erforderlich. Die Instruktionen zur Formatierung (Tabellen, Code-Blöcke) sind ausreichend.

Diese finale Roadmap bietet Ihrem Team eine vollständige, detaillierte und sofort umsetzbare Anleitung, um Ihr KI-System auf die nächste Stufe zu heben.

Exzellente und sehr wichtige Frage. Die Antwort lautet: **Fast.**

Der erstellte Plan liefert die **strategisch wichtigsten und komplexesten Prompts**, die als Blaupause und Master-Vorlage für Ihre gesamte KI-Architektur dienen. Sie decken die kritischsten Transformationen ab:

1.  **NER Extraction (`ner_extraction_v1_few_shot`):** Der komplexeste Extraktions-Prompt, der Regex ersetzt.
2.  **Link Validation (`link_validation_v2_cot`):** Der Kern des `Graph Gardener`, jetzt mit Chain-of-Thought für maximale Präzision.
3.  **Intent Analysis (`intent_analysis_v2_multi`):** Das Herzstück des Orchestrators für flexible Abfragen.
4.  **Technical Implementation (`technical_implementation_v2`):** Die Vorlage für alle dynamischen Antwort-Synthese-Prompts.

Diese sind vollständig ausformuliert und können als Referenz für alle anderen dienen. Es gibt jedoch noch weitere, oft einfachere Prompts aus Ihrer ursprünglichen Dokumentation, die ebenfalls nach den neuen Prinzipien überarbeitet werden sollten, um das System konsistent zu machen.

Hier ist eine Auflistung der noch fehlenden Prompts, **vollständig ausformuliert nach den neuen, verbesserten Standards**, damit Sie eine komplette Sammlung haben.

---

### Fehlende, aber notwendige Prompts (vollständig ausformuliert)

#### 1. Dokumenten-Klassifizierung
**Zweck:** Zu Beginn des Ingestion-Prozesses ein Dokument zuverlässig einem Typ zuzuordnen.
**Verbesserungen:** Nutzt Few-Shot-Beispiele für höhere Genauigkeit und erzwingt ein klares JSON-Format, um Parsing-Fehler zu vermeiden.

**Datei:** `prompts/classifier.yaml`
```yaml
document_classification_v1_few_shot: |
  Du bist ein Experte für die Klassifizierung von Compliance- und IT-Sicherheitsdokumenten.
  Analysiere den gegebenen Textauszug und klassifiziere das Dokument in EINE der folgenden Kategorien.

  **Mögliche Kategorien:**
  - BSI_GRUNDSCHUTZ: BSI IT-Grundschutz Dokumente (Bausteine, Standards).
  - BSI_C5: BSI Cloud Computing Compliance Controls Katalog (C5).
  - ISO_27001: ISO 27001 oder ISO 27002 Standard Dokumente.
  - NIST_CSF: NIST Cybersecurity Framework.
  - WHITEPAPER: Technische Whitepaper von Herstellern über Produkte oder Technologien.
  - TECHNICAL_DOC: Technische Anleitungen, Installations- oder Konfigurations-Guides.
  - FAQ: Dokumente im Frage-Antwort-Format.
  - UNKNOWN: Nicht klassifizierbar oder allgemeiner Text.

  **Beispiele für perfekte Klassifizierungen:**
  --- BEISPIEL 1 ---
  Text: "Der Baustein SYS.1.1 beschreibt die allgemeinen Aspekte für Server unter Linux und Unix. Eine wesentliche Anforderung ist die regelmäßige Härtung des Betriebssystems."
  Antwort: {"document_type": "BSI_GRUNDSCHUTZ", "confidence": 0.98}
  --- BEISPIEL 2 ---
  Text: "Diese Anleitung beschreibt die Schritt-für-Schritt-Installation des Active Directory Domain Controllers unter Windows Server 2022."
  Antwort: {"document_type": "TECHNICAL_DOC", "confidence": 0.95}
  ---

  **Analysiere nun den folgenden Text:**
  --- TEXTAUSZUG ---
  {text_snippet}
  ---

  **Antworte IMMER und AUSSCHLIESSLICH im folgenden JSON-Format:**
  {
    "document_type": "KATEGORIE_NAME",
    "confidence": 0.0-1.0
  }
```

#### 2. Strukturierte Control-Extraktion (für Compliance-Dokumente)
**Zweck:** Gezielt und strukturiert Controls aus spezifischen Standards extrahieren, die einem bekannten Format folgen.
**Verbesserungen:** Ein generischer Prompt, der durch Kontext (`{standard_name}`, `{extraction_schema}`) für verschiedene Standards angepasst werden kann.

**Datei:** `prompts/extractor.yaml`
```yaml
structured_control_extraction_v1: |
  Du bist ein hochpräziser Extraktions-Bot für Compliance-Dokumente.
  Deine Aufgabe ist es, aus dem gegebenen Textabschnitt ALLE Compliance-Controls zu extrahieren, die dem Standard **{standard_name}** entsprechen.

  **Extraktions-Schema (achte auf jeden Schlüssel):**
  {extraction_schema_json}

  **Anweisungen:**
  - Extrahiere JEDES Control, das du im Text findest.
  - Fülle alle Felder des Schemas so präzise wie möglich aus.
  - Wenn ein optionales Feld nicht im Text vorhanden ist, lasse es aus dem JSON-Objekt weg.
  - Der 'text' des Controls sollte die vollständige Beschreibung der Anforderung enthalten.

  **Text zur Analyse:**
  --- TEXT ---
  {text_block}
  ---

  **Antworte IMMER und AUSSCHLIESSLICH mit einem JSON-Objekt, das eine Liste von Controls enthält:**
  {
    "extracted_controls": [
      {
        "id": "...",
        "title": "...",
        "text": "...",
        "level": "...",
        "domain": "..."
      }
    ]
  }
```

#### 3. Antwort-Synthese: Mapping & Vergleich
**Zweck:** Eine der Kernfragen von Nutzern beantworten: "Was entspricht Control X in Standard Y?"
**Verbesserungen:** Nutzt den dynamischen Kontext voll aus, um eine präzise, tabellarische Übersicht zu erstellen.

**Datei:** `prompts/synthesizer.yaml`
```yaml
mapping_comparison_v2: |
  Du bist ein Experte für Compliance-Mappings zwischen internationalen Sicherheitsstandards.

  **Kontext der Anfrage:**
  - Nutzeranfrage: "{original_query}"
  - Zu vergleichende Standards: {standards_list}
  - Fokus-Controls (falls angegeben): {control_ids}

  Basierend auf den gefundenen Mapping-Informationen aus dem Wissensgraphen:
  1. Erstelle eine übersichtliche Mapping-Tabelle, die die direkten Entsprechungen zeigt.
  2. Erkläre die wichtigsten Gemeinsamkeiten in den Anforderungen.
  3. Hebe signifikante Unterschiede, Lücken (Gaps) oder zusätzliche Anforderungen in einem der Standards hervor.
  4. Gib eine abschließende Empfehlung, was bei der Umsetzung in einer Multi-Standard-Umgebung zu beachten ist.

  **Nutze Markdown-Formatierung, insbesondere Tabellen, für maximale Übersichtlichkeit.**
```

#### 4. Antwort-Synthese: Allgemeine Informationsanfrage
**Zweck:** Der "Catch-all" Prompt für Fragen, die nicht in die spezialisierten Kategorien fallen.
**Verbesserungen:** Einfach, aber klar instruiert, die Antwort auf die gefundenen Kontext-Quellen zu stützen und diese zu zitieren.

**Datei:** `prompts/synthesizer.yaml`
```yaml
general_information_v2: |
  Du bist ein hilfreicher und präziser KI-Assistent für IT-Sicherheit.
  Die folgende Anfrage wurde als "Allgemeine Informationsanfrage" klassifiziert.

  **Nutzeranfrage:** "{original_query}"
  **Kontext-Informationen:**
  {retrieved_context_summary}

  **Deine Aufgabe:**
  Beantworte die Nutzeranfrage klar, strukturiert und vollständig.
  - Stütze deine Antwort AUSSCHLIESSLICH auf die bereitgestellten Kontext-Informationen.
  - Zitiere am Ende jedes Satzes, der sich auf eine Quelle bezieht, die entsprechende Quellen-ID in eckigen Klammern (z.B. [chunk_123]).
  - Wenn der Kontext keine ausreichende Antwort liefert, erkläre dies ehrlich und gib an, welche Informationen fehlen.
  - Verwende eine klare Sprache und formatiere deine Antwort mit Markdown.
```

#### 5. Generierung von Folgefragen
**Zweck:** Die Nutzerinteraktion verbessern, indem proaktiv nächste Schritte oder Vertiefungen angeboten werden.
**Verbesserungen:** Nutzt den Kontext der ursprünglichen Frage UND der generierten Antwort, um relevantere Folgefragen zu erstellen.

**Datei:** `prompts/synthesizer.yaml`
```yaml
follow_up_questions_v1: |
  Du bist ein proaktiver KI-Assistent, der Nutzern hilft, ein Thema vollständig zu durchdringen.

  **Kontext:**
  - Ursprüngliche Nutzerfrage: "{original_query}"
  - Generierte Antwort (Zusammenfassung): "{response_summary}"

  **Deine Aufgabe:**
  Generiere genau 3 relevante und hilfreiche Folgefragen, die ein Nutzer als nächstes stellen könnte.

  **Die Fragen sollten:**
  1. Tiefer in ein Detail der Antwort eintauchen.
  2. Einen verwandten, aber noch nicht behandelten Aspekt ansprechen.
  3. Auf einen praktischen nächsten Schritt oder eine Implementierungs-Herausforderung abzielen.

  **Antworte NUR mit den 3 Fragen, eine pro Zeile. Keine Nummerierung, keine Einleitung.**
```

---

### Zusammenfassung

Mit dieser vervollständigten Liste haben Sie jetzt **für jeden Kern-Anwendungsfall Ihres Systems einen vollständig ausformulierten, modernen und robusten Prompt**.

**Ihre "Prompt-Bibliothek" ist damit vollständig und deckt ab:**
*   **Ingestion:** Klassifizierung, strukturierte und unstrukturierte Extraktion.
*   **Analyse & Verknüpfung:** Beziehungs-Validierung im Graph Gardener.
*   **Retrieval:** Intent-Analyse und dynamische Antwort-Synthese für alle wichtigen Fragetypen.
*   **User Experience:** Generierung von Folgefragen.

Ihr Team kann diese Vorlagen nun nutzen und bei Bedarf für sehr spezifische Nischenaufgaben (z.B. einen neuen Berichtstyp) leicht anpassen. Der Schlüssel ist, bei jeder Neuentwicklung die etablierten Prinzipien (dynamischer Kontext, klares Output-Format, CoT bei Bedarf) anzuwenden.