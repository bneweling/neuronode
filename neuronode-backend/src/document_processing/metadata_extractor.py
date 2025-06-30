"""
Document Metadata Extractor
Extrahiert Metadaten aus Dokumenten für Document-Knoten
"""
import hashlib
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import aiofiles

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PyPDF2 nicht verfügbar - PDF-Metadaten werden nicht extrahiert")

try:
    from docx import Document as DocxDocument
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    logger.warning("python-docx nicht verfügbar - DOCX-Metadaten werden nicht extrahiert")

class DocumentMetadataExtractor:
    """Extrahiert Metadaten aus verschiedenen Dokumenttypen"""
    
    def __init__(self):
        self.standard_patterns = {
            'BSI': r'BSI.*Grundschutz.*(\d{4})',
            'ISO': r'ISO.*(\d+):(\d{4})',
            'NIST': r'NIST.*(\w+).*v?(\d+\.?\d*)',
            'CIS': r'CIS.*Controls.*v?(\d+\.?\d*)'
        }
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Hauptmethode: Extrahiert alle Metadaten"""
        file_path = Path(file_path)
        
        # Basis-Metadaten
        metadata = {
            'filename': file_path.name,
            'hash': await self._calculate_hash(file_path),
            'file_size': file_path.stat().st_size,
            'document_type': self._detect_document_type(file_path),
            'source_url': None,
            'author': None,
            'page_count': 0
        }
        
        # Standard-spezifische Metadaten
        standard_info = self._extract_standard_info(file_path.name)
        metadata.update(standard_info)
        
        # Format-spezifische Metadaten
        if file_path.suffix.lower() == '.pdf' and PDF_SUPPORT:
            pdf_metadata = await self._extract_pdf_metadata(file_path)
            metadata.update(pdf_metadata)
        elif file_path.suffix.lower() in ['.docx', '.doc'] and DOCX_SUPPORT:
            doc_metadata = await self._extract_docx_metadata(file_path)
            metadata.update(doc_metadata)
        
        return metadata
    
    async def _calculate_hash(self, file_path: Path) -> str:
        """SHA-256 Hash des Dokuments"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"Hash-Berechnung fehlgeschlagen für {file_path}: {e}")
            return hashlib.sha256(str(file_path).encode()).hexdigest()  # Fallback
    
    def _detect_document_type(self, file_path: Path) -> str:
        """Erkennt Dokumenttyp anhand Dateiname"""
        filename = file_path.name.lower()
        
        if any(word in filename for word in ['grundschutz', 'bsi']):
            return 'BSI_GRUNDSCHUTZ'
        elif 'iso' in filename and '27001' in filename:
            return 'ISO_27001'
        elif 'nist' in filename:
            return 'NIST_FRAMEWORK'
        elif 'cis' in filename:
            return 'CIS_CONTROLS'
        else:
            return 'UNKNOWN'
    
    def _extract_standard_info(self, filename: str) -> Dict[str, Any]:
        """Extrahiert Standard-Name und Version"""
        result = {
            'standard_name': 'Unknown',
            'standard_version': 'Unknown'
        }
        
        for standard, pattern in self.standard_patterns.items():
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                result['standard_name'] = standard
                if standard == 'ISO':
                    result['standard_version'] = f"{match.group(1)}:{match.group(2)}"
                else:
                    result['standard_version'] = match.group(1)
                break
        
        return result
    
    async def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """PDF-spezifische Metadaten"""
        metadata = {'page_count': 0, 'author': None}
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                # PyPDF2 requires a file-like object, so we use BytesIO
                from io import BytesIO
                pdf_reader = PyPDF2.PdfReader(BytesIO(content))
                metadata['page_count'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    metadata['author'] = pdf_reader.metadata.get('/Author', None)
        except Exception as e:
            logger.warning(f"PDF-Metadaten konnten nicht extrahiert werden: {e}")
        
        return metadata
    
    async def _extract_docx_metadata(self, file_path: Path) -> Dict[str, Any]:
        """DOCX-spezifische Metadaten"""
        metadata = {'page_count': 0, 'author': None}
        
        try:
            doc = DocxDocument(file_path)
            metadata['page_count'] = len(doc.paragraphs) // 50  # Grobe Schätzung
            
            if doc.core_properties.author:
                metadata['author'] = doc.core_properties.author
        except Exception as e:
            logger.warning(f"DOCX-Metadaten konnten nicht extrahiert werden: {e}")
        
        return metadata 