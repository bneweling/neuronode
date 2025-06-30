# ===================================================================
# AUTO RELATIONSHIP DISCOVERY - LEGACY WRAPPER FOR LITELLM MIGRATION
# Neuronode - LiteLLM v1.72.6 Migration
# 
# MIGRATION STATUS: Legacy wrapper for seamless transition
# ===================================================================

"""
Automatic Relationship Discovery System
Entdeckt und erstellt automatisch Beziehungen zwischen Entitäten
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import re

# Legacy wrapper import - TODO: Migrate to EnhancedLiteLLMClient
try:
    from src.config.llm_config import llm_router, ModelPurpose
except ImportError:
    # Fallback for migration phase
    from src.config.llm_config_legacy import legacy_llm_router as llm_router, ModelPurpose

from src.storage.neo4j_client import Neo4jClient
from src.models.llm_models import AutoRelationshipCandidate, RelationshipType
from src.utils.llm_parser import LLMParser

logger = logging.getLogger(__name__)

@dataclass
class EntityMention:
    """Erwähnung einer Entität in einem Text"""
    entity_id: str
    entity_type: str
    text_span: str
    start_position: int
    end_position: int
    context: str
    confidence: float

class AutoRelationshipDiscovery:
    """System zur automatischen Beziehungserkennung"""
    
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.EXTRACTION)
        self.neo4j = Neo4jClient()
        self.parser = LLMParser()
        
        # Linguistische Muster für Beziehungstypen
        self.relationship_patterns = {
            RelationshipType.IMPLEMENTS: [
                r"implementiert?",
                r"umsetzt?",
                r"erfüllt?"
            ],
            RelationshipType.SUPPORTS: [
                r"unterstützt?",
                r"hilft?\s+bei",
                r"ermöglicht?"
            ],
            RelationshipType.REFERENCES: [
                r"verweist?\s+auf",
                r"siehe\s+(?:auch\s+)?",
                r"gemäß"
            ]
        }

    async def discover_relationships_in_text(self, text: str) -> List[AutoRelationshipCandidate]:
        """Entdeckt Beziehungen in einem Text"""
        logger.info(f"Discovering relationships in text ({len(text)} chars)")
        
        candidates = []
        
        # Control-IDs finden
        control_pattern = r'\b([A-Z]{2,4}\.?\d+\.?A\d+)\b'
        controls = re.findall(control_pattern, text)
        
        # Technologien finden
        tech_pattern = r'\b(Active\s+Directory|LDAP|Firewall)\b'
        technologies = re.findall(tech_pattern, text, re.IGNORECASE)
        
        # Einfache Beziehungslogik
        for control in controls:
            for tech in technologies:
                if self._are_related_in_text(text, control, tech):
                    candidate = AutoRelationshipCandidate(
                        source_entity=control,
                        target_entity=tech,
                        relationship_type=RelationshipType.IMPLEMENTS,
                        confidence=0.7,
                        evidence=f"Text mentions both {control} and {tech}",
                        source_text=text[:200]
                    )
                    candidates.append(candidate)
        
        return candidates
    
    def _are_related_in_text(self, text: str, entity1: str, entity2: str) -> bool:
        """Prüft ob zwei Entitäten im Text in Beziehung stehen"""
        # Vereinfachte Logik - prüft Nähe im Text
        pos1 = text.lower().find(entity1.lower())
        pos2 = text.lower().find(entity2.lower())
        
        if pos1 == -1 or pos2 == -1:
            return False
        
        # Wenn sie weniger als 100 Zeichen voneinander entfernt sind
        return abs(pos1 - pos2) < 100

    async def auto_create_relationships(self, candidates: List[AutoRelationshipCandidate], min_confidence: float = 0.7) -> List[str]:
        """Erstellt automatisch Beziehungen für hochvertrauenswürdige Kandidaten"""
        
        created_relationships = []
        
        high_confidence_candidates = [
            c for c in candidates 
            if c.confidence >= min_confidence
        ]
        
        logger.info(f"Auto-creating {len(high_confidence_candidates)} high-confidence relationships")
        
        for candidate in high_confidence_candidates:
            try:
                # Beziehung in Neo4j erstellen
                relationship_id = await self._create_neo4j_relationship(candidate)
                if relationship_id:
                    created_relationships.append(relationship_id)
                    logger.info(f"Created relationship: {candidate.source_entity} -> {candidate.target_entity}")
                
            except Exception as e:
                logger.error(f"Failed to create relationship {candidate.source_entity} -> {candidate.target_entity}: {e}")
        
        return created_relationships

    async def _create_neo4j_relationship(self, candidate: AutoRelationshipCandidate) -> Optional[str]:
        """Erstellt Beziehung in Neo4j"""
        
        cypher_query = """
        MATCH (source), (target)
        WHERE source.id = $source_id AND target.id = $target_id
        
        CREATE (source)-[r:AUTO_DISCOVERED {
            type: $rel_type,
            confidence: $confidence,
            evidence: $evidence,
            source_text: $source_text,
            created_at: datetime(),
            auto_generated: true
        }]->(target)
        
        RETURN elementId(r) as relationship_id
        """
        
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(
                    cypher_query,
                    source_id=candidate.source_entity,
                    target_id=candidate.target_entity,
                    rel_type=candidate.relationship_type.value,
                    confidence=candidate.confidence,
                    evidence=candidate.evidence,
                    source_text=candidate.source_text
                )
                
                record = result.single()
                return record['relationship_id'] if record else None
        except Exception as e:
            logger.error(f"Neo4j relationship creation failed: {e}")
            return None 