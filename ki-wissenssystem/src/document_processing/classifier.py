from typing import Dict, Any
from src.models.document_types import DocumentType, FileType
from src.config.llm_config import llm_router, ModelPurpose
from langchain.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

class DocumentClassifier:
    def __init__(self):
        self.llm = llm_router.get_model(ModelPurpose.CLASSIFICATION)
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """Du bist ein Experte für die Klassifizierung von Compliance- und Sicherheitsdokumenten.
            Analysiere den gegebenen Text und klassifiziere ihn in eine der folgenden Kategorien:
            
            - BSI_GRUNDSCHUTZ: BSI IT-Grundschutz Dokumente
            - BSI_C5: BSI Cloud Computing Compliance Controls Katalog
            - ISO_27001: ISO 27001 Standard Dokumente
            - NIST_CSF: NIST Cybersecurity Framework
            - WHITEPAPER: Technische Whitepaper von Herstellern
            - TECHNICAL_DOC: Technische Dokumentationen und Anleitungen
            - FAQ: Häufig gestellte Fragen
            - UNKNOWN: Nicht klassifizierbar
            
            Antworte NUR mit dem Kategorienamen."""),
            ("human", "Dokument-Auszug (erste 2000 Zeichen):\n\n{text}")
        ])
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def classify(self, text: str, metadata: Dict[str, Any] = None) -> DocumentType:
        """Classify document based on content"""
        # Use first 2000 characters for classification
        sample_text = text[:2000]
        
        # Check for obvious patterns first
        if "IT-Grundschutz" in sample_text or "BSI-Standard" in sample_text:
            return DocumentType.BSI_GRUNDSCHUTZ
        elif "Cloud Computing Compliance" in sample_text or "BSI C5" in sample_text:
            return DocumentType.BSI_C5
        elif "ISO/IEC 27001" in sample_text or "ISO 27001" in sample_text:
            return DocumentType.ISO_27001
        elif "NIST Cybersecurity Framework" in sample_text or "NIST CSF" in sample_text:
            return DocumentType.NIST_CSF
        
        # Use LLM for classification
        chain = self.classification_prompt | self.llm
        response = chain.invoke({"text": sample_text})
        
        try:
            return DocumentType[response.content.strip()]
        except KeyError:
            return DocumentType.UNKNOWN