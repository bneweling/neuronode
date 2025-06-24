import asyncio
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging

from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient
from src.config.llm_config import llm_router, ModelPurpose
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class GraphGardener:
    """Continuously improves knowledge graph connections"""
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.chroma = ChromaClient()
        self.llm = llm_router.get_model(ModelPurpose.EXTRACTION)
        
        self.link_validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Experte für Compliance und IT-Sicherheit.
            
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
            REASON: <Kurze Begründung>"""),
            ("human", """Control:
            ID: {control_id}
            Title: {control_title}
            Text: {control_text}
            
            Chunk:
            {chunk_text}""")
        ])
        
        self.entity_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extrahiere Technologien und Produkte aus dem Text.
            
            Fokussiere auf:
            - Konkrete Technologien (z.B. Azure AD, AWS KMS)
            - Sicherheitstools (z.B. CrowdStrike, Sentinel)
            - Standards und Frameworks
            - Wichtige Konzepte
            
            Gib eine komma-separierte Liste zurück."""),
            ("human", "{text}")
        ])
    
    async def run_gardening_cycle(self, focus: str = "orphans"):
        """Run a complete gardening cycle"""
        
        logger.info(f"Starting gardening cycle with focus: {focus}")
        start_time = datetime.now()
        
        try:
            if focus == "orphans":
                stats = await self._process_orphan_nodes()
            elif focus == "technologies":
                stats = await self._extract_and_link_technologies()
            elif focus == "cross_reference":
                stats = await self._improve_cross_references()
            else:
                stats = {"error": "Unknown focus"}
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Gardening cycle completed in {duration:.2f}s")
            logger.info(f"Stats: {stats}")
            
            return {
                "focus": focus,
                "duration": duration,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in gardening cycle: {e}")
            return {
                "focus": focus,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_orphan_nodes(self) -> Dict[str, Any]:
        """Find and connect orphan nodes"""
        
        # Get orphan nodes
        orphans = self.neo4j.get_orphan_nodes(min_connections=2)
        logger.info(f"Found {len(orphans)} orphan nodes")
        
        stats = {
            "orphans_found": len(orphans),
            "new_relationships": 0,
            "processed": 0
        }
        
        # Process each orphan
        for orphan_data in orphans[:50]:  # Limit per cycle
            orphan = orphan_data["node"]
            
            try:
                # Find potential connections
                if "text" in orphan:
                    new_relationships = await self._find_connections_for_node(
                        orphan["id"],
                        orphan["text"][:1000],  # Limit text length
                        orphan.get("title", "")
                    )
                    
                    stats["new_relationships"] += new_relationships
                    stats["processed"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing orphan {orphan.get('id')}: {e}")
                continue
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        return stats
    
    async def _find_connections_for_node(
        self,
        node_id: str,
        node_text: str,
        node_title: str = ""
    ) -> int:
        """Find and create connections for a node"""
        
        # Search for similar content
        search_query = f"{node_title} {node_text[:200]}"
        similar_chunks = self.chroma.search_similar(
            search_query,
            n_results=10,
            filter_dict={"id": {"$ne": node_id}}  # Exclude self
        )
        
        new_relationships = 0
        
        # Evaluate each potential connection
        for chunk in similar_chunks:
            if chunk["distance"] < 0.3:  # High similarity threshold
                # Get the node from Neo4j
                target_node = self._get_node_by_id(chunk["id"])
                
                if target_node and target_node.get("id") != node_id:
                    # Validate relationship
                    relationship = await self._validate_relationship(
                        node_text,
                        node_title,
                        target_node.get("text", ""),
                        target_node.get("title", ""),
                        target_node.get("id", "")
                    )
                    
                    if relationship["type"] != "NONE" and relationship["confidence"] > 0.7:
                        # Create relationship
                        self._create_relationship(
                            node_id,
                            target_node["id"],
                            relationship["type"],
                            relationship["confidence"],
                            relationship["reason"]
                        )
                        new_relationships += 1
        
        return new_relationships
    
    async def _validate_relationship(
        self,
        source_text: str,
        source_title: str,
        target_text: str,
        target_title: str,
        target_id: str
    ) -> Dict[str, Any]:
        """Validate if a relationship should exist between two nodes"""
        
        # For control relationships, use structured validation
        if target_id and (target_id.startswith("OPS") or target_id.startswith("IDM") or "-" in target_id):
            response = await self.llm.ainvoke(
                self.link_validation_prompt.format_messages(
                    control_id=target_id,
                    control_title=target_title,
                    control_text=target_text[:500],
                    chunk_text=source_text[:500]
                )
            )
            
            # Parse response
            lines = response.content.strip().split("\n")
            result = {"type": "NONE", "confidence": 0.0, "reason": ""}
            
            for line in lines:
                if line.startswith("RELATIONSHIP:"):
                    result["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    result["confidence"] = float(line.split(":", 1)[1].strip())
                elif line.startswith("REASON:"):
                    result["reason"] = line.split(":", 1)[1].strip()
            
            return result
        
        # For other relationships, use similarity-based approach
        return {
            "type": "RELATES_TO",
            "confidence": 0.8,
            "reason": "High semantic similarity"
        }
    
    async def _extract_and_link_technologies(self) -> Dict[str, Any]:
        """Extract technology entities and create links"""
        
        stats = {
            "chunks_processed": 0,
            "technologies_found": 0,
            "links_created": 0
        }
        
        # Get recent chunks without technology links
        with self.neo4j.driver.session() as session:
            result = session.run("""
                MATCH (k:KnowledgeChunk)
                WHERE NOT (k)-[:MENTIONS]->(:Technology)
                AND k.text IS NOT NULL
                RETURN k
                LIMIT 100
            """)
            
            chunks = [dict(record["k"]) for record in result]
        
        logger.info(f"Processing {len(chunks)} chunks for technology extraction")
        
        for chunk in chunks:
            try:
                # Extract technologies
                technologies = await self._extract_technologies(chunk["text"])
                
                for tech in technologies:
                    # Create technology node and link
                    self._create_technology_link(chunk["id"], tech)
                    stats["technologies_found"] += 1
                
                stats["chunks_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing chunk {chunk['id']}: {e}")
                continue
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        return stats
    
    async def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology mentions from text"""
        
        response = await self.llm.ainvoke(
            self.entity_extraction_prompt.format_messages(text=text[:1000])
        )
        
        # Parse comma-separated list
        technologies = [
            tech.strip() 
            for tech in response.content.split(",") 
            if tech.strip()
        ]
        
        # Filter and normalize
        valid_technologies = []
        for tech in technologies:
            if len(tech) > 2 and len(tech) < 50:  # Basic validation
                valid_technologies.append(tech)
        
        return valid_technologies[:10]  # Limit number
    
    def _create_technology_link(self, chunk_id: str, technology: str):
        """Create link between chunk and technology"""
        
        with self.neo4j.driver.session() as session:
            session.run("""
                MATCH (k:KnowledgeChunk {id: $chunk_id})
                MERGE (t:Technology {name: $technology})
                MERGE (k)-[:MENTIONS]->(t)
            """, chunk_id=chunk_id, technology=technology)
    
    async def _improve_cross_references(self) -> Dict[str, Any]:
        """Improve cross-references between different standards"""
        
        stats = {
            "mappings_checked": 0,
            "mappings_created": 0,
            "mappings_strengthened": 0
        }
        
        # Find potential mapping candidates
        with self.neo4j.driver.session() as session:
            # Find controls from different sources with similar text
            result = session.run("""
                MATCH (c1:ControlItem), (c2:ControlItem)
                WHERE c1.source <> c2.source
                AND c1.id < c2.id  // Avoid duplicates
                AND NOT (c1)-[:MAPS_TO]-(c2)
                AND (
                    c1.title CONTAINS c2.title 
                    OR c2.title CONTAINS c1.title
                    OR c1.text CONTAINS c2.title
                    OR c2.text CONTAINS c1.title
                )
                RETURN c1, c2
                LIMIT 50
            """)
            
            candidates = [(dict(record["c1"]), dict(record["c2"])) for record in result]
        
        logger.info(f"Found {len(candidates)} mapping candidates")
        
        for c1, c2 in candidates:
            try:
                # Validate mapping
                is_valid_mapping = await self._validate_control_mapping(c1, c2)
                
                if is_valid_mapping:
                    self._create_control_mapping(c1["id"], c2["id"])
                    stats["mappings_created"] += 1
                
                stats["mappings_checked"] += 1
                
            except Exception as e:
                logger.error(f"Error checking mapping {c1['id']} <-> {c2['id']}: {e}")
                continue
            
            await asyncio.sleep(0.5)
        
        return stats
    
    async def _validate_control_mapping(self, control1: Dict, control2: Dict) -> bool:
        """Validate if two controls should be mapped"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Bewerte, ob diese zwei Controls äquivalent sind oder sich aufeinander beziehen.
            
            Antworte mit JA wenn:
            - Sie die gleiche Anforderung beschreiben
            - Sie sich gegenseitig ergänzen
            - Eine ist spezifischer als die andere
            
            Antworte mit NEIN wenn:
            - Sie unterschiedliche Anforderungen beschreiben
            - Sie sich widersprechen
            - Der Bezug nur oberflächlich ist
            
            Antworte nur mit JA oder NEIN."""),
            ("human", """Control 1 ({source1}):
            ID: {id1}
            Title: {title1}
            Text: {text1}
            
            Control 2 ({source2}):
            ID: {id2}
            Title: {title2}
            Text: {text2}""")
        ])
        
        response = await self.llm.ainvoke(
            prompt.format_messages(
                source1=control1["source"],
                id1=control1["id"],
                title1=control1["title"],
                text1=control1["text"][:300],
                source2=control2["source"],
                id2=control2["id"],
                title2=control2["title"],
                text2=control2["text"][:300]
            )
        )
        
        return response.content.strip().upper() == "JA"
    
    def _create_control_mapping(self, control1_id: str, control2_id: str):
        """Create mapping between two controls"""
        
        with self.neo4j.driver.session() as session:
            session.run("""
                MATCH (c1:ControlItem {id: $id1})
                MATCH (c2:ControlItem {id: $id2})
                MERGE (c1)-[:MAPS_TO]-(c2)
            """, id1=control1_id, id2=control2_id)
    
    def _get_node_by_id(self, node_id: str) -> Optional[Dict]:
        """Get node from Neo4j by ID"""
        
        with self.neo4j.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})
                RETURN n
                LIMIT 1
            """, id=node_id)
            
            record = result.single()
            return dict(record["n"]) if record else None
    
    def _create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        confidence: float,
        reason: str
    ):
        """Create relationship in Neo4j"""
        
        with self.neo4j.driver.session() as session:
            session.run(f"""
                MATCH (s {{id: $source_id}})
                MATCH (t {{id: $target_id}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.confidence = $confidence,
                    r.reason = $reason,
                    r.created_at = datetime()
            """, source_id=source_id, target_id=target_id, 
                confidence=confidence, reason=reason)
    
    async def schedule_continuous_gardening(self, interval_hours: int = 24):
        """Schedule continuous gardening cycles"""
        
        focus_rotation = ["orphans", "technologies", "cross_reference"]
        focus_index = 0
        
        while True:
            try:
                # Run gardening cycle
                focus = focus_rotation[focus_index % len(focus_rotation)]
                await self.run_gardening_cycle(focus)
                
                focus_index += 1
                
                # Wait for next cycle
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in scheduled gardening: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error