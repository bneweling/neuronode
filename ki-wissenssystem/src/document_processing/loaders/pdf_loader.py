from pypdf import PdfReader
from typing import List, Dict, Any
import re

class PDFLoader:
    def __init__(self):
        self.page_pattern = re.compile(r'^\d+$')
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """Load PDF and extract text with metadata"""
        reader = PdfReader(file_path)
        
        pages = []
        metadata = {
            "num_pages": len(reader.pages),
            "pdf_metadata": reader.metadata
        }
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            # Clean up text
            text = self._clean_text(text)
            
            pages.append({
                "page_num": i + 1,
                "text": text,
                "metadata": {
                    "page_size": (page.mediabox.width, page.mediabox.height)
                }
            })
        
        return {
            "pages": pages,
            "metadata": metadata,
            "full_text": "\n\n".join([p["text"] for p in pages])
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers if standalone
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()