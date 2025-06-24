from typing import List, Dict, Any, Tuple
from src.models.document_types import KnowledgeChunk
from src.config.llm_config import llm_router, ModelPurpose
from src.document_processing.chunker import SmartChunker
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
import uuid
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ChunkAnalysis(BaseModel):
    """Analysis result for a text chunk"""
    summary: str = Field(description="Concise summary of the chunk's content")
    keywords: List[str] = Field(description="Key technical terms and concepts")
    entities: List[str] = Field(description="Technologies, products, standards mentioned")
    topics: List[str] = Field(description="Main topics covered")
    potential_relations: List[Dict[str, str]] = Field(
        description="Potential relationships to compliance requirements",
        default_factory=list
    )

class UnstructuredProcessor:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.EXTRACTION)
        self.chunker = SmartChunker()
        self.output_parser = PydanticOutputParser(pydantic_object=ChunkAnalysis)
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Experte für IT-Sicherheit und Compliance.
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
            
            {format_instructions}"""),
            ("human", "Text zum Analysieren:\n\n{text}")
        ])
        
        self.entity_linking_prompt = ChatPromptTemplate.from_messages([
            ("system", """Gegeben ist ein Text-Chunk und eine Liste von bekannten Compliance-Controls.
            Identifiziere, welche Controls dieser Text möglicherweise implementiert oder referenziert.
            
            Bekannte Controls:
            {known_controls}
            
            Antworte mit einer Liste von Beziehungen im Format:
            - control_id: Die ID des relevanten Controls
            - relationship: Art der Beziehung (IMPLEMENTS, SUPPORTS, REFERENCES)
            - confidence: Konfidenz-Score (0.0-1.0)
            - reason: Kurze Begründung"""),
            ("human", "Text-Chunk:\n{chunk_text}")
        ])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_document(
        self, 
        text: str, 
        source: str,
        document_type: str,
        metadata: Dict[str, Any] = None
    ) -> List[KnowledgeChunk]:
        """Process unstructured document into enriched knowledge chunks"""
        
        # Create chunks
        raw_chunks = self.chunker.chunk_document(text, document_type)
        
        # Process each chunk
        knowledge_chunks = []
        for i, raw_chunk in enumerate(raw_chunks):
            try:
                chunk_id = f"{source}_{i}_{uuid.uuid4().hex[:8]}"
                
                # Analyze chunk
                analysis = self._analyze_chunk(raw_chunk["text"])
                
                # Create knowledge chunk
                knowledge_chunk = KnowledgeChunk(
                    id=chunk_id,
                    text=raw_chunk["text"],
                    summary=analysis.summary,
                    keywords=analysis.keywords,
                    entities=analysis.entities,
                    relationships=self._format_relationships(analysis.potential_relations),
                    source=source,
                    page=raw_chunk.get("metadata", {}).get("page"),
                    metadata={
                        **raw_chunk.get("metadata", {}),
                        "topics": analysis.topics,
                        "document_type": document_type,
                        **(metadata or {})
                    }
                )
                
                knowledge_chunks.append(knowledge_chunk)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                # Create basic chunk without analysis
                knowledge_chunks.append(KnowledgeChunk(
                    id=chunk_id,
                    text=raw_chunk["text"],
                    summary="",
                    keywords=[],
                    entities=[],
                    relationships=[],
                    source=source,
                    metadata=raw_chunk.get("metadata", {})
                ))
        
        logger.info(f"Processed {len(knowledge_chunks)} chunks from {source}")
        return knowledge_chunks
    
    def _analyze_chunk(self, chunk_text: str) -> ChunkAnalysis:
        """Analyze a single chunk with LLM"""
        chain = self.analysis_prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "text": chunk_text[:2000],  # Limit text length
            "format_instructions": self.output_parser.get_format_instructions()
        })
        
        return result
    
    def _format_relationships(self, potential_relations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format relationships for storage"""
        formatted = []
        for rel in potential_relations:
            formatted.append({
                "type": rel.get("relation_type", "RELATES_TO"),
                "target_id": rel.get("target"),
                "confidence": float(rel.get("confidence", 0.5)),
                "reason": rel.get("reason", "")
            })
        return formatted
    
    def enrich_with_entity_linking(
        self, 
        chunks: List[KnowledgeChunk], 
        known_controls: List[Dict[str, str]]
    ) -> List[KnowledgeChunk]:
        """Enrich chunks by linking them to known controls"""
        
        # Format known controls for prompt
        controls_text = "\n".join([
            f"- {c['id']}: {c['title']}" 
            for c in known_controls[:50]  # Limit to prevent prompt overflow
        ])
        
        enriched_chunks = []
        for chunk in chunks:
            try:
                # Get entity linking suggestions
                linking_result = self._get_entity_links(chunk.text, controls_text)
                
                # Add high-confidence links to relationships
                for link in linking_result:
                    if link["confidence"] > 0.7:
                        chunk.relationships.append({
                            "type": link["relationship"],
                            "target_id": link["control_id"],
                            "confidence": link["confidence"],
                            "reason": link["reason"]
                        })
                
                enriched_chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Error enriching chunk {chunk.id}: {e}")
                enriched_chunks.append(chunk)
        
        return enriched_chunks
    
    def _get_entity_links(self, chunk_text: str, known_controls: str) -> List[Dict[str, Any]]:
        """Get entity linking suggestions from LLM"""
        chain = self.entity_linking_prompt | self.llm
        
        response = chain.invoke({
            "chunk_text": chunk_text[:1500],
            "known_controls": known_controls
        })
        
        # Parse response
        links = []
        try:
            # Simple parsing - in production, use structured output
            lines = response.content.strip().split("\n")
            current_link = {}
            
            for line in lines:
                if line.startswith("- control_id:"):
                    if current_link:
                        links.append(current_link)
                    current_link = {"control_id": line.split(":", 1)[1].strip()}
                elif line.startswith("- relationship:"):
                    current_link["relationship"] = line.split(":", 1)[1].strip()
                elif line.startswith("- confidence:"):
                    current_link["confidence"] = float(line.split(":", 1)[1].strip())
                elif line.startswith("- reason:"):
                    current_link["reason"] = line.split(":", 1)[1].strip()
            
            if current_link:
                links.append(current_link)
                
        except Exception as e:
            logger.error(f"Error parsing entity links: {e}")
        
        return links