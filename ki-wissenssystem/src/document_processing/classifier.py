from typing import Dict, Any
from src.models.document_types import DocumentType, FileType
from src.config.llm_config import llm_router, ModelPurpose
from langchain.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class DocumentClassifier:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.CLASSIFICATION)
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("human", """Du bist ein Experte für die Klassifizierung von Compliance- und Sicherheitsdokumenten.
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
            
            Dokument-Auszug (erste 2000 Zeichen):\n\n{text}""")
        ])
    
    def _classify_with_rules(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Fallback rule-based classification when API is unavailable"""
        sample_text = text.lower()
        
        # Enhanced rule-based classification
        if any(keyword in sample_text for keyword in ["it-grundschutz", "bsi-standard", "grundschutz", "baustein"]):
            return DocumentType.BSI_GRUNDSCHUTZ
        elif any(keyword in sample_text for keyword in ["cloud computing compliance", "bsi c5", "c5-kriterien"]):
            return DocumentType.BSI_C5
        elif any(keyword in sample_text for keyword in ["iso/iec 27001", "iso 27001", "isms", "informationssicherheits-managementsystem"]):
            return DocumentType.ISO_27001
        elif any(keyword in sample_text for keyword in ["nist cybersecurity framework", "nist csf", "nist.sp.800-53"]):
            return DocumentType.NIST_CSF
        elif any(keyword in sample_text for keyword in ["whitepaper", "technical paper", "produktdokumentation"]):
            return DocumentType.WHITEPAPER
        elif any(keyword in sample_text for keyword in ["anleitung", "installation", "konfiguration", "setup", "technical documentation"]):
            return DocumentType.TECHNICAL_DOC
        elif any(keyword in sample_text for keyword in ["faq", "häufig gestellte fragen", "frequently asked"]):
            return DocumentType.FAQ
        
        # Check filename if metadata is available
        if metadata and "filename" in metadata:
            filename = metadata["filename"].lower()
            if "grundschutz" in filename:
                return DocumentType.BSI_GRUNDSCHUTZ
            elif "iso27001" in filename or "iso_27001" in filename:
                return DocumentType.ISO_27001
            elif "nist" in filename:
                return DocumentType.NIST_CSF
        
        return DocumentType.UNKNOWN
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def classify(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Classify document based on content"""
        # Use first 2000 characters for classification
        sample_text = text[:2000]
        
        # First try rule-based classification for obvious cases
        rule_result = self._classify_with_rules(sample_text, metadata)
        if rule_result != DocumentType.UNKNOWN:
            logger.info(f"Document classified using rules: {rule_result}")
            return rule_result
        
        try:
            # Use LLM for classification
            chain = self.classification_prompt | self.llm
            response = chain.invoke({"text": sample_text})
            
            classified_type = DocumentType[response.content.strip()]
            logger.info(f"Document classified using LLM: {classified_type}")
            return classified_type
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}. Using rule-based fallback.")
            # API quota exceeded or other error - use rule-based fallback
            return self._classify_with_rules(sample_text, metadata)