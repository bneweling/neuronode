# ===================================================================
# STRUCTURED EXTRACTOR - LEGACY WRAPPER FOR LITELLM MIGRATION
# Neuronode - LiteLLM v1.72.6 Migration
# 
# MIGRATION STATUS:
# - Core RAG Pipeline: 100% migrated to LiteLLM
# - Legacy Wrapper: Maintains compatibility during transition
# - Future Migration: To be migrated to EnhancedLiteLLMClient
# ===================================================================

from typing import List, Dict, Any, Optional, Tuple
# Legacy wrapper import - TODO: Migrate to EnhancedLiteLLMClient
try:
    from src.config.llm_config import llm_router, ModelPurpose
except ImportError:
    # Fallback for migration phase
    from src.config.llm_config_legacy import legacy_llm_router as llm_router, ModelPurpose
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
import re
import logging

from src.config.exceptions import (
    ErrorCode, ProcessingPipelineError, LLMServiceError
)
from src.utils.error_handler import error_handler, handle_exceptions
from src.models.document_types import DocumentType, ControlItem

logger = logging.getLogger(__name__)

class ExtractedControl(BaseModel):
    """Schema for extracted control items"""
    id: str = Field(description="Control ID (e.g., OPS.1.1.A1, C5-01)")
    title: str = Field(description="Control title")
    text: str = Field(description="Full control description/requirements")
    level: Optional[str] = Field(description="Control level (e.g., Basis, Standard, Hoch)")
    domain: Optional[str] = Field(description="Domain/Category (e.g., OPS, IDM)")
    related_controls: List[str] = Field(default_factory=list, description="IDs of related controls")

class ExtractedControlSet(BaseModel):
    """Set of extracted controls"""
    controls: List[ExtractedControl]
    document_metadata: Dict[str, Any] = Field(default_factory=dict)

class StructuredExtractor:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.EXTRACTION)
        self.output_parser = PydanticOutputParser(pydantic_object=ExtractedControlSet)
        
        # Specific patterns for different standards
        self.patterns = {
            DocumentType.BSI_GRUNDSCHUTZ: {
                "control": re.compile(r'([A-Z]{3,4}\.\d+(?:\.\d+)*\.A\d+)\s*([^\n]+)'),
                "level": re.compile(r'\((Basis|Standard|Hoch)\)'),
                "domain": re.compile(r'^([A-Z]{3,4})')
            },
            DocumentType.BSI_C5: {
                "control": re.compile(r'([A-Z]{2,3}-\d{2})\s*([^\n]+)'),
                "domain": re.compile(r'^([A-Z]{2,3})')
            }
        }
        
        self.extraction_prompts = {
            DocumentType.BSI_GRUNDSCHUTZ: self._create_bsi_gs_prompt(),
            DocumentType.BSI_C5: self._create_bsi_c5_prompt(),
            DocumentType.ISO_27001: self._create_iso_prompt(),
            DocumentType.NIST_CSF: self._create_nist_prompt()
        }
    
    def _create_bsi_gs_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für BSI IT-Grundschutz. 
            Extrahiere alle Sicherheitsanforderungen aus dem gegebenen Text.
            
            Jede Anforderung hat:
            - Eine ID (z.B. SYS.1.1.A1, OPS.1.1.A5)
            - Einen Titel
            - Eine Beschreibung der Anforderung
            - Ein Level (Basis, Standard, oder Hoch)
            - Eine Domäne (der erste Teil der ID, z.B. SYS, OPS, APP)
            
            {format_instructions}
            
            Achte darauf, den vollständigen Text der Anforderung zu erfassen.
            
            Text: {text}""")
        ])
    
    def _create_bsi_c5_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für BSI C5 (Cloud Computing Compliance Controls).
            Extrahiere alle Kontrollen aus dem gegebenen Text.
            
            Jede Kontrolle hat:
            - Eine ID (z.B. OPS-01, IDM-09)
            - Einen Titel
            - Eine detaillierte Beschreibung
            - Eine Domäne (z.B. OPS, IDM, PS)
            
            {format_instructions}
            
            Erfasse auch Hinweise auf verwandte Kontrollen oder Standards.
            
            Text: {text}""")
        ])
    
    def _create_iso_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für ISO 27001/27002.
            Extrahiere alle Controls aus dem gegebenen Text.
            
            Jedes Control hat:
            - Eine Nummer (z.B. 5.1.1, A.8.1.1)
            - Einen Titel
            - Die Control-Beschreibung
            - Die Kategorie/Domäne
            
            {format_instructions}
            
            Text: {text}""")
        ])
    
    def _create_nist_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für das NIST Cybersecurity Framework.
            Extrahiere alle Controls/Subcategories aus dem Text.
            
            Jedes Element hat:
            - Eine ID (z.g. ID.AM-1, PR.AC-4)
            - Einen Titel/Namen
            - Die Beschreibung
            - Die Function (Identify, Protect, Detect, Respond, Recover)
            - Die Category
            
            {format_instructions}
            
            Text: {text}""")
        ])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_controls(self, text: str, document_type: DocumentType, source: str) -> List[ControlItem]:
        """Extract controls from structured compliance documents"""
        
        # First try regex-based extraction for known formats
        regex_controls = self._extract_with_regex(text, document_type)
        
        # Then use LLM for comprehensive extraction
        llm_controls = self._extract_with_llm(text, document_type)
        
        # Merge and deduplicate results
        all_controls = self._merge_controls(regex_controls, llm_controls, source)
        
        logger.info(f"Extracted {len(all_controls)} controls from {source}")
        return all_controls
    
    def _extract_with_regex(self, text: str, document_type: DocumentType) -> List[Dict[str, Any]]:
        """Fast regex-based extraction for known patterns"""
        controls = []
        
        if document_type not in self.patterns:
            return controls
        
        pattern_set = self.patterns[document_type]
        control_pattern = pattern_set["control"]
        
        # Split text into sections
        sections = re.split(r'\n(?=[A-Z]{2,4}[-.]?\d+)', text)
        
        for section in sections:
            match = control_pattern.search(section)
            if match:
                control_id = match.group(1)
                control_title = match.group(2).strip()
                
                # Extract level if applicable
                level = None
                if "level" in pattern_set:
                    level_match = pattern_set["level"].search(section)
                    if level_match:
                        level = level_match.group(1)
                
                # Extract domain
                domain = None
                if "domain" in pattern_set:
                    domain_match = pattern_set["domain"].match(control_id)
                    if domain_match:
                        domain = domain_match.group(1)
                
                controls.append({
                    "id": control_id,
                    "title": control_title,
                    "text": section.strip(),
                    "level": level,
                    "domain": domain
                })
        
        return controls
    
    def _extract_with_llm(self, text: str, document_type: DocumentType) -> List[Dict[str, Any]]:
        """LLM-based extraction for comprehensive parsing"""
        if document_type not in self.extraction_prompts:
            return []
        
        prompt = self.extraction_prompts[document_type]
        
        # Process in chunks if text is too long
        max_chunk_size = 4000
        chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size-500)]
        
        all_controls = []
        
        for chunk in chunks:
            chain = prompt | self.llm | self.output_parser
            try:
                result = chain.invoke({
                    "text": chunk,
                    "format_instructions": self.output_parser.get_format_instructions()
                })
                
                for control in result.controls:
                    all_controls.append(control.dict())
                    
            except LLMServiceError as e:
                error_handler.log_error(e, {"chunk_length": len(chunk), "document_type": document_type.value})
                continue  # Skip this chunk but continue processing
            except Exception as e:
                structured_error = ProcessingPipelineError(
                    f"Failed to extract controls from text chunk: {str(e)}",
                    ErrorCode.EXTRACTION_FAILED,
                    {"chunk_length": len(chunk), "document_type": document_type.value},
                    cause=e
                )
                error_handler.log_error(structured_error)
                continue  # Skip this chunk but continue processing
        
        return all_controls
    
    def _merge_controls(self, regex_controls: List[Dict], llm_controls: List[Dict], source: str) -> List[ControlItem]:
        """Merge and deduplicate controls from different extraction methods"""
        merged = {}
        
        # Add regex controls first (they're usually more accurate for IDs)
        for control in regex_controls:
            control_id = control["id"]
            merged[control_id] = control
        
        # Add/update with LLM controls
        for control in llm_controls:
            control_id = control["id"]
            if control_id in merged:
                # Merge information, preferring LLM for detailed text
                merged[control_id]["text"] = control.get("text", merged[control_id]["text"])
                if "related_controls" in control:
                    merged[control_id]["related_controls"] = control["related_controls"]
            else:
                merged[control_id] = control
        
        # Convert to ControlItem objects
        control_items = []
        for control_data in merged.values():
            control_items.append(ControlItem(
                id=control_data["id"],
                title=control_data["title"],
                text=control_data["text"],
                level=control_data.get("level"),
                domain=control_data.get("domain"),
                source=source,
                metadata={
                    "related_controls": control_data.get("related_controls", [])
                }
            ))
        
        return control_items