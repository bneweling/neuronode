from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DocumentType(Enum):
    BSI_GRUNDSCHUTZ = "bsi_grundschutz"
    BSI_C5 = "bsi_c5"
    ISO_27001 = "iso_27001"
    NIST_CSF = "nist_csf"
    WHITEPAPER = "whitepaper"
    TECHNICAL_DOC = "technical_doc"
    FAQ = "faq"
    UNKNOWN = "unknown"

class FileType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    XML = "xml"

class ControlItem(BaseModel):
    id: str
    title: str
    text: str
    level: Optional[str] = None
    domain: Optional[str] = None
    source: str
    metadata: Dict[str, Any] = {}

class KnowledgeChunk(BaseModel):
    id: str
    text: str
    summary: str
    keywords: List[str]
    entities: List[str]
    relationships: List[Dict[str, Any]]
    source: str
    page: Optional[int] = None
    metadata: Dict[str, Any] = {}

class ProcessedDocument(BaseModel):
    filename: str
    file_type: FileType
    document_type: DocumentType
    chunks: List[KnowledgeChunk]
    controls: List[ControlItem]
    metadata: Dict[str, Any]