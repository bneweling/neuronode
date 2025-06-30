# src/document_processing/loaders/text_loader.py
from typing import Dict, Any

class TextLoader:
    def load(self, file_path: str) -> Dict[str, Any]:
        """Load text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            "full_text": text,
            "metadata": {
                "file_size": len(text),
                "line_count": text.count('\n') + 1
            }
        }

