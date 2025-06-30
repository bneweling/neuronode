# ===================================================================
# DOCUMENT CLASSIFIER - MIGRATED TO ENHANCED LITELLM CLIENT
# Neuronode - LiteLLM v1.72.6 Migration
# 
# MIGRATION CHANGES:
# - Replaced llm_router with EnhancedLiteLLMClient
# - Used classification-primary model (Gemini Flash for speed)
# - Implemented BATCH Priorität (background classification)
# - Added structured JSON output for consistency
# - Enhanced error handling with LiteLLM exception mapping
# - Performance target: Cost-effective high-volume classification
# ===================================================================

from typing import Dict, Any
from src.models.document_types import DocumentType, FileType
import logging
import asyncio
import time

# Migration: New LiteLLM imports
from ..llm.litellm_client import (
    get_litellm_client, 
    LiteLLMClient,
    RequestPriorityLevel,
    LiteLLMExceptionMapper
)
from ..models.llm_models import LLMRequest, LLMMessage

# Legacy imports removed:
# from src.config.llm_config import llm_router, ModelPurpose
# from langchain.prompts import ChatPromptTemplate
# from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """
    Enhanced Document Classifier with LiteLLM integration
    
    MIGRATION FEATURES:
    - Uses classification-primary model (Gemini Flash)
    - BATCH priority for cost-effective background processing
    - Structured JSON output for consistency
    - Enhanced error handling with fallback mechanisms
    - Performance optimized for high-volume classification
    """
    
    def __init__(self):
        """Initialize enhanced document classifier"""
        self.litellm_client = get_litellm_client()
        
        # Classification categories with descriptions
        self.classification_categories = {
            "BSI_GRUNDSCHUTZ": "BSI IT-Grundschutz Dokumente",
            "BSI_C5": "BSI Cloud Computing Compliance Controls Katalog", 
            "ISO_27001": "ISO 27001 Standard Dokumente",
            "NIST_CSF": "NIST Cybersecurity Framework",
            "WHITEPAPER": "Technische Whitepaper von Herstellern",
            "TECHNICAL_DOC": "Technische Dokumentationen und Anleitungen",
            "FAQ": "Häufig gestellte Fragen",
            "UNKNOWN": "Nicht klassifizierbar"
        }
        
        logger.info("Enhanced DocumentClassifier initialized with LiteLLM client")
    
    def _create_classification_prompt(self, text: str) -> str:
        """Create structured classification prompt"""
        categories_text = "\n".join([
            f"- {key}: {desc}" for key, desc in self.classification_categories.items()
        ])
        
        return f"""Du bist ein Experte für die Klassifizierung von Compliance- und Sicherheitsdokumenten.
Analysiere den gegebenen Text und klassifiziere ihn in eine der folgenden Kategorien:

{categories_text}

Antworte mit einem JSON-Objekt in folgendem Format:
{{
    "category": "KATEGORIE_NAME",
    "confidence": 0.95,
    "reasoning": "Kurze Begründung der Klassifizierung"
}}

Dokument-Auszug (erste 2000 Zeichen):

{text}"""
    
    def _classify_with_rules(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Enhanced rule-based classification fallback"""
        sample_text = text.lower()
        
        # Enhanced rule-based classification with confidence scoring
        classification_rules = [
            (["it-grundschutz", "bsi-standard", "grundschutz", "baustein"], DocumentType.BSI_GRUNDSCHUTZ),
            (["cloud computing compliance", "bsi c5", "c5-kriterien"], DocumentType.BSI_C5),
            (["iso/iec 27001", "iso 27001", "isms", "informationssicherheits-managementsystem"], DocumentType.ISO_27001),
            (["nist cybersecurity framework", "nist csf", "nist.sp.800-53"], DocumentType.NIST_CSF),
            (["whitepaper", "technical paper", "produktdokumentation"], DocumentType.WHITEPAPER),
            (["anleitung", "installation", "konfiguration", "setup", "technical documentation"], DocumentType.TECHNICAL_DOC),
            (["faq", "häufig gestellte fragen", "frequently asked"], DocumentType.FAQ)
        ]
        
        # Score-based classification
        best_match = DocumentType.UNKNOWN
        best_score = 0
        
        for keywords, doc_type in classification_rules:
            score = sum(1 for keyword in keywords if keyword in sample_text)
            if score > best_score:
                best_score = score
                best_match = doc_type
        
        # Check filename if metadata is available
        if metadata and "filename" in metadata and best_match == DocumentType.UNKNOWN:
            filename = metadata["filename"].lower()
            filename_rules = [
                ("grundschutz", DocumentType.BSI_GRUNDSCHUTZ),
                ("iso27001", DocumentType.ISO_27001),
                ("iso_27001", DocumentType.ISO_27001),
                ("nist", DocumentType.NIST_CSF)
            ]
            
            for keyword, doc_type in filename_rules:
                if keyword in filename:
                    best_match = doc_type
                    break
        
        return best_match
    
    async def classify_async(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Async classification with LiteLLM"""
        sample_text = text[:2000]  # Use first 2000 characters
        
        # First try rule-based classification for obvious cases
        rule_result = self._classify_with_rules(sample_text, metadata)
        if rule_result != DocumentType.UNKNOWN:
            logger.info(f"Document classified using rules: {rule_result}")
            return rule_result
        
        try:
            # Create structured prompt for LLM classification
            classification_prompt = self._create_classification_prompt(sample_text)
            
            # === DYNAMIC MODEL RESOLUTION ===
            # Get model manager and resolve optimal model for classification task
            model_manager = await get_model_manager()
            model_config = await model_manager.get_model_for_task(
                task_type=TaskType.CLASSIFICATION,
                model_tier=ModelTier.COST_EFFECTIVE,  # Fast classification doesn't need premium models
                fallback=True
            )
            
            # Create LLM request with dynamically resolved model
            request = LLMRequest(
                messages=[
                    LLMMessage(role="user", content=classification_prompt)
                ],
                model=model_config["model"],  # DYNAMIC: Resolved from LiteLLM UI
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=1024,
                stream=False,
                # Request structured JSON response
                extra_kwargs={
                    "response_format": {"type": "json_object"}
                }
            )
            
            logger.info(f"Using dynamic model for classification: {model_config['model']} (tier: {model_config['tier']}, strategy: {model_config['selection_strategy']})")
            
            # Execute with BATCH priority (cost-effective background processing)
            response = await self.litellm_client.complete(
                request=request,
                priority=RequestPriorityLevel.BATCH,  # Background processing priority
                purpose="document_classification"  # For audit logging
            )
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.content)
                category = result.get("category", "UNKNOWN")
                confidence = result.get("confidence", 0.0)
                reasoning = result.get("reasoning", "No reasoning provided")
                
                # Convert to DocumentType enum
                if category in self.classification_categories:
                    classified_type = DocumentType[category]
                    logger.info(f"Document classified using LLM: {classified_type} (confidence: {confidence:.2f}) - {reasoning}")
                    return classified_type
                else:
                    logger.warning(f"Unknown category returned: {category}")
                    return DocumentType.UNKNOWN
                    
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response, using content as category")
                # Fallback: try to extract category from raw content
                content = response.content.strip()
                if content in self.classification_categories:
                    return DocumentType[content]
                else:
                    return DocumentType.UNKNOWN
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}. Using rule-based fallback.")
            # Map LiteLLM exceptions for better error handling
            mapped_exception = LiteLLMExceptionMapper.map_exception(e)
            logger.debug(f"Mapped exception: {type(mapped_exception).__name__}: {mapped_exception}")
            
            # Fallback to rule-based classification
            return self._classify_with_rules(sample_text, metadata)
    
    def classify(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Synchronous classification wrapper"""
        try:
            # Run async classification in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an event loop, create a new task
                import asyncio
                future = asyncio.ensure_future(self.classify_async(text, metadata))
                # Note: This won't work in nested event loops, but provides compatibility
                return DocumentType.UNKNOWN  # Fallback for nested loops
            else:
                return loop.run_until_complete(self.classify_async(text, metadata))
        except Exception as e:
            logger.error(f"Async classification failed: {e}")
            # Ultimate fallback to rule-based classification
            return self._classify_with_rules(text[:2000], metadata)


# ===================================================================
# BACKWARD COMPATIBILITY WRAPPER
# ===================================================================

class DocumentClassifierLegacy:
    """Legacy wrapper for backward compatibility during migration"""
    
    def __init__(self):
        self.enhanced_classifier = DocumentClassifier()
        logger.warning("Using legacy DocumentClassifier wrapper - migrate to DocumentClassifier")
    
    def classify(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Legacy classification method"""
        return self.enhanced_classifier.classify(text, metadata)

# Legacy alias for existing code
LegacyDocumentClassifier = DocumentClassifierLegacy