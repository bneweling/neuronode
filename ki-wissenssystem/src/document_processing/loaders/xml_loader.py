# src/document_processing/loaders/xml_loader.py
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import Dict, Any

class XMLLoader:
    def load(self, file_path: str) -> Dict[str, Any]:
        """Load and parse XML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as XML
        try:
            root = ET.fromstring(content)
            # Convert to text representation
            text = self._xml_to_text(root)
            metadata = {
                "root_tag": root.tag,
                "xml_valid": True
            }
        except:
            # Fallback to BeautifulSoup for invalid XML
            soup = BeautifulSoup(content, 'xml')
            text = soup.get_text(separator='\n')
            metadata = {
                "xml_valid": False
            }
        
        return {
            "full_text": text,
            "raw_xml": content,
            "metadata": metadata
        }
    
    def _xml_to_text(self, element, level=0) -> str:
        """Recursively convert XML to readable text"""
        indent = "  " * level
        text = f"{indent}{element.tag}"
        
        if element.text and element.text.strip():
            text += f": {element.text.strip()}"
        
        text += "\n"
        
        for child in element:
            text += self._xml_to_text(child, level + 1)
        
        return text