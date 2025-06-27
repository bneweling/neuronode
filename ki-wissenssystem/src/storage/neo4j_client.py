from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.models.document_types import ControlItem, KnowledgeChunk
import logging

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
    
    def close(self):
        self.driver.close()