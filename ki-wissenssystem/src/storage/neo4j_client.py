from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.models.document_types import ControlItem, KnowledgeChunk
import logging

from src.config.exceptions import (
    ErrorCode, DatabaseError, SystemError
)
from src.utils.error_handler import error_handler, handle_exceptions, retry_with_backoff

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self._create_constraints()
    
    def _create_constraints(self):
        """Create uniqueness constraints and indexes"""
        with self.driver.session() as session:
            # Constraints
            session.run("""
                CREATE CONSTRAINT control_id IF NOT EXISTS
                FOR (c:ControlItem) REQUIRE c.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT chunk_id IF NOT EXISTS
                FOR (k:KnowledgeChunk) REQUIRE k.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT tech_name IF NOT EXISTS
                FOR (t:Technology) REQUIRE t.name IS UNIQUE
            """)
            
            # Indexes
            session.run("CREATE INDEX control_domain IF NOT EXISTS FOR (c:ControlItem) ON (c.domain)")
            session.run("CREATE INDEX control_source IF NOT EXISTS FOR (c:ControlItem) ON (c.source)")
    
    def create_control_item(self, control: ControlItem) -> str:
        """Create or update a control item"""
        with self.driver.session() as session:
            # Convert complex types to strings for Neo4j compatibility
            control_data = control.dict()
            
            # Convert metadata dict to JSON string
            if 'metadata' in control_data and isinstance(control_data['metadata'], dict):
                import json
                control_data['metadata'] = json.dumps(control_data['metadata'])
            
            result = session.run("""
                MERGE (c:ControlItem {id: $id})
                SET c.title = $title,
                    c.text = $text,
                    c.level = $level,
                    c.domain = $domain,
                    c.source = $source,
                    c.metadata = $metadata
                RETURN c.id as id
            """, **control_data)
            
            return result.single()["id"]
    
    def create_knowledge_chunk(self, chunk: KnowledgeChunk) -> str:
        """Create a knowledge chunk"""
        with self.driver.session() as session:
            # Convert complex types to strings for Neo4j compatibility
            chunk_data = chunk.dict()
            
            # Convert keywords list to string
            if 'keywords' in chunk_data and isinstance(chunk_data['keywords'], list):
                chunk_data['keywords'] = ', '.join(chunk_data['keywords'])
            
            # Convert metadata dict to JSON string
            if 'metadata' in chunk_data and isinstance(chunk_data['metadata'], dict):
                import json
                chunk_data['metadata'] = json.dumps(chunk_data['metadata'])
            
            result = session.run("""
                CREATE (k:KnowledgeChunk {
                    id: $id,
                    text: $text,
                    summary: $summary,
                    keywords: $keywords,
                    source: $source,
                    page: $page,
                    metadata: $metadata
                })
                RETURN k.id as id
            """, **chunk_data)
            
            chunk_id = result.single()["id"]
            
            # Create entity nodes
            for entity in chunk.entities:
                self._create_entity(session, entity, chunk_id)
            
            # Create relationships
            for rel in chunk.relationships:
                self._create_relationship(session, chunk_id, rel)
            
            return chunk_id
    
    def _create_entity(self, session, entity_name: str, chunk_id: str):
        """Create entity and link to chunk"""
        session.run("""
            MERGE (e:Entity {name: $name})
            WITH e
            MATCH (k:KnowledgeChunk {id: $chunk_id})
            MERGE (k)-[:MENTIONS]->(e)
        """, name=entity_name, chunk_id=chunk_id)
    
    def _create_relationship(self, session, chunk_id: str, rel: Dict[str, Any]):
        """Create relationship from chunk to other nodes"""
        rel_type = rel.get("type", "RELATES_TO")
        target_id = rel.get("target_id")
        confidence = rel.get("confidence", 0.5)
        
        if target_id:
            session.run(f"""
                MATCH (k:KnowledgeChunk {{id: $chunk_id}})
                MATCH (t {{id: $target_id}})
                MERGE (k)-[r:{rel_type}]->(t)
                SET r.confidence = $confidence
            """, chunk_id=chunk_id, target_id=target_id, confidence=confidence)
    
    def find_related_nodes(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find all nodes related to a given node"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (start {id: $node_id})-[*1..%d]-(end)
                RETURN DISTINCT end as node, 
                       labels(end) as labels,
                       length(path) as distance
                ORDER BY distance
                LIMIT 50
            """ % max_depth, node_id=node_id)
            
            return [dict(record) for record in result]
    
    def search_controls(self, search_term: str) -> List[Dict[str, Any]]:
        """Search controls by text"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:ControlItem)
                WHERE c.text CONTAINS $search_term 
                   OR c.title CONTAINS $search_term
                   OR c.id CONTAINS $search_term
                RETURN c
                LIMIT 20
            """, search_term=search_term)
            
            return [dict(record["c"]) for record in result]
    
    def get_orphan_nodes(self, min_connections: int = 1) -> List[Dict[str, Any]]:
        """Find nodes with few connections"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE NOT n:Entity
                WITH n, COUNT{(n)-[]->()} + COUNT{(n)<-[]-()} as connections
                WHERE connections <= $min_connections
                RETURN n, connections
                ORDER BY connections
                LIMIT 100
            """, min_connections=min_connections)
            
            return [{"node": dict(record["n"]), "connections": record["connections"]} 
                    for record in result]
    
    def create_document_node(self, document_metadata: Dict[str, Any]) -> str:
        """Erstellt oder findet Document-Knoten anhand Hash (verhindert echte Duplikate)"""
        with self.driver.session() as session:
            result = session.run("""
                // KRITISCH: MERGE auf hash, nicht auf randomUUID()!
                // Dies verhindert echte Duplikate auf Datenbankebene
                MERGE (d:Document {hash: $hash})
                ON CREATE SET
                    d.id = randomUUID(),
                    d.filename = $filename,
                    d.document_type = $document_type,
                    d.standard_name = $standard_name,
                    d.standard_version = $standard_version,
                    d.processed_at = datetime(),
                    d.source_url = $source_url,
                    d.author = $author,
                    d.file_size = $file_size,
                    d.page_count = $page_count,
                    d.created_at = datetime()
                ON MATCH SET
                    d.last_seen = datetime(),
                    d.access_count = coalesce(d.access_count, 0) + 1
                RETURN d.id as document_id, 
                       (CASE WHEN d.created_at = d.last_seen THEN 'created' ELSE 'found' END) as status
            """, **document_metadata)
            record = result.single()
            
            # Log für Debugging
            if record["status"] == "found":
                logger.info(f"Document with hash {document_metadata['hash'][:8]}... already exists")
            else:
                logger.info(f"Created new document: {record['document_id']}")
                
            return record["document_id"]

    def link_document_to_content(self, document_id: str, content_id: str, content_type: str):
        """Verknüpft Document mit seinem Inhalt"""
        with self.driver.session() as session:
            session.run(f"""
                MATCH (d:Document {{id: $document_id}})
                MATCH (c:{content_type} {{id: $content_id}})
                MERGE (d)-[:CONTAINS]->(c)
                SET c.document_source = d.filename
            """, document_id=document_id, content_id=content_id)

    def find_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Sucht Document anhand Hash (Duplikat-Prüfung)"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {hash: $hash})
                RETURN d.id as id, d.filename as filename, d.processed_at as processed_at
            """, hash=file_hash)
            record = result.single()
            return dict(record) if record else None

    def link_document_versions(self, new_doc_id: str, old_doc_id: str):
        """Verknüpft Document-Versionen"""
        with self.driver.session() as session:
            session.run("""
                MATCH (new:Document {id: $new_doc_id})
                MATCH (old:Document {id: $old_doc_id})
                MERGE (new)-[:SUPERSEDES]->(old)
            """, new_doc_id=new_doc_id, old_doc_id=old_doc_id)

    def create_contextual_relationship(
        self, 
        source_id: str, 
        target_id: str, 
        relationship_type: str,
        context_data: Dict[str, Any]
    ) -> str:
        """Erstellt kontextuelle Beziehung mit Intermediate-Knoten"""
        
        context_node_type = f"{relationship_type}Context"
        
        with self.driver.session() as session:
            # Context-Knoten erstellen
            result = session.run(f"""
                CREATE (ctx:{context_node_type} {{
                    id: randomUUID(),
                    context: $context,
                    confidence: $confidence,
                    evidence_source: $evidence_source,
                    status: $status,
                    created_at: datetime(),
                    reasoning: $reasoning
                }})
                RETURN ctx.id as context_id
            """, **context_data)
            
            context_id = result.single()["context_id"]
            
            # Quelle -> Kontext -> Ziel verknüpfen
            session.run(f"""
                MATCH (s {{id: $source_id}}), (ctx {{id: $context_id}}), (t {{id: $target_id}})
                CREATE (s)-[:HAS_{relationship_type.upper()}]->(ctx)
                CREATE (ctx)-[:{relationship_type.upper()}_TARGET]->(t)
            """, source_id=source_id, context_id=context_id, target_id=target_id)
            
            return context_id

    def close(self):
        self.driver.close()