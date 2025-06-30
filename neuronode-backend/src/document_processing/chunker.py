from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config.settings import settings
import re

class SmartChunker:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        # Patterns for structured content
        self.control_pattern = re.compile(
            r'(?:^|\n)([A-Z]+[-.]?\d+(?:\.\d+)*(?:\.[A-Z]\d*)?)\s*[:\-]?\s*([^\n]+)'
        )
        self.heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
    
    def chunk_document(self, text: str, document_type: str) -> List[Dict[str, Any]]:
        """Create intelligent chunks based on document type"""
        
        if document_type in ["BSI_GRUNDSCHUTZ", "BSI_C5", "ISO_27001"]:
            return self._chunk_structured_document(text)
        else:
            return self._chunk_unstructured_document(text)
    
    def _chunk_structured_document(self, text: str) -> List[Dict[str, Any]]:
        """Chunk structured compliance documents"""
        chunks = []
        
        # Find all control items
        control_matches = list(self.control_pattern.finditer(text))
        
        if control_matches:
            for i, match in enumerate(control_matches):
                start = match.start()
                end = control_matches[i + 1].start() if i + 1 < len(control_matches) else len(text)
                
                chunk_text = text[start:end].strip()
                control_id = match.group(1)
                control_title = match.group(2)
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "control_id": control_id,
                        "control_title": control_title,
                        "chunk_type": "control"
                    }
                })
        else:
            # Fallback to standard chunking
            chunks = self._chunk_unstructured_document(text)
        
        return chunks
    
    def _chunk_unstructured_document(self, text: str) -> List[Dict[str, Any]]:
        """Chunk unstructured documents"""
        raw_chunks = self.text_splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            # Try to find section context
            section = self._find_section_context(text, chunk_text)
            
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "chunk_index": i,
                    "chunk_type": "text",
                    "section": section
                }
            })
        
        return chunks
    
    def _find_section_context(self, full_text: str, chunk_text: str) -> str:
        """Find the section/heading this chunk belongs to"""
        chunk_start = full_text.find(chunk_text)
        if chunk_start == -1:
            return "Unknown"
        
        # Look backwards for the nearest heading
        text_before = full_text[:chunk_start]
        headings = list(self.heading_pattern.finditer(text_before))
        
        if headings:
            return headings[-1].group(1)
        
        return "Main"