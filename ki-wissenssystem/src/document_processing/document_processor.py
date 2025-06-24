from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from datetime import datetime

from src.models.document_types import (
    DocumentType, FileType, ProcessedDocument, 
    ControlItem, KnowledgeChunk
)
from src.document_processing.loaders.pdf_loader import PDFLoader
from src.document_processing.loaders.office_loader import OfficeLoader
from src.document_processing.loaders.text_loader import TextLoader
from src.document_processing.loaders.xml_loader import XMLLoader
from src.document_processing.classifier import DocumentClassifier
from src.extractors.structured_extractor import StructuredExtractor
from src.extractors.unstructured_processor import UnstructuredProcessor
from src.extractors.quality_validator import QualityValidator
from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient

import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processing pipeline"""
    
    def __init__(self):
        # Initialize loaders
        self.loaders = {
            FileType.PDF: PDFLoader(),
            FileType.DOCX: OfficeLoader(),
            FileType.XLSX: OfficeLoader(),
            FileType.PPTX: OfficeLoader(),
            FileType.TXT: TextLoader(),
            FileType.XML: XMLLoader()
        }
        
        # Initialize processors
        self.classifier = DocumentClassifier()
        self.structured_extractor = StructuredExtractor()
        self.unstructured_processor = UnstructuredProcessor()
        self.validator = QualityValidator()
        
        # Initialize storage
        self.neo4j = Neo4jClient()
        self.chroma = ChromaClient()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_document(
        self, 
        file_path: str,
        force_type: Optional[DocumentType] = None,
        validate: bool = True
    ) -> ProcessedDocument:
        """Process a document through the entire pipeline"""
        
        file_path = Path(file_path)
        file_type = self._detect_file_type(file_path)
        
        logger.info(f"Processing {file_path.name} (type: {file_type})")
        
        # Load document
        raw_content = await self._load_document(file_path, file_type)
        
        # Classify document type
        if force_type:
            document_type = force_type
        else:
            document_type = await self._classify_document(raw_content["full_text"])
        
        logger.info(f"Document classified as: {document_type}")
        
        # Process based on document type
        if document_type in [DocumentType.BSI_GRUNDSCHUTZ, DocumentType.BSI_C5, 
                            DocumentType.ISO_27001, DocumentType.NIST_CSF]:
            controls, chunks = await self._process_structured_document(
                raw_content, document_type, str(file_path), validate
            )
        else:
            controls = []
            chunks = await self._process_unstructured_document(
                raw_content, document_type, str(file_path)
            )
        
        # Store in databases
        await self._store_results(controls, chunks, document_type)
        
        # Create processed document
        processed_doc = ProcessedDocument(
            filename=file_path.name,
            file_type=file_type,
            document_type=document_type,
            chunks=chunks,
            controls=controls,
            metadata={
                "file_hash": self._calculate_file_hash(file_path),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_metadata": raw_content.get("metadata", {})
            }
        )
        
        logger.info(f"Successfully processed {file_path.name}: "
                   f"{len(controls)} controls, {len(chunks)} chunks")
        
        return processed_doc
    
    def _detect_file_type(self, file_path: Path) -> FileType:
        """Detect file type from extension"""
        extension = file_path.suffix.lower().lstrip('.')
        
        mapping = {
            'pdf': FileType.PDF,
            'docx': FileType.DOCX,
            'xlsx': FileType.XLSX,
            'pptx': FileType.PPTX,
            'txt': FileType.TXT,
            'xml': FileType.XML
        }
        
        return mapping.get(extension, FileType.TXT)
    
    async def _load_document(self, file_path: Path, file_type: FileType) -> Dict[str, Any]:
        """Load document using appropriate loader"""
        loader = self.loaders.get(file_type)
        if not loader:
            raise ValueError(f"No loader available for file type: {file_type}")
        
        # Load in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        if file_type == FileType.PDF:
            content = await loop.run_in_executor(
                self.executor, loader.load, str(file_path)
            )
        elif file_type == FileType.DOCX:
            content = await loop.run_in_executor(
                self.executor, loader.load_docx, str(file_path)
            )
        elif file_type == FileType.XLSX:
            content = await loop.run_in_executor(
                self.executor, loader.load_xlsx, str(file_path)
            )
        elif file_type == FileType.PPTX:
            content = await loop.run_in_executor(
                self.executor, loader.load_pptx, str(file_path)
            )
        elif file_type == FileType.TXT:
            content = await loop.run_in_executor(
                self.executor, loader.load, str(file_path)
            )
        elif file_type == FileType.XML:
            content = await loop.run_in_executor(
                self.executor, loader.load, str(file_path)
            )
        
        return content
    
    async def _classify_document(self, text: str) -> DocumentType:
        """Classify document type"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.classifier.classify, text
        )
    
    async def _process_structured_document(
        self, 
        content: Dict[str, Any], 
        document_type: DocumentType,
        source: str,
        validate: bool
    ) -> Tuple[List[ControlItem], List[KnowledgeChunk]]:
        """Process structured compliance document"""
        
        loop = asyncio.get_event_loop()
        
        # Extract controls
        controls = await loop.run_in_executor(
            self.executor,
            self.structured_extractor.extract_controls,
            content["full_text"],
            document_type,
            source
        )
        
        # Validate if required
        if validate and controls:
            validated_controls, reports = await loop.run_in_executor(
                self.executor,
                self.validator.validate_controls,
                controls,
                document_type.value
            )
            
            # Log validation results
            failed_validations = [r for r in reports if not r["valid"]]
            if failed_validations:
                logger.warning(f"Validation failed for {len(failed_validations)} controls")
            
            controls = validated_controls
        
        # Also create chunks for vector search
        chunks = await loop.run_in_executor(
            self.executor,
            self.unstructured_processor.process_document,
            content["full_text"],
            source,
            document_type.value
        )
        
        # Link chunks to controls
        if controls:
            control_list = [{"id": c.id, "title": c.title} for c in controls]
            chunks = await loop.run_in_executor(
                self.executor,
                self.unstructured_processor.enrich_with_entity_linking,
                chunks,
                control_list
            )
        
        return controls, chunks
    
    async def _process_unstructured_document(
        self,
        content: Dict[str, Any],
        document_type: DocumentType,
        source: str
    ) -> List[KnowledgeChunk]:
        """Process unstructured document"""
        
        loop = asyncio.get_event_loop()
        
        chunks = await loop.run_in_executor(
            self.executor,
            self.unstructured_processor.process_document,
            content["full_text"],
            source,
            document_type.value,
            content.get("metadata", {})
        )
        
        return chunks
    
    async def _store_results(
        self,
        controls: List[ControlItem],
        chunks: List[KnowledgeChunk],
        document_type: DocumentType
    ):
        """Store results in Neo4j and ChromaDB"""
        
        loop = asyncio.get_event_loop()
        
        # Store controls in Neo4j
        for control in controls:
            await loop.run_in_executor(
                self.executor,
                self.neo4j.create_control_item,
                control
            )
        
        # Store chunks in both Neo4j and ChromaDB
        collection_name = "compliance" if document_type in [
            DocumentType.BSI_GRUNDSCHUTZ, DocumentType.BSI_C5,
            DocumentType.ISO_27001, DocumentType.NIST_CSF
        ] else "technical"
        
        for chunk in chunks:
            # Store in Neo4j
            await loop.run_in_executor(
                self.executor,
                self.neo4j.create_knowledge_chunk,
                chunk
            )
            
            # Store in ChromaDB
            await loop.run_in_executor(
                self.executor,
                self.chroma.add_chunk,
                chunk.dict(),
                collection_name
            )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def process_batch(
        self,
        file_paths: List[str],
        max_concurrent: int = 3
    ) -> List[ProcessedDocument]:
        """Process multiple documents concurrently"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(file_path):
            async with semaphore:
                try:
                    return await self.process_document(file_path)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    return None
        
        tasks = [process_with_semaphore(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks)
        
        # Filter out failed processes
        return [r for r in results if r is not None]
    
    def close(self):
        """Clean up resources"""
        self.neo4j.close()
        self.executor.shutdown(wait=True)