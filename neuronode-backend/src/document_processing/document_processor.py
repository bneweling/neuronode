from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from datetime import datetime
import aiofiles

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
from src.document_processing.metadata_extractor import DocumentMetadataExtractor

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
        self.metadata_extractor = DocumentMetadataExtractor()
        
        # Initialize storage
        self.neo4j = Neo4jClient()
        self.chroma = ChromaClient()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_document(
        self, 
        file_path: str,
        force_type: Optional[DocumentType] = None,
        validate: bool = True,
        status_callback: Optional[Callable] = None,
        task_id: Optional[str] = None
    ) -> ProcessedDocument:
        """Process a document through the entire pipeline"""
        
        file_path = Path(file_path)
        file_type = self._detect_file_type(file_path)
        
        logger.info(f"Processing {file_path.name} (type: {file_type})")
        
        # Callback: Document loading started
        if status_callback:
            status_callback(task_id, "loading", 0.1, {"step": "document_loading", "filename": file_path.name})
        
        # Load document
        raw_content = await self._load_document(file_path, file_type)
        
        # Callback: Document loaded, starting classification
        if status_callback:
            status_callback(task_id, "classifying", 0.2, {"step": "document_classification", "text_length": len(raw_content.get("full_text", ""))})
        
        # Classify document type
        if force_type:
            document_type = force_type
        else:
            document_type = await self._classify_document(raw_content["full_text"])
        
        logger.info(f"Document classified as: {document_type}")
        
        # Callback: Classification complete, starting extraction
        if status_callback:
            status_callback(task_id, "extracting", 0.4, {"step": "content_extraction", "document_type": document_type.value})
        
        # Process based on document type
        if document_type in [DocumentType.BSI_GRUNDSCHUTZ, DocumentType.BSI_C5, 
                            DocumentType.ISO_27001, DocumentType.NIST_CSF]:
            controls, chunks = await self._process_structured_document(
                raw_content, document_type, str(file_path), validate, status_callback, task_id
            )
        else:
            controls = []
            chunks = await self._process_unstructured_document(
                raw_content, document_type, str(file_path), status_callback, task_id
            )
        
        # Callback: Processing complete, starting storage
        if status_callback:
            status_callback(task_id, "storing", 0.8, {
                "step": "graph_storage", 
                "num_controls": len(controls), 
                "num_chunks": len(chunks)
            })
        
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
                "file_hash": await self._calculate_file_hash(file_path),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_metadata": raw_content.get("metadata", {})
            }
        )
        
        # Callback: Processing completed
        if status_callback:
            status_callback(task_id, "completed", 1.0, {
                "step": "processing_completed",
                "filename": file_path.name,
                "document_type": document_type.value,
                "num_controls": len(controls),
                "num_chunks": len(chunks),
                "processing_timestamp": processed_doc.metadata["processing_timestamp"]
            })
        
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
        validate: bool,
        status_callback: Optional[Callable] = None,
        task_id: Optional[str] = None
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
        
        # Callback: Controls extracted, starting validation
        if status_callback:
            status_callback(task_id, "validating", 0.5, {
                "step": "control_validation", 
                "num_controls_extracted": len(controls)
            })
        
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
        
        # Callback: Validation complete, starting chunking
        if status_callback:
            status_callback(task_id, "chunking", 0.6, {
                "step": "smart_chunking", 
                "num_validated_controls": len(controls)
            })
        
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
        source: str,
        status_callback: Optional[Callable] = None,
        task_id: Optional[str] = None
    ) -> List[KnowledgeChunk]:
        """Process unstructured document"""
        
        loop = asyncio.get_event_loop()
        
        # Callback: Starting chunking for unstructured document
        if status_callback:
            status_callback(task_id, "chunking", 0.6, {
                "step": "unstructured_chunking", 
                "document_type": document_type.value
            })
        
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
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while True:
                byte_block = await f.read(4096)
                if not byte_block:
                    break
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
    
    async def process_document_with_metadata(self, file_path: str) -> Dict[str, Any]:
        """Erweiterte Dokumentverarbeitung mit Document-Knoten"""
        
        # 1. Metadaten extrahieren
        logger.info(f"Extracting metadata for document: {Path(file_path).name}")
        metadata = await self.metadata_extractor.extract_metadata(file_path)
        
        # 2. Duplikat-Prüfung
        existing_doc = self.neo4j.find_document_by_hash(metadata['hash'])
        if existing_doc:
            logger.info(f"Document already processed: {existing_doc['filename']}")
            return {
                'status': 'duplicate',
                'document_id': existing_doc['id'],
                'message': f"Dokument bereits verarbeitet am {existing_doc['processed_at']}"
            }
        
        # 3. Document-Knoten erstellen
        logger.info("Creating document node in graph database")
        document_id = self.neo4j.create_document_node(metadata)
        
        # 4. Inhalt verarbeiten (bestehende Logik)
        processed_doc = await self.process_document(file_path)
        
        # 5. Inhalt mit Document verknüpfen
        for control in processed_doc.controls:
            self.neo4j.link_document_to_content(document_id, control.id, "ControlItem")
        
        for chunk in processed_doc.chunks:
            self.neo4j.link_document_to_content(document_id, chunk.id, "KnowledgeChunk")
        
        # 6. Versionierung prüfen
        await self._check_and_link_versions(document_id, metadata)
        
        return {
            'status': 'success',
            'document_id': document_id,
            'metadata': metadata,
            'controls_count': len(processed_doc.controls),
            'chunks_count': len(processed_doc.chunks)
        }
    
    async def _check_and_link_versions(self, document_id: str, metadata: Dict[str, Any]):
        """Prüft und verknüpft Document-Versionen"""
        # Suche nach älteren Versionen desselben Standards
        with self.neo4j.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                WHERE d.standard_name = $standard_name 
                  AND d.standard_version < $current_version
                  AND d.id <> $current_doc_id
                RETURN d.id as old_doc_id
                ORDER BY d.standard_version DESC
                LIMIT 1
            """, 
            standard_name=metadata['standard_name'],
            current_version=metadata['standard_version'],
            current_doc_id=document_id)
            
            old_doc = result.single()
            if old_doc:
                self.neo4j.link_document_versions(document_id, old_doc['old_doc_id'])
                logger.info("Linking document with previous version")

    def close(self):
        """Clean up resources"""
        self.neo4j.close()
        self.executor.shutdown(wait=True)