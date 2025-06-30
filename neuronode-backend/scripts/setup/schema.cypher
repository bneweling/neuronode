// Document Node Schema
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT document_hash_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.hash IS UNIQUE;

// Indizes für Performance
CREATE INDEX document_standard_idx IF NOT EXISTS FOR (d:Document) ON (d.standard_name);
CREATE INDEX document_type_idx IF NOT EXISTS FOR (d:Document) ON (d.document_type);
CREATE INDEX document_version_idx IF NOT EXISTS FOR (d:Document) ON (d.standard_version);

// Volltext-Index für Suche
CREATE FULLTEXT INDEX document_fulltext_idx IF NOT EXISTS FOR (d:Document) ON EACH [d.filename, d.standard_name, d.author];

// Erweiterte Indizes für ControlItem und KnowledgeChunk
CREATE INDEX control_title_idx IF NOT EXISTS FOR (c:ControlItem) ON (c.title);
CREATE INDEX chunk_source_idx IF NOT EXISTS FOR (k:KnowledgeChunk) ON (k.document_source);

// Volltext-Indizes für bessere Suche
CREATE FULLTEXT INDEX control_fulltext_idx IF NOT EXISTS FOR (c:ControlItem) ON EACH [c.title, c.text];
CREATE FULLTEXT INDEX chunk_fulltext_idx IF NOT EXISTS FOR (k:KnowledgeChunk) ON EACH [k.text, k.summary];
CREATE FULLTEXT INDEX technology_fulltext_idx IF NOT EXISTS FOR (t:Technology) ON EACH [t.name, t.description];

// Constraints für neue Node-Typen
CREATE CONSTRAINT implementation_id_unique IF NOT EXISTS FOR (i:Implementation) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT support_context_id_unique IF NOT EXISTS FOR (s:SupportContext) REQUIRE s.id IS UNIQUE; 