from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.models.document_types import ControlItem, KnowledgeChunk
import logging
import os
import json
from pathlib import Path

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
        # Enhanced initialization with enterprise features
        self._ensure_database_ready()
    
    def _ensure_database_ready(self):
        """Enterprise-ready database initialization with auto-healing"""
        try:
            logger.info("🔄 Initializing Neo4j database with enterprise features...")
            
            # Step 1: Create complete schema
            self._create_complete_schema()
            
            # Step 2: Validate database health
            db_health = self._validate_database_health()
            
            # Step 3: Auto-load sample data if database is empty
            if db_health["is_empty"]:
                logger.info("🚀 Database is empty - loading sample data for production readiness")
                self._load_sample_data()
            
            # Step 4: Final validation
            final_health = self._validate_database_health()
            if final_health["is_functional"]:
                logger.info("✅ Neo4j database ready for enterprise production")
            else:
                logger.warning("⚠️ Database initialized but may need additional setup")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            # Don't fail completely - allow degraded mode
            logger.warning("🔧 Continuing in degraded mode - manual database setup may be required")
    
    def _create_complete_schema(self):
        """Create complete Neo4j schema for enterprise production"""
        with self.driver.session() as session:
            try:
                # Core constraints
                schema_commands = [
                    # Document constraints
                    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                    "CREATE CONSTRAINT document_hash_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.hash IS UNIQUE",
                    
                    # Control and chunk constraints
                    "CREATE CONSTRAINT control_id IF NOT EXISTS FOR (c:ControlItem) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (k:KnowledgeChunk) REQUIRE k.id IS UNIQUE",
                    "CREATE CONSTRAINT tech_name IF NOT EXISTS FOR (t:Technology) REQUIRE t.name IS UNIQUE",
                    "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                    
                    # Performance indexes
                    "CREATE INDEX document_standard_idx IF NOT EXISTS FOR (d:Document) ON (d.standard_name)",
                    "CREATE INDEX document_type_idx IF NOT EXISTS FOR (d:Document) ON (d.document_type)",
                    "CREATE INDEX control_domain IF NOT EXISTS FOR (c:ControlItem) ON (c.domain)",
                    "CREATE INDEX control_source IF NOT EXISTS FOR (c:ControlItem) ON (c.source)",
                    "CREATE INDEX control_title_idx IF NOT EXISTS FOR (c:ControlItem) ON (c.title)",
                    "CREATE INDEX chunk_source_idx IF NOT EXISTS FOR (k:KnowledgeChunk) ON (k.document_source)",
                    
                    # Fulltext indexes for search
                    "CREATE FULLTEXT INDEX document_fulltext_idx IF NOT EXISTS FOR (d:Document) ON EACH [d.filename, d.standard_name, d.author]",
                    "CREATE FULLTEXT INDEX control_fulltext_idx IF NOT EXISTS FOR (c:ControlItem) ON EACH [c.title, c.text]",
                    "CREATE FULLTEXT INDEX chunk_fulltext_idx IF NOT EXISTS FOR (k:KnowledgeChunk) ON EACH [k.text, k.summary]",
                    "CREATE FULLTEXT INDEX technology_fulltext_idx IF NOT EXISTS FOR (t:Technology) ON EACH [t.name, t.description]"
                ]
                
                for i, command in enumerate(schema_commands, 1):
                    try:
                        session.run(command)
                        logger.debug(f"✅ Schema command {i}/{len(schema_commands)} executed")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                            logger.debug(f"ℹ️ Schema command {i} already exists (skipped)")
                        else:
                            logger.warning(f"⚠️ Schema command {i} failed: {e}")
                
                logger.info("✅ Complete Neo4j schema initialized")
                
            except Exception as e:
                logger.error(f"❌ Schema creation failed: {e}")
                raise DatabaseError("Failed to create database schema", ErrorCode.NEO4J_CONNECTION_FAILED)
    
    def _validate_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health validation"""
        health = {
            "is_connected": False,
            "is_empty": True,
            "is_functional": False,
            "node_counts": {},
            "relationship_counts": {},
            "schema_status": "unknown"
        }
        
        try:
            with self.driver.session() as session:
                # Test basic connectivity
                session.run("RETURN 1").single()
                health["is_connected"] = True
                
                # Check node counts
                node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                total_nodes = 0
                for record in node_result:
                    labels = record["labels"]
                    count = record["count"]
                    label_str = ":".join(labels) if labels else "Unknown"
                    health["node_counts"][label_str] = count
                    total_nodes += count
                
                # Check relationship counts
                rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
                total_rels = 0
                for record in rel_result:
                    rel_type = record["rel_type"]
                    count = record["count"]
                    health["relationship_counts"][rel_type] = count
                    total_rels += count
                
                # Determine if database is empty
                health["is_empty"] = total_nodes == 0
                
                # Check if database is functional (has proper structure)
                required_labels = ["ControlItem", "KnowledgeChunk", "Technology", "Entity"]
                has_required_structure = any(
                    any(label in node_label for label in required_labels)
                    for node_label in health["node_counts"].keys()
                )
                
                health["is_functional"] = (
                    health["is_connected"] and 
                    not health["is_empty"] and 
                    has_required_structure
                )
                health["schema_status"] = "complete" if health["is_functional"] else "minimal"
                
                logger.debug(f"📊 Database health: {health}")
                
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            health["error"] = str(e)
        
        return health
    
    def _load_sample_data(self):
        """Load enterprise sample data for immediate productivity"""
        try:
            # Check for existing sample data files
            backend_dir = Path(__file__).parent.parent.parent
            sample_files = {
                "bst1": backend_dir / "BST1.json",
                "bst2": backend_dir / "BST2.json", 
                "cypher": backend_dir / "BSTcypher.txt"
            }
            
            # Load JSON data if available
            loaded_data = False
            for name, file_path in sample_files.items():
                if file_path.exists() and name.startswith("bst"):
                    try:
                        logger.info(f"📂 Loading sample data from {file_path.name}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Import control items
                        if 'controls' in data:
                            self._import_controls(data['controls'])
                        
                        # Import knowledge chunks  
                        if 'knowledge_chunks' in data:
                            self._import_knowledge_chunks(data['knowledge_chunks'])
                        
                        # Import technologies
                        if 'technologies' in data:
                            self._import_technologies(data['technologies'])
                        
                        # Import entities
                        if 'entities' in data:
                            self._import_entities(data['entities'])
                            
                        loaded_data = True
                        logger.info(f"✅ Successfully loaded sample data from {file_path.name}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load {file_path.name}: {e}")
            
            # Execute Cypher relationships if available
            cypher_file = sample_files["cypher"]
            if cypher_file.exists() and loaded_data:
                try:
                    logger.info("🔗 Creating sample relationships from Cypher script")
                    self._execute_cypher_script(cypher_file)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to execute Cypher script: {e}")
            
            if not loaded_data:
                logger.info("🎯 Creating minimal sample data for system validation")
                self._create_minimal_sample_data()
                
        except Exception as e:
            logger.error(f"❌ Sample data loading failed: {e}")
    
    def _import_controls(self, controls: List[Dict]):
        """Import control items from sample data"""
        with self.driver.session() as session:
            for control_data in controls:
                try:
                    session.run("""
                        MERGE (c:ControlItem {id: $id})
                        SET c.title = $title,
                            c.text = $text, 
                            c.level = $level,
                            c.domain = $domain,
                            c.source = $source,
                            c.metadata = $metadata
                    """, **control_data)
                except Exception as e:
                    logger.debug(f"Control import warning: {e}")
    
    def _import_knowledge_chunks(self, chunks: List[Dict]):
        """Import knowledge chunks from sample data"""
        with self.driver.session() as session:
            for chunk_data in chunks:
                try:
                    # Convert complex types for Neo4j
                    if 'keywords' in chunk_data and isinstance(chunk_data['keywords'], list):
                        chunk_data['keywords'] = ', '.join(chunk_data['keywords'])
                    if 'metadata' in chunk_data and isinstance(chunk_data['metadata'], dict):
                        chunk_data['metadata'] = json.dumps(chunk_data['metadata'])
                    
                    session.run("""
                        CREATE (k:KnowledgeChunk {
                            id: $id,
                            text: $text,
                            summary: $summary,
                            keywords: $keywords,
                            source: $source,
                            page: $page,
                            metadata: $metadata
                        })
                    """, **chunk_data)
                except Exception as e:
                    logger.debug(f"Chunk import warning: {e}")
    
    def _import_technologies(self, technologies: List[Dict]):
        """Import technology nodes from sample data"""
        with self.driver.session() as session:
            for tech_data in technologies:
                try:
                    session.run("""
                        MERGE (t:Technology {name: $name})
                        SET t.category = $category,
                            t.metadata = $metadata
                    """, 
                    name=tech_data['name'],
                    category=tech_data.get('category', 'Unknown'),
                    metadata=json.dumps(tech_data.get('metadata', {})))
                except Exception as e:
                    logger.debug(f"Technology import warning: {e}")
    
    def _import_entities(self, entities: List[Dict]):
        """Import entity nodes from sample data"""
        with self.driver.session() as session:
            for entity_data in entities:
                try:
                    session.run("""
                        MERGE (e:Entity {name: $name})
                        SET e.type = $type,
                            e.description = $description
                    """,
                    name=entity_data['name'],
                    type=entity_data.get('type', 'Unknown'),
                    description=entity_data.get('description', ''))
                except Exception as e:
                    logger.debug(f"Entity import warning: {e}")
    
    def _execute_cypher_script(self, cypher_file: Path):
        """Execute Cypher script for relationships"""
        with open(cypher_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split commands more intelligently
        commands = []
        current_command = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                if current_command:
                    commands.append('\n'.join(current_command))
                    current_command = []
                continue
            current_command.append(line)
        
        if current_command:
            commands.append('\n'.join(current_command))
        
        with self.driver.session() as session:
            for command in commands:
                if command.strip():
                    try:
                        session.run(command)
                    except Exception as e:
                        logger.debug(f"Cypher command warning: {e}")
    
    def _create_minimal_sample_data(self):
        """Create minimal sample data for system validation"""
        with self.driver.session() as session:
            try:
                # Create minimal sample nodes for health validation
                session.run("""
                    MERGE (c:ControlItem {id: 'SAMPLE.001'})
                    SET c.title = 'Sample Security Control',
                        c.text = 'This is a sample security control for system validation',
                        c.level = 'Standard',
                        c.domain = 'SAMPLE',
                        c.source = 'system_initialization'
                        
                    MERGE (k:KnowledgeChunk {id: 'SAMPLE_CHUNK_001'})
                    SET k.text = 'Sample knowledge chunk for system validation',
                        k.summary = 'System validation chunk',
                        k.source = 'system_initialization'
                        
                    MERGE (t:Technology {name: 'Sample Technology'})
                    SET t.category = 'Validation'
                        
                    MERGE (e:Entity {name: 'Sample Entity'})
                    SET e.type = 'Validation'
                    
                    MERGE (c)-[:RELATED_TO {confidence: 0.9}]->(k)
                    MERGE (t)-[:IMPLEMENTS]->(c)
                    MERGE (k)-[:MENTIONS]->(e)
                """)
                logger.info("✅ Minimal sample data created for system validation")
            except Exception as e:
                logger.warning(f"⚠️ Minimal sample data creation failed: {e}")

    # Health check method for external validation
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for monitoring"""
        return self._validate_database_health()

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