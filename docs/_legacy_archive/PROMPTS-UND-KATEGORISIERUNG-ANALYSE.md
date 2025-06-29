# Analyse aller Hardcoded Prompts und Kategorisierungslogik
## KI-Wissenssystem - Detaillierte Dokumentation

**Erstellt am:** `2025-01-25`  
**Version:** `1.0`  
**Zweck:** Vollständige Dokumentation aller im System verwendeten hardcoded Prompts, Keyword-Kataloge, Muster und Kategorisierungslogik

---

## 📋 Inhaltsverzeichnis

1. [LLM-Prompts](#llm-prompts)
2. [Dokumentklassifizierung](#dokumentklassifizierung)
3. [Intent-Analyse und Entity-Extraktion](#intent-analyse-und-entity-extraktion)
4. [Query-Expansion und Synonyme](#query-expansion-und-synonyme)
5. [Response-Synthese](#response-synthese)
6. [Control-Extraktion](#control-extraktion)
7. [Graph-Analyse](#graph-analyse)
8. [Validierung und Qualitätskontrolle](#validierung-und-qualitätskontrolle)
9. [Regex-Pattern und Erkennungsmuster](#regex-pattern-und-erkennungsmuster)
10. [Hardcoded Keywords und Kategorien](#hardcoded-keywords-und-kategorien)

---

## 🤖 LLM-Prompts

### Response Synthesizer Prompts
**Datei:** `src/retrievers/response_synthesizer.py`

#### 1. Compliance-Requirements Prompt
```
Du bist ein Compliance-Experte, der Beratern hilft, Anforderungen zu verstehen.

Basierend auf den gefundenen Informationen:
1. Erkläre die relevanten Compliance-Anforderungen klar und präzise
2. Nenne die spezifischen Control-IDs und deren Anforderungen
3. Erwähne das Level/die Kritikalität (falls vorhanden)
4. Erkläre den Kontext und Zweck der Anforderung
5. Weise auf verwandte Anforderungen hin

Struktur:
- Hauptanforderung(en)
- Details und Kontext
- Verwandte Controls
- Praktische Hinweise

Verwende Markdown-Formatierung.
```

#### 2. Technical Implementation Prompt
```
Du bist ein technischer Experte, der bei der Implementierung von Sicherheitsmaßnahmen hilft.

Basierend auf den gefundenen Informationen:
1. Beschreibe konkrete Implementierungsschritte
2. Nenne spezifische Konfigurationen oder Settings
3. Erwähne relevante Tools oder Features
4. Gib Best Practices und Empfehlungen
5. Weise auf häufige Fehler oder Fallstricke hin

Struktur:
- Übersicht der Lösung
- Schritt-für-Schritt Anleitung
- Technische Details
- Hinweise und Empfehlungen

Nutze Code-Blöcke für Befehle oder Konfigurationen.
```

#### 3. Mapping-Comparison Prompt
```
Du bist ein Experte für Compliance-Mappings zwischen verschiedenen Standards.

Basierend auf den gefundenen Mappings:
1. Zeige die Entsprechungen zwischen den Standards
2. Erkläre Gemeinsamkeiten und Unterschiede
3. Weise auf Lücken oder zusätzliche Anforderungen hin
4. Gib Empfehlungen für die praktische Umsetzung

Struktur:
- Mapping-Übersicht (Tabelle wenn möglich)
- Detaillierte Entsprechungen
- Unterschiede und Lücken
- Empfehlungen

Verwende Tabellen für bessere Übersichtlichkeit.
```

#### 4. Best Practice Prompt
```
Du bist ein Sicherheitsexperte, der Best Practices empfiehlt.

Basierend auf den gefundenen Informationen:
1. Stelle bewährte Verfahren vor
2. Begründe die Empfehlungen
3. Gib konkrete Beispiele
4. Erwähne häufige Fehler
5. Priorisiere die Maßnahmen

Struktur:
- Top-Empfehlungen
- Detaillierte Best Practices
- Umsetzungshinweise
- Zu vermeidende Fehler

Nutze Aufzählungen und Priorisierungen.
```

#### 5. Specific Control Prompt
```
Du bist ein Compliance-Experte, der spezifische Controls erklärt.

Für das/die angefragte(n) Control(s):
1. Gib die vollständige Control-Beschreibung
2. Erkläre den Zweck und Kontext
3. Nenne konkrete Umsetzungsanforderungen
4. Verweise auf verwandte Controls
5. Gib Implementierungshinweise

Struktur:
- Control-Details (ID, Titel, Level)
- Vollständige Anforderung
- Erklärung und Kontext
- Verwandte Controls
- Umsetzungshinweise
```

#### 6. General Information Prompt
```
Du bist ein hilfreicher IT-Sicherheitsexperte.

Beantworte die Frage basierend auf den gefundenen Informationen:
1. Gib eine klare und verständliche Antwort
2. Strukturiere die Information logisch
3. Verwende Beispiele wo hilfreich
4. Verweise auf relevante Standards oder Best Practices

Sei präzise aber vollständig.
```

#### 7. Follow-up Questions Prompt
```
Basierend auf der Frage und Antwort, 
generiere 3 relevante Folgefragen, die der Nutzer stellen könnte.

Die Fragen sollten:
- Spezifischer oder tiefer ins Thema gehen
- Verwandte Aspekte abdecken
- Praktische nächste Schritte adressieren

Gib nur die Fragen zurück, eine pro Zeile.
```

---

## 📑 Dokumentklassifizierung

### Document Classifier Prompts
**Datei:** `src/document_processing/classifier.py`

#### LLM-basierte Klassifizierung
```
Du bist ein Experte für die Klassifizierung von Compliance- und Sicherheitsdokumenten.
Analysiere den gegebenen Text und klassifiziere ihn in eine der folgenden Kategorien:

- BSI_GRUNDSCHUTZ: BSI IT-Grundschutz Dokumente
- BSI_C5: BSI Cloud Computing Compliance Controls Katalog
- ISO_27001: ISO 27001 Standard Dokumente
- NIST_CSF: NIST Cybersecurity Framework
- WHITEPAPER: Technische Whitepaper von Herstellern
- TECHNICAL_DOC: Technische Dokumentationen und Anleitungen
- FAQ: Häufig gestellte Fragen
- UNKNOWN: Nicht klassifizierbar

Antworte NUR mit dem Kategorienamen.
```

### Regel-basierte Klassifizierung
**Datei:** `src/document_processing/classifier.py`

#### Keyword-basierte Erkennung
```python
# BSI IT-Grundschutz
["it-grundschutz", "bsi-standard", "grundschutz", "baustein"]

# BSI C5
["cloud computing compliance", "bsi c5", "c5-kriterien"]

# ISO 27001
["iso/iec 27001", "iso 27001", "isms", "informationssicherheits-managementsystem"]

# NIST CSF
["nist cybersecurity framework", "nist csf", "nist.sp.800-53"]

# Whitepaper
["whitepaper", "technical paper", "produktdokumentation"]

# Technical Documentation
["anleitung", "installation", "konfiguration", "setup", "technical documentation"]

# FAQ
["faq", "häufig gestellte fragen", "frequently asked"]
```

#### Dateiname-basierte Erkennung
```python
# Filename-Pattern
if "grundschutz" in filename:
    return DocumentType.BSI_GRUNDSCHUTZ
elif "iso27001" in filename or "iso_27001" in filename:
    return DocumentType.ISO_27001
elif "nist" in filename:
    return DocumentType.NIST_CSF
```

---

## 🎯 Intent-Analyse und Entity-Extraktion

### Intent Analyzer
**Datei:** `src/retrievers/intent_analyzer.py`

#### Intent Analysis Prompt
```
Du bist ein Experte für die Analyse von Compliance- und Sicherheitsfragen.

Analysiere die Nutzeranfrage und identifiziere:

1. **Primary Intent** - Was will der Nutzer hauptsächlich wissen?
   - compliance_requirement: Anforderungen eines Standards
   - technical_implementation: Technische Umsetzung
   - mapping_comparison: Vergleich zwischen Standards
   - best_practice: Best Practices und Empfehlungen
   - specific_control: Spezifische Control-Abfrage
   - general_information: Allgemeine Informationen

2. **Entities** - Extrahiere alle relevanten Entitäten:
   - standards: Compliance-Standards (BSI C5, ISO 27001, etc.)
   - technologies: Technologien/Produkte (Azure, AWS, etc.)
   - controls: Spezifische Control-IDs
   - concepts: Sicherheitskonzepte (MFA, Encryption, etc.)

3. **Search Keywords** - Wichtige Suchbegriffe

4. **Special Requirements**:
   - requires_comparison: Müssen Standards verglichen werden?
   - temporal_context: Gibt es zeitliche Einschränkungen?
```

#### Fallback Intent Detection (Keyword-basiert)
```python
# Compliance Requirements
["was fordert", "anforderung", "muss ich", "compliance"]

# Technical Implementation
["wie implementiere", "umsetzen", "konfigurieren", "einrichten"]

# Mapping Comparison
["vergleich", "unterschied", "mapping", "vs", "versus"]

# Best Practices
["best practice", "empfehlung", "tipps"]
```

#### Stopwords (Deutsche Sprache)
```python
stopwords = {
    "der", "die", "das", "und", "oder", "aber", "mit", "von", "zu", "in",
    "für", "auf", "bei", "nach", "wie", "was", "wann", "wo", "ist", "sind",
    "wird", "werden", "kann", "können", "muss", "müssen", "soll", "sollen"
}
```

#### Synonym-Mapping
```python
synonym_map = {
    "mfa": ["multi-factor authentication", "zwei-faktor", "2fa", "mehrstufige authentifizierung"],
    "encryption": ["verschlüsselung", "crypto", "kryptografie"],
    "backup": ["datensicherung", "sicherung", "recovery"],
    "firewall": ["brandmauer", "paketfilter", "netzwerkschutz"],
    "identity": ["identität", "iam", "identity management", "identitätsverwaltung"],
    "azure": ["microsoft azure", "azure cloud", "ms azure"],
    "aws": ["amazon web services", "amazon cloud"],
    "patch": ["update", "patching", "aktualisierung", "security update"]
}
```

---

## 🔍 Query-Expansion und Synonyme

### Query Expander
**Datei:** `src/retrievers/query_expander.py`

#### Technische Synonyme (Erweitert)
```python
technical_synonyms = {
    "passwort": ["password", "kennwort", "authentifizierung", "login"],
    "server": ["system", "rechner", "maschine", "host"],
    "netzwerk": ["network", "lan", "wan", "infrastruktur"],
    "sicherheit": ["security", "schutz", "absicherung"],
    "backup": ["sicherung", "datensicherung", "archivierung"],
    "encryption": ["verschlüsselung", "chiffrierung", "kryptographie"],
    "firewall": ["brandmauer", "paketfilter", "netzwerkschutz"],
    "active_directory": ["ad", "verzeichnisdienst", "ldap", "domain_controller"],
    "compliance": ["konformität", "regelkonformität", "einhaltung"],
    "audit": ["prüfung", "revision", "kontrolle", "auditierung"]
}
```

#### Stopwords für Query Expansion
```python
stopwords = {
    'der', 'die', 'das', 'und', 'oder', 'ist', 'sind', 
    'ein', 'eine', 'wie', 'was', 'wo', 'wann', 'warum'
}
```

#### LLM Query Expansion Prompt
```
Erweitere die folgende Suchanfrage um verwandte Begriffe und Konzepte:

ANFRAGE: "{query}"

KONTEXT:
{context oder "Keine zusätzlichen Kontextinformationen verfügbar"}

Analysiere die Anfrage und:
1. Identifiziere verwandte technische Begriffe
2. Erkenne implizite Konzepte
3. Füge relevante Synonyme hinzu
4. Berücksichtige Compliance- und Sicherheitskontext

Antworte im JSON-Format:
{
    "expanded_terms": ["begriff1", "begriff2", ...],
    "context_terms": ["kontext1", "kontext2", ...],
    "reasoning": "Begründung für die Erweiterung",
    "confidence": "HIGH/MEDIUM/LOW",
    "implicit_concepts": ["konzept1", "konzept2", ...]
}
```

#### Alternative Formulierungen Prompt
```
Generiere 3-5 alternative Formulierungen für diese Suchanfrage:

ORIGINAL: "{query}"

Die Alternativen sollten:
1. Dieselbe Intention haben
2. Andere Schlüsselwörter verwenden
3. Formal und informell variieren
4. Technisch und business-orientiert sein

Antworte nur mit den alternativen Formulierungen, eine pro Zeile.
```

---

## 🧩 Control-Extraktion

### Structured Extractor
**Datei:** `src/extractors/structured_extractor.py`

#### BSI IT-Grundschutz Extraction Prompt
```
Du bist ein Experte für BSI IT-Grundschutz. 
Extrahiere alle Sicherheitsanforderungen aus dem gegebenen Text.

Jede Anforderung hat:
- Eine ID (z.B. SYS.1.1.A1, OPS.1.1.A5)
- Einen Titel
- Eine Beschreibung der Anforderung
- Ein Level (Basis, Standard, oder Hoch)
- Eine Domäne (der erste Teil der ID, z.B. SYS, OPS, APP)

Achte darauf, den vollständigen Text der Anforderung zu erfassen.
```

#### BSI C5 Extraction Prompt
```
Du bist ein Experte für BSI C5 (Cloud Computing Compliance Controls).
Extrahiere alle Kontrollen aus dem gegebenen Text.

Jede Kontrolle hat:
- Eine ID (z.B. OPS-01, IDM-09)
- Einen Titel
- Eine detaillierte Beschreibung
- Eine Domäne (z.B. OPS, IDM, PS)

Erfasse auch Hinweise auf verwandte Kontrollen oder Standards.
```

#### ISO 27001 Extraction Prompt
```
Du bist ein Experte für ISO 27001/27002.
Extrahiere alle Controls aus dem gegebenen Text.

Jedes Control hat:
- Eine Nummer (z.B. 5.1.1, A.8.1.1)
- Einen Titel
- Die Control-Beschreibung
- Die Kategorie/Domäne
```

#### NIST CSF Extraction Prompt
```
Du bist ein Experte für das NIST Cybersecurity Framework.
Extrahiere alle Controls/Subcategories aus dem Text.

Jedes Element hat:
- Eine ID (z.g. ID.AM-1, PR.AC-4)
- Einen Titel/Namen
- Die Beschreibung
- Die Function (Identify, Protect, Detect, Respond, Recover)
- Die Category
```

---

## 📊 Graph-Analyse

### Graph Gardener
**Datei:** `src/orchestration/graph_gardener.py`

#### Link Validation Prompt
```
Du bist ein Experte für Compliance und IT-Sicherheit.

Bewerte, ob der gegebene Text-Chunk eine Beziehung zum Control hat.

Mögliche Beziehungen:
- IMPLEMENTS: Der Text beschreibt, wie das Control umgesetzt wird
- SUPPORTS: Der Text unterstützt oder ergänzt das Control
- REFERENCES: Der Text verweist auf das Control
- CONFLICTS: Der Text widerspricht dem Control
- NONE: Keine relevante Beziehung

Antworte im Format:
RELATIONSHIP: <type>
CONFIDENCE: <0.0-1.0>
REASON: <Kurze Begründung>
```

#### Graph Keywords für Relevanz-Analyse
**Datei:** `src/retrievers/response_synthesizer.py`
```python
graph_keywords = [
    'beziehung', 'verbindung', 'zusammenhang', 'verknüpfung',
    'mapping', 'zuordnung', 'entsprechung', 'äquivalenz',
    'struktur', 'hierarchie', 'abhängigkeit', 'vernetzung',
    'graph', 'netzwerk', 'topologie', 'architektur',
    'control', 'controls', 'standard', 'standards',
    'framework', 'richtlinie', 'compliance'
]
```

---

## ✅ Validierung und Qualitätskontrolle

### Quality Validator
**Datei:** `src/extractors/quality_validator.py`

#### Control Validation Prompt
```
Du bist ein Experte für Compliance-Standards. 
Validiere das extrahierte Control auf Vollständigkeit und Richtigkeit.

Bewerte:
1. Ist die Control-ID korrekt formatiert?
2. Ist der Titel aussagekräftig?
3. Ist die Beschreibung vollständig?
4. Sind alle Pflichtfelder vorhanden?
5. Stimmt das Level/die Kategorie?

Antworte im JSON-Format:
{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["problem1", "problem2"],
    "suggestions": ["suggestion1", "suggestion2"]
}
```

#### Control Comparison Prompt
```
Vergleiche zwei Versionen eines extrahierten Controls.

Bewerte:
1. Stimmen die wichtigsten Felder (ID, Title) überein?
2. Ist der Inhalt semantisch gleich?
3. Welche Version ist vollständiger/besser?

Antworte im JSON-Format:
{
    "match_score": 0.0-1.0,
    "matching_fields": ["id", "title", ...],
    "differences": ["field: difference description"],
    "preferred_version": 1 oder 2,
    "merge_suggestions": {"field": "value"}
}
```

---

## 🔧 Regex-Pattern und Erkennungsmuster

### Control-ID Pattern
**Datei:** `src/extractors/structured_extractor.py`

#### BSI IT-Grundschutz Pattern
```python
"control": re.compile(r'([A-Z]{3,4}\.\d+(?:\.\d+)*\.A\d+)\s*([^\n]+)'),
"level": re.compile(r'\((Basis|Standard|Hoch)\)'),
"domain": re.compile(r'^([A-Z]{3,4})')
```

#### BSI C5 Pattern
```python
"control": re.compile(r'([A-Z]{2,3}-\d{2})\s*([^\n]+)'),
"domain": re.compile(r'^([A-Z]{2,3})')
```

### Entity Recognition Pattern
**Datei:** `src/retrievers/intent_analyzer.py`

#### Control-ID Patterns
```python
"bsi_control": re.compile(r'\b([A-Z]{3,4}[-.]?\d+(?:\.\d+)*(?:\.A\d+)?)\b'),
"c5_control": re.compile(r'\b([A-Z]{2,3}-\d{2})\b'),
"iso_control": re.compile(r'\b(?:ISO\s*)?(?:27001|27002)(?:\s*[:\-]\s*)?([A-Z]?\d+(?:\.\d+)*)\b', re.I)
```

#### Technology Patterns
```python
"technology": re.compile(r'\b(Azure|AWS|GCP|Active Directory|Entra|Office 365|SharePoint|Teams)\b', re.I)
```

#### Standards Patterns
```python
"standard": re.compile(r'\b(BSI(?:\s+(?:C5|IT-Grundschutz))?|ISO\s*2700[0-9]|NIST(?:\s+CSF)?|SOC\s*2)\b', re.I)
```

### Query Expander Patterns
**Datei:** `src/retrievers/query_expander.py`

#### Control Pattern für Query Expansion
```python
control_patterns = [
    r'\b([A-Z]{2,4}\.?\d+\.?A\d+)\b',  # BSI Format: ORP.4.A1
    r'\b([A-Z]{2,4}-\d+)\b',           # ISO Format: AC-2
    r'\b([A-Z]{3}\.\d{2})\b'           # Alternative: SYS.01
]
```

### Document Processing Patterns
**Datei:** `src/document_processing/chunker.py`

#### Content Structure Pattern
```python
control_pattern = re.compile(
    r'(?:^|\n)([A-Z]+[-.]?\d+(?:\.\d+)*(?:\.[A-Z]\d*)?)\s*[:\-]?\s*([^\n]+)'
)
heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
```

---

## 📚 Hardcoded Keywords und Kategorien

### Document Type Keywords
**Datei:** `src/models/document_types.py`

#### Document Type Enumeration
```python
class DocumentType(Enum):
    BSI_GRUNDSCHUTZ = "bsi_grundschutz"
    BSI_C5 = "bsi_c5"
    ISO_27001 = "iso_27001"
    NIST_CSF = "nist_csf"
    WHITEPAPER = "whitepaper"
    TECHNICAL_DOC = "technical_doc"
    FAQ = "faq"
    UNKNOWN = "unknown"
```

### Intent Types
**Datei:** `src/retrievers/intent_analyzer.py`

#### Query Intent Enumeration
```python
class QueryIntent(Enum):
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    TECHNICAL_IMPLEMENTATION = "technical_implementation"
    MAPPING_COMPARISON = "mapping_comparison"
    BEST_PRACTICE = "best_practice"
    SPECIFIC_CONTROL = "specific_control"
    GENERAL_INFORMATION = "general_information"
```

### Node Types und Farben
**Datei:** `src/retrievers/response_synthesizer.py`

#### Node Color Mapping
```python
color_map = {
    "ControlItem": "#FF6B6B",     # Red
    "Technology": "#4ECDC4",      # Teal
    "KnowledgeChunk": "#45B7D1",  # Blue
    "Document": "#96CEB4",        # Green
    "Entity": "#FECA57"           # Yellow
}
```

#### Edge Color Mapping
```python
color_map = {
    "IMPLEMENTS": "#E74C3C",      # Red
    "SUPPORTS": "#3498DB",        # Blue
    "REFERENCES": "#9B59B6",      # Purple
    "CONTAINS": "#27AE60",        # Green
    "RELATES_TO": "#95A5A6"       # Gray
}
```

### Obsidian Plugin Categories
**Datei:** `obsidian-ki-plugin/src/components/GraphSearch.ts`

#### Category Icons
```typescript
const categoryIcons = {
    'ControlItem': '🛡️',
    'Technology': '⚙️',
    'KnowledgeChunk': '📄',
    'Document': '📝',
    'Process': '🔄',
    'Risk': '⚠️'
}
```

#### Category Colors
```typescript
const categoryColors = {
    'ControlItem': '#4a9eff',
    'Technology': '#7c3aed',
    'KnowledgeChunk': '#10b981',
    'Document': '#f59e0b',
    'Process': '#ef4444',
    'Risk': '#8b5cf6'
}
```

### Document Type Labels
**Datei:** `obsidian-ki-plugin/src/components/DocumentUploadInterface.ts`

#### Type Label Mapping
```typescript
const labels = {
    'bsi_grundschutz': 'BSI IT-Grundschutz',
    'bsi_c5': 'BSI C5 Cloud',
    'iso_27001': 'ISO 27001',
    'nist_csf': 'NIST Cybersecurity Framework',
    'whitepaper': 'Technisches Whitepaper',
    'technical_doc': 'Technische Dokumentation',
    'faq': 'FAQ Dokument',
    'unknown': 'Unbekannter Typ'
}
```

---

## 📈 Metadata-Extraktion

### Metadata Extractor
**Datei:** `src/document_processing/metadata_extractor.py`

#### Standard Recognition Patterns
```python
standard_patterns = {
    'BSI': r'BSI.*Grundschutz.*(\d{4})',
    'ISO': r'ISO.*(\d+):(\d{4})',
    'NIST': r'NIST.*(\w+).*v?(\d+\.?\d*)',
    'CIS': r'CIS.*Controls.*v?(\d+\.?\d*)'
}
```

#### Document Type Detection (Filename-based)
```python
# Filename-based detection logic
if any(word in filename for word in ['grundschutz', 'bsi']):
    return 'BSI_GRUNDSCHUTZ'
elif 'iso' in filename and '27001' in filename:
    return 'ISO_27001'
elif 'nist' in filename:
    return 'NIST_FRAMEWORK'
elif 'cis' in filename:
    return 'CIS_CONTROLS'
```

---

## 🔄 Auto-Relationship Discovery

### Relationship Discovery
**Datei:** `src/orchestration/auto_relationship_discovery.py`

#### Simple Relationship Detection Patterns
```python
# Control-IDs finden
control_pattern = r'\b([A-Z]{2,4}\.?\d+\.?A\d+)\b'

# Technologien finden
tech_pattern = r'\b(Active\s+Directory|LDAP|Firewall)\b'
```

#### Relationship Types
```python
class RelationshipType(Enum):
    IMPLEMENTS = "IMPLEMENTS"
    SUPPORTS = "SUPPORTS"
    REFERENCES = "REFERENCES"
    CONFLICTS = "CONFLICTS"
    RELATES_TO = "RELATES_TO"
```

---

## 📝 Unstructured Processing

### Unstructured Processor
**Datei:** `src/extractors/unstructured_processor.py`

#### Chunk Analysis Prompt
```
Du bist ein Experte für IT-Sicherheit und Compliance.
Analysiere den gegebenen Textabschnitt und extrahiere:

1. Eine prägnante Zusammenfassung (2-3 Sätze)
2. Wichtige Schlüsselwörter und technische Begriffe
3. Erwähnte Technologien, Produkte oder Standards
4. Die Hauptthemen des Abschnitts
5. Mögliche Beziehungen zu Compliance-Anforderungen

Für Beziehungen, gib an:
- relation_type: z.B. "IMPLEMENTS", "RELATES_TO", "REFERENCES"
- target: Die vermutete Control-ID oder der Technologie-Name
- confidence: Wie sicher bist du (0.0-1.0)
```

#### Entity Linking Prompt
```
Gegeben ist ein Text-Chunk und eine Liste von bekannten Compliance-Controls.
Identifiziere, welche Controls dieser Text möglicherweise implementiert oder referenziert.

Bekannte Controls:
{known_controls}

Antworte mit einer Liste von Beziehungen im Format:
- control_id: Die ID des relevanten Controls
- relationship: Art der Beziehung (IMPLEMENTS, SUPPORTS, REFERENCES)
- confidence: Konfidenz-Score (0.0-1.0)
- reason: Kurze Begründung
```

---

## 🎯 Zusammenfassung

### Kritische Hardcoded Elemente

1. **Prompts:** 15+ spezialisierte LLM-Prompts für verschiedene Anwendungsfälle
2. **Keywords:** 100+ hardcoded Keywords für Dokumentklassifizierung
3. **Regex-Pattern:** 20+ Pattern für Control-IDs, Technologien und Standards
4. **Synonym-Maps:** 50+ technische Begriffe mit Synonymen
5. **Intent-Detection:** 6 verschiedene Intent-Typen mit Keyword-Triggern
6. **Fallback-Logic:** Regel-basierte Klassifizierung für API-Ausfälle
7. **Color-Mappings:** Farbkodierung für UI-Komponenten
8. **Type-Definitions:** Umfassende Enumerations für Dokument- und Node-Typen

### Wartungsempfehlungen

1. **Zentralisierung:** Prompts in separaten Konfigurationsdateien speichern
2. **Versionierung:** Änderungen an Prompts versionieren und dokumentieren
3. **A/B Testing:** Verschiedene Prompt-Varianten testen
4. **Internationalisierung:** Mehrsprachige Unterstützung vorbereiten
5. **Performance-Monitoring:** Erfolg verschiedener Pattern überwachen
6. **Automatisierung:** Keyword-Listen aus Trainingsdaten generieren

**Ende der Dokumentation** - Stand: 2025-01-25 