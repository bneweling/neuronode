#!/usr/bin/env python3
"""
KI-Wissenssystem API
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
import traceback
import uuid

from src.api.models import (
    QueryRequest, QueryResponse, DocumentUploadResponse,
    BatchProcessRequest, SystemStatus, WebSocketMessage
)
from src.models.document_types import FileType, DocumentType
from src.orchestration.query_orchestrator import QueryOrchestrator
from src.orchestration.graph_gardener import GraphGardener
from src.document_processing.document_processor import DocumentProcessor
from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components with proper error handling
document_processor = None
query_orchestrator = None
graph_gardener = None
chroma_client = None
neo4j_client = None

def initialize_components():
    """Initialize all core components with error handling"""
    global document_processor, query_orchestrator, graph_gardener, chroma_client, neo4j_client
    
    try:
        # Initialize DocumentProcessor
        from src.document_processing.document_processor import DocumentProcessor
        document_processor = DocumentProcessor()
        logger.info("✅ DocumentProcessor initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize DocumentProcessor: {e}")
        document_processor = None
    
    try:
        # Initialize ChromaDB client
        from src.storage.chroma_client import ChromaClient
        chroma_client = ChromaClient()
        logger.info("✅ ChromaDB client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ChromaDB client: {e}")
        chroma_client = None
    
    try:
        # Initialize Neo4j client
        from src.storage.neo4j_client import Neo4jClient
        neo4j_client = Neo4jClient()
        logger.info("✅ Neo4j client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Neo4j client: {e}")
        neo4j_client = None
    
    try:
        # Initialize QueryOrchestrator
        from src.orchestration.query_orchestrator import QueryOrchestrator
        if chroma_client and neo4j_client:
            query_orchestrator = QueryOrchestrator(
                chroma_client=chroma_client,
                neo4j_client=neo4j_client
            )
            logger.info("✅ QueryOrchestrator initialized successfully")
        else:
            logger.warning("⚠️ QueryOrchestrator not initialized - missing dependencies")
            query_orchestrator = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize QueryOrchestrator: {e}")
        query_orchestrator = None
    
    try:
        # Initialize GraphGardener
        from src.orchestration.graph_gardener import GraphGardener
        if neo4j_client:
            graph_gardener = GraphGardener(neo4j_client=neo4j_client)
            logger.info("✅ GraphGardener initialized successfully")
        else:
            logger.warning("⚠️ GraphGardener not initialized - missing Neo4j client")
            graph_gardener = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize GraphGardener: {e}")
        graph_gardener = None

# Global task storage for real processing status
processing_tasks: Dict[str, Dict[str, Any]] = {}

def update_task_status(task_id: str, status: str, progress: float, metadata: Dict = {}):
    """Update task status in global store"""
    processing_tasks[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata,
        "steps_completed": _get_completed_steps(status),
        "current_step": status,
        "estimated_completion": _estimate_completion(progress)
    }
    logger.info(f"Task {task_id}: {status} ({progress:.1%}) - {metadata.get('step', 'unknown')}")

def _get_completed_steps(current_status: str) -> List[str]:
    """Get list of completed steps based on current status"""
    step_order = ["loading", "classifying", "extracting", "validating", "chunking", "storing", "completed"]
    
    if current_status == "failed":
        return []
    
    try:
        current_index = step_order.index(current_status)
        return step_order[:current_index]
    except ValueError:
        return []

def _estimate_completion(progress: float) -> str:
    """Estimate completion time based on progress"""
    if progress >= 1.0:
        return datetime.utcnow().isoformat()
    
    # Estimate remaining time based on progress (simple linear estimation)
    estimated_total_seconds = 60  # Assume 60 seconds total processing time
    remaining_progress = 1.0 - progress
    remaining_seconds = estimated_total_seconds * remaining_progress
    
    estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_seconds)
    return estimated_completion.isoformat()

# Initialize FastAPI app
app = FastAPI(
    title="KI-Wissenssystem API",
    description="API für intelligente Dokumentenverarbeitung und Wissensgraph-Management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    """Initialize components and start background services"""
    logger.info("🚀 Starting KI-Wissenssystem API...")
    initialize_components()
    
    # Start automatic graph gardening if available
    if graph_gardener:
        asyncio.create_task(continuous_graph_gardening())
        logger.info("🌱 Automatic graph gardening started")
    else:
        logger.warning("⚠️ Automatic graph gardening not started - GraphGardener not available")

async def continuous_graph_gardening():
    """Run continuous graph gardening in background"""
    while True:
        try:
            if graph_gardener:
                await graph_gardener.schedule_continuous_gardening()
                logger.info("🌱 Graph gardening cycle completed")
        except Exception as e:
            logger.error(f"❌ Graph gardening failed: {e}")
        await asyncio.sleep(3600)  # 1 hour pause

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
        "version": "1.0.0"
    }
    
    # Check Neo4j
    try:
        if neo4j_client:
            with neo4j_client.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            health_status["components"]["neo4j"] = {
                "status": "healthy",
                "message": "Connected"
            }
        else:
            health_status["components"]["neo4j"] = {
                "status": "unhealthy", 
                "message": "Not initialized"
            }
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check ChromaDB
    try:
        if chroma_client:
            chroma_client.client.heartbeat()
            health_status["components"]["chromadb"] = {
                "status": "healthy",
                "message": "Connected"
            }
        else:
            health_status["components"]["chromadb"] = {
                "status": "unhealthy",
                "message": "Not initialized"
            }
    except Exception as e:
        health_status["components"]["chromadb"] = {
            "status": "unhealthy", 
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check DocumentProcessor
    try:
        if document_processor:
            health_status["components"]["document_processor"] = {
                "status": "healthy",
                "message": "Initialized"
            }
        else:
            health_status["components"]["document_processor"] = {
                "status": "unhealthy",
                "message": "Not initialized"
            }
    except Exception as e:
        health_status["components"]["document_processor"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check QueryOrchestrator
    try:
        if query_orchestrator:
            health_status["components"]["query_orchestrator"] = {
                "status": "healthy",
                "message": "Initialized"
            }
        else:
            health_status["components"]["query_orchestrator"] = {
                "status": "unhealthy",
                "message": "Not initialized"
            }
    except Exception as e:
        health_status["components"]["query_orchestrator"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["status"] = "degraded"
    
    # Overall status
    unhealthy_components = [
        comp for comp, status in health_status["components"].items() 
        if status["status"] == "unhealthy"
    ]
    
    if len(unhealthy_components) > 2:
        health_status["status"] = "unhealthy"
    elif unhealthy_components:
        health_status["status"] = "degraded"
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics"""
    health_info = await health_check()
    
    # Add detailed metrics
    try:
        if neo4j_client:
            with neo4j_client.driver.session() as session:
                # Node counts
                node_result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                nodes = {}
                total_nodes = 0
                for record in node_result:
                    labels = record["labels"]
                    count = record["count"]
                    label_str = ":".join(labels) if labels else "Unknown"
                    nodes[label_str] = count
                    total_nodes += count
                
                # Relationship counts
                rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
                relationships = {}
                total_rels = 0
                for record in rel_result:
                    rel_type = record["rel_type"]
                    count = record["count"]
                    relationships[rel_type] = count
                    total_rels += count
                
                health_info["metrics"] = {
                    "neo4j": {
                        "total_nodes": total_nodes,
                        "total_relationships": total_rels,
                        "node_types": nodes,
                        "relationship_types": relationships
                    }
                }
    except Exception as e:
        health_info["metrics"] = {"neo4j_error": str(e)}
    
    # ChromaDB metrics
    try:
        if chroma_client:
            collections_info = {}
            total_docs = 0
            for name, collection in chroma_client.collections.items():
                count = collection.count()
                collections_info[name] = count
                total_docs += count
            
            if "metrics" not in health_info:
                health_info["metrics"] = {}
            
            health_info["metrics"]["chromadb"] = {
                "total_documents": total_docs,
                "collections": collections_info
            }
    except Exception as e:
        if "metrics" not in health_info:
            health_info["metrics"] = {}
        health_info["metrics"]["chromadb_error"] = str(e)
    
    # Processing tasks info
    health_info["processing"] = {
        "active_tasks": len(processing_tasks),
        "task_ids": list(processing_tasks.keys())
    }
    
    return health_info

# Query endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query with RAG pipeline"""
    try:
        # Check if query orchestrator is available
        if not query_orchestrator:
            logger.warning("QueryOrchestrator not available - using fallback")
            
            # Fallback: Simple response without RAG
            return QueryResponse(
                response="Entschuldigung, das Abfragesystem ist derzeit nicht verfügbar. Bitte versuchen Sie es später erneut.",
                sources=[],
                metadata={
                    "status": "fallback",
                    "reason": "QueryOrchestrator not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Process with full RAG pipeline
        result = await query_orchestrator.process_query(
            query=request.query,
            user_context=request.context,
            use_cache=request.use_cache
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        
        # Enhanced fallback with ChromaDB direct access if available
        if chroma_client:
            try:
                # Direct ChromaDB search as fallback
                search_results = await _fallback_chromadb_search(request.query)
                
                return QueryResponse(
                    response=f"Basierend auf den verfügbaren Dokumenten: {search_results['summary']}",
                    sources=search_results['sources'],
                    metadata={
                        "status": "chromadb_fallback",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
        
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

async def _fallback_chromadb_search(query: str, n_results: int = 3):
    """Fallback search using ChromaDB directly"""
    try:
        # Search across all collections
        search_results = chroma_client.search_similar(
            query=query,
            collection_names=["compliance", "technical", "general"],
            n_results=n_results * 2  # Get more results to filter
        )
        
        # Create summary
        if search_results:
            summary = f"Gefunden: {len(search_results)} relevante Dokument-Abschnitte aus verarbeiteten Dokumenten. "
            
            # Add info about document types found
            collections_found = set(result.get('collection', 'unknown') for result in search_results)
            if 'compliance' in collections_found:
                summary += "Enthält Compliance-Dokumente (BSI, ISO, NIST). "
            if 'technical' in collections_found:
                summary += "Enthält technische Dokumentation. "
                
            # Add sample content from top result
            if search_results[0].get('text'):
                sample_text = search_results[0]['text'][:200]
                summary += f"\n\nAuszug aus relevantem Dokument: \"{sample_text}...\""
        else:
            summary = "Keine relevanten Dokumente gefunden. Möglicherweise wurden noch keine Dokumente verarbeitet oder die Anfrage ist zu spezifisch."
        
        # Format sources for response
        formatted_sources = []
        for result in search_results[:5]:  # Top 5 results
            formatted_sources.append({
                "text": result.get('text', ''),
                "metadata": result.get('metadata', {}),
                "confidence": 1.0 - result.get('distance', 1.0),  # Convert distance to confidence
                "collection": result.get('collection', 'unknown')
            })
        
        return {
            "summary": summary,
            "sources": formatted_sources
        }
        
    except Exception as e:
        logger.error(f"Fallback ChromaDB search failed: {e}")
        return {
            "summary": f"Suche in der Dokumentenbasis ist derzeit nicht verfügbar. Fehler: {str(e)}",
            "sources": []
        }

@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """Process a query with streaming response"""
    
    async def generate():
        try:
            # Start with metadata
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Check if query orchestrator is available
            if not query_orchestrator:
                yield f"data: {json.dumps({'type': 'error', 'error': 'QueryOrchestrator not available'})}\n\n"
                return
            
            # Process query
            result = await query_orchestrator.process_query(
                query=request.query,
                user_context=request.context,
                use_cache=request.use_cache
            )
            
            # Stream response in chunks
            response_text = result['response']
            chunk_size = 100
            
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send sources and metadata
            yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': result['metadata']})}\n\n"
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Document processing endpoints
@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    force_type: Optional[str] = None,
    validate: bool = True
):
    """Upload and process a document"""
    try:
        logger.info(f"📄 Upload gestartet: {file.filename}")
        
        # Check if document processor is available
        if not document_processor:
            logger.warning("DocumentProcessor nicht verfügbar - einfache Verarbeitung")
            # Simple fallback processing
            content = await file.read()
            return DocumentUploadResponse(
                filename=file.filename,
                status="processed_simple",
                metadata={
                    "size": len(content),
                    "message": "Dokument empfangen, aber Verarbeitung eingeschränkt (Services nicht verfügbar)"
                }
            )
        
        # Save uploaded file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"📄 Datei gespeichert: {tmp_path} ({len(content)} bytes)")
        
        # Process document
        if force_type:
            try:
                from src.models.document_types import DocumentType
                force_type_enum = DocumentType[force_type.upper()]
            except:
                logger.warning(f"Unknown document type: {force_type}")
                force_type_enum = None
        else:
            force_type_enum = None
        
        # Process immediately for small files, in background for large ones
        file_size = len(content)
        if file_size < 5 * 1024 * 1024:  # 5MB
            try:
                result = await document_processor.process_document(
                    tmp_path,
                    force_type=force_type_enum,
                    validate=validate
                )
                
                # Clean up
                os.unlink(tmp_path)
                
                return DocumentUploadResponse(
                    filename=file.filename,
                    status="completed",
                    document_type=result.document_type.value if hasattr(result, 'document_type') else "unknown",
                    num_chunks=len(result.chunks) if hasattr(result, 'chunks') else 0,
                    num_controls=len(result.controls) if hasattr(result, 'controls') else 0,
                    metadata=result.metadata if hasattr(result, 'metadata') else {}
                )
            except Exception as processing_error:
                logger.error(f"Document processing failed: {processing_error}")
                # Clean up
                os.unlink(tmp_path)
                
                # Return partial success
                return DocumentUploadResponse(
                    filename=file.filename,
                    status="upload_only",
                    metadata={
                        "size": file_size,
                        "error": f"Processing failed: {str(processing_error)}",
                        "message": "Datei hochgeladen, aber Verarbeitung fehlgeschlagen"
                    }
                )
        else:
            # Process in background
            task_id = f"doc_{datetime.utcnow().timestamp()}"
            
            background_tasks.add_task(
                process_document_background,
                tmp_path,
                file.filename,
                task_id,
                force_type_enum,
                validate
            )
            
            return DocumentUploadResponse(
                filename=file.filename,
                status="processing",
                task_id=task_id,
                metadata={"file_size": file_size}
            )
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        import traceback
        traceback.print_exc()
        
        return DocumentUploadResponse(
            filename=file.filename if 'file' in locals() else "unknown",
            status="error",
            metadata={
                "error": str(e),
                "message": "Upload komplett fehlgeschlagen"
            }
        )

@app.post("/documents/batch")
async def process_batch(request: BatchProcessRequest, background_tasks: BackgroundTasks):
    """Process multiple documents in batch"""
    task_id = f"batch_{datetime.utcnow().timestamp()}"
    
    background_tasks.add_task(
        process_batch_background,
        request.file_paths,
        task_id
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "num_documents": len(request.file_paths)
    }

# Knowledge graph endpoints
@app.get("/knowledge-graph/stats")
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        with neo4j_client.driver.session() as session:
            # Get node counts
            node_counts = {}
            for label in ["ControlItem", "KnowledgeChunk", "Technology", "Entity"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                node_counts[label] = result.single()["count"]
            
            # Get relationship counts
            rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            rel_counts = {record["type"]: record["count"] for record in rel_result}
            
            # Get orphan count
            orphan_result = session.run("""
                MATCH (n)
                WHERE NOT (n)-[]-()
                RETURN count(n) as count
            """)
            orphan_count = orphan_result.single()["count"]
        
        # Get vector store stats
        vector_stats = {}
        for collection_name, collection in chroma_client.collections.items():
            vector_stats[collection_name] = collection.count()
        
        return {
            "neo4j": {
                "nodes": node_counts,
                "relationships": rel_counts,
                "orphan_nodes": orphan_count
            },
            "chromadb": {
                "collections": vector_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-graph/search")
async def search_graph(
    query: str,
    node_type: Optional[str] = None,
    limit: int = 20
):
    """Search the knowledge graph"""
    try:
        with neo4j_client.driver.session() as session:
            if node_type:
                cypher = f"""
                    MATCH (n:{node_type})
                    WHERE n.text CONTAINS $query 
                       OR n.title CONTAINS $query
                       OR n.id CONTAINS $query
                    RETURN n
                    LIMIT $limit
                """
            else:
                cypher = """
                    MATCH (n)
                    WHERE n.text CONTAINS $query 
                       OR n.title CONTAINS $query
                       OR n.id CONTAINS $query
                    RETURN n, labels(n) as labels
                    LIMIT $limit
                """
            
            result = session.run(cypher, query=query, limit=limit)
            
            nodes = []
            for record in result:
                node_data = dict(record["n"])
                if "labels" in record:
                    node_data["_labels"] = record["labels"]
                nodes.append(node_data)
            
            return {
                "query": query,
                "results": nodes,
                "count": len(nodes)
            }
            
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-graph/node/{node_id}")
async def get_node_context(
    node_id: str,
    depth: int = 2,
    include_metadata: bool = True
):
    """Get detailed node information with context"""
    try:
        with neo4j_client.driver.session() as session:
            # Get the main node
            node_result = session.run("""
                MATCH (n {id: $node_id})
                RETURN n, labels(n) as labels
            """, node_id=node_id)
            
            main_record = node_result.single()
            if not main_record:
                raise HTTPException(status_code=404, detail="Node not found")
            
            main_node = dict(main_record["n"])
            main_node["_labels"] = main_record["labels"]
            
            # Get related nodes with relationships
            related_result = session.run(f"""
                MATCH path = (start {{id: $node_id}})-[r*1..{depth}]-(end)
                RETURN DISTINCT 
                    end as node, 
                    labels(end) as labels,
                    [rel in relationships(path) | {{
                        type: type(rel),
                        properties: properties(rel),
                        start_id: startNode(rel).id,
                        end_id: endNode(rel).id
                    }}] as path_relationships,
                    length(path) as distance
                ORDER BY distance
                LIMIT 50
            """, node_id=node_id)
            
            related_nodes = []
            edges = []
            processed_edges = set()
            
            for record in related_result:
                # Add related node
                node_data = dict(record["node"])
                node_data["_labels"] = record["labels"]
                node_data["_distance"] = record["distance"]
                related_nodes.append(node_data)
                
                # Add relationships
                for rel in record["path_relationships"]:
                    edge_key = f"{rel['start_id']}-{rel['type']}-{rel['end_id']}"
                    if edge_key not in processed_edges:
                        processed_edges.add(edge_key)
                        edges.append({
                            "source": rel["start_id"],
                            "target": rel["end_id"],
                            "type": rel["type"],
                            "properties": rel["properties"]
                        })
        
        return {
            "main_node": main_node,
            "nodes": [main_node] + related_nodes,
            "edges": edges,
            "metadata": {
                "depth": depth,
                "total_nodes": len(related_nodes) + 1,
                "total_edges": len(edges)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting node context for {node_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/processing-status/{task_id}")
async def get_processing_status(task_id: str):
    """Get REAL status of document processing task"""
    
    # Check for real processing task first
    if task_id in processing_tasks:
        return processing_tasks[task_id]
    
    # If task not found, it might be an old simulation task or invalid
    logger.warning(f"Task {task_id} not found in processing tasks")
    raise HTTPException(status_code=404, detail="Processing task not found")

@app.post("/documents/analyze-preview")
async def analyze_document_preview(
    file: UploadFile = File(...),
    preview_length: int = 2000
):
    """Analyze document without full processing - for preview/transparency"""
    try:
        # Read file content
        content = await file.read()
        
        # Quick file type detection
        import tempfile
        import os
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        file_path = Path(tmp_path)
        
        try:
            file_type = document_processor._detect_file_type(file_path)
        except Exception as e:
            logger.warning(f"File type detection failed: {e}. Using fallback.")
            # Fallback file type detection based on extension
            ext = file.filename.split('.')[-1].lower() if file.filename else ""
            if ext == "pdf":
                file_type = FileType.PDF
            elif ext in ["txt", "md"]:
                file_type = FileType.TXT
            elif ext in ["doc", "docx"]:
                file_type = FileType.DOCX
            else:
                file_type = FileType.TXT
        
        # Load first part of document with fallback
        try:
            if file_type == FileType.PDF:
                from src.document_processing.loaders.pdf_loader import PDFLoader
                loader = PDFLoader()
                raw_content = loader.load(tmp_path)
            elif file_type == FileType.TXT:
                raw_content = {"full_text": content.decode('utf-8', errors='ignore')}
            else:
                # For other file types, try to extract as text
                try:
                    raw_content = {"full_text": content.decode('utf-8', errors='ignore')}
                except:
                    raw_content = {"full_text": "Binary file - full processing required"}
        except Exception as e:
            logger.warning(f"Document loading failed: {e}. Using fallback.")
            try:
                raw_content = {"full_text": content.decode('utf-8', errors='ignore')}
            except:
                raw_content = {"full_text": "Binary file - full processing required"}
        
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        # Preview text
        preview_text = raw_content.get("full_text", "")[:preview_length]
        
        # Classification with enhanced error handling
        predicted_type = DocumentType.UNKNOWN
        classification_status = "failed"
        
        try:
            if document_processor:
                from src.document_processing.classifier import DocumentClassifier
                classifier = DocumentClassifier()
                predicted_type = classifier.classify(preview_text, {"filename": file.filename})
                classification_status = "success"
            else:
                logger.warning("Document processor not available. Using basic classification.")
                # Basic rule-based classification as fallback
                preview_lower = preview_text.lower()
                if "grundschutz" in preview_lower or "bsi" in preview_lower:
                    predicted_type = DocumentType.BSI_GRUNDSCHUTZ
                elif "iso 27001" in preview_lower or "iso/iec 27001" in preview_lower:
                    predicted_type = DocumentType.ISO_27001
                elif "nist" in preview_lower:
                    predicted_type = DocumentType.NIST_CSF
                else:
                    predicted_type = DocumentType.TECHNICAL_DOC
                classification_status = "fallback"
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Ultra-simple fallback based on filename
            if file.filename:
                filename_lower = file.filename.lower()
                if "grundschutz" in filename_lower:
                    predicted_type = DocumentType.BSI_GRUNDSCHUTZ
                elif "iso" in filename_lower:
                    predicted_type = DocumentType.ISO_27001
                elif "nist" in filename_lower:
                    predicted_type = DocumentType.NIST_CSF
                else:
                    predicted_type = DocumentType.TECHNICAL_DOC
            classification_status = "filename_fallback"
        
        # Estimate processing complexity
        word_count = len(preview_text.split())
        estimated_chunks = max(1, word_count // 200)  # Rough estimate
        
        processing_estimate = {
            "estimated_duration_seconds": min(300, max(10, word_count // 100)),
            "estimated_chunks": estimated_chunks,
            "will_extract_controls": predicted_type.value in [
                "bsi_grundschutz", "bsi_c5", "iso_27001", "nist_csf"
            ],
            "processing_steps": [
                "File loading",
                "Content extraction", 
                "Document classification",
                "Control extraction" if predicted_type.value in ["bsi_grundschutz", "bsi_c5", "iso_27001", "nist_csf"] else "Chunk creation",
                "Quality validation",
                "Graph storage",
                "Vector indexing",
                "Relationship analysis"
            ]
        }
        
        return {
            "filename": file.filename,
            "file_type": file_type.value,
            "predicted_document_type": predicted_type.value,
            "preview_text": preview_text,
            "file_size_bytes": len(content),
            "word_count": word_count,
            "processing_estimate": processing_estimate,
            "confidence_indicators": {
                "type_detection": "high" if file_type != FileType.TXT else "medium",
                "classification": "high" if classification_status == "success" else "medium",
                "classification_method": classification_status
            },
            "status": "success",
            "warnings": ["API quota reached - using fallback classification"] if classification_status != "success" else []
        }
        
    except Exception as e:
        logger.error(f"Error analyzing document preview: {e}")
        return {
            "filename": file.filename if 'file' in locals() else "unknown",
            "status": "error",
            "error": str(e),
            "message": "Dokument-Analyse fehlgeschlagen. Bitte versuchen Sie es später erneut.",
            "file_type": "unknown",
            "predicted_document_type": "unknown",
            "preview_text": "",
            "file_size_bytes": 0,
            "word_count": 0,
            "processing_estimate": {
                "estimated_duration_seconds": 30,
                "estimated_chunks": 1,
                "will_extract_controls": False,
                "processing_steps": ["Basic upload processing"]
            },
            "confidence_indicators": {
                "type_detection": "low",
                "classification": "failed"
            }
        }

@app.get("/knowledge-graph/relationships/types")
async def get_relationship_types():
    """Get all relationship types in the graph with counts"""
    try:
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, 
                       count(r) as count,
                       collect(DISTINCT [labels(startNode(r))[0], labels(endNode(r))[0]]) as node_type_pairs
                ORDER BY count DESC
            """)
            
            relationships = []
            for record in result:
                relationships.append({
                    "type": record["relationship_type"],
                    "count": record["count"],
                    "connects": record["node_type_pairs"],
                    "description": _get_relationship_description(record["relationship_type"])
                })
        
        return {
            "relationship_types": relationships,
            "total_types": len(relationships)
        }
        
    except Exception as e:
        logger.error(f"Error getting relationship types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_relationship_description(rel_type: str) -> str:
    """Get human-readable description of relationship type"""
    descriptions = {
        "IMPLEMENTS": "Technologie implementiert Control oder Anforderung",
        "SUPPORTS": "Dokument unterstützt oder ergänzt Control",
        "REFERENCES": "Verweis oder Referenz zwischen Dokumenten",
        "MAPS_TO": "Mapping zwischen verschiedenen Standards",
        "MENTIONS": "Erwähnung von Entität in Dokument",
        "RELATES_TO": "Allgemeine thematische Beziehung",
        "CONFLICTS": "Widerspruch oder Konflikt zwischen Inhalten",
        "DEPENDS_ON": "Abhängigkeit zwischen Controls oder Komponenten"
    }
    return descriptions.get(rel_type, f"Beziehung vom Typ {rel_type}")

@app.get("/knowledge-graph/orphans")
async def get_orphan_nodes(min_connections: int = 1):
    """Get nodes with few or no connections"""
    try:
        orphans = neo4j_client.get_orphan_nodes(min_connections)
        
        # Add suggestions for each orphan
        for orphan in orphans:
            node_data = orphan["node"]
            if "text" in node_data:
                # Find potential connections via similarity search
                similar = chroma_client.search_similar(
                    node_data["text"][:200],
                    n_results=3,
                    filter_dict={"id": {"$ne": node_data.get("id")}}
                )
                
                orphan["potential_connections"] = [
                    {
                        "target_id": chunk["id"],
                        "similarity": 1 - chunk["distance"],
                        "reason": "Semantic similarity"
                    }
                    for chunk in similar
                    if chunk["distance"] < 0.4  # High similarity threshold
                ]
            else:
                orphan["potential_connections"] = []
        
        return {
            "orphan_nodes": orphans,
            "count": len(orphans),
            "suggestions_available": sum(1 for o in orphans if o.get("potential_connections"))
        }
        
    except Exception as e:
        logger.error(f"Error getting orphan nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge-graph/validate-relationship")
async def validate_potential_relationship(
    source_id: str,
    target_id: str,
    relationship_type: Optional[str] = None
):
    """Validate if a relationship should exist between two nodes"""
    try:
        # Get both nodes
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH (s {id: $source_id}), (t {id: $target_id})
                RETURN s, t, labels(s) as source_labels, labels(t) as target_labels
            """, source_id=source_id, target_id=target_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="One or both nodes not found")
            
            source_node = dict(record["s"])
            target_node = dict(record["t"])
            source_labels = record["source_labels"]
            target_labels = record["target_labels"]
        
        # Use graph gardener to validate relationship
        if relationship_type:
            validation = await graph_gardener._validate_relationship(
                source_node.get("text", source_node.get("title", "")),
                source_node.get("title", ""),
                target_node.get("text", target_node.get("title", "")),
                target_node.get("title", ""),
                target_id
            )
        else:
            # Auto-determine relationship type
            validation = await graph_gardener._validate_relationship(
                source_node.get("text", source_node.get("title", "")),
                source_node.get("title", ""),
                target_node.get("text", target_node.get("title", "")),
                target_node.get("title", ""),
                target_id
            )
        
        return {
            "source": {
                "id": source_id,
                "labels": source_labels,
                "title": source_node.get("title", "")
            },
            "target": {
                "id": target_id, 
                "labels": target_labels,
                "title": target_node.get("title", "")
            },
            "validation": validation,
            "recommendation": "create" if validation["confidence"] > 0.7 else "skip"
        }
        
    except Exception as e:
        logger.error(f"Error validating relationship {source_id} -> {target_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.post("/admin/reindex")
async def trigger_reindex(background_tasks: BackgroundTasks):
    """Trigger reindexing of vector store"""
    task_id = f"reindex_{datetime.utcnow().timestamp()}"
    
    background_tasks.add_task(reindex_vector_store, task_id)
    
    return {
        "task_id": task_id,
        "status": "started"
    }

@app.post("/admin/garden")
async def trigger_gardening(
    background_tasks: BackgroundTasks,
    focus: str = "orphans"
):
    """Manually trigger graph gardening"""
    task_id = f"garden_{datetime.utcnow().timestamp()}"
    
    background_tasks.add_task(
        run_gardening_task,
        task_id,
        focus
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "focus": focus
    }

# Enhanced WebSocket endpoint for real-time chat with RAG
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with RAG pipeline"""
    await websocket.accept()
    
    # Generate session ID
    session_id = f"ws_{datetime.utcnow().timestamp()}"
    logger.info(f"WebSocket connection established: {session_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "query":
                # Process query
                await websocket.send_json({
                    "type": "processing",
                    "message": "Verarbeite Ihre Anfrage..."
                })
                
                try:
                    if query_orchestrator:
                        # Process with conversation context if provided
                        if "conversation" in message:
                            result = await query_orchestrator.process_conversation(
                                messages=message["conversation"],
                                conversation_id=session_id
                            )
                        else:
                            result = await query_orchestrator.process_query(
                                query=message["query"],
                                user_context={"session_id": session_id}
                            )
                    else:
                        # Fallback to direct ChromaDB search
                        if chroma_client:
                            fallback_result = await _fallback_chromadb_search(message["query"])
                            result = {
                                "response": fallback_result["summary"],
                                "sources": fallback_result["sources"],
                                "metadata": {"status": "fallback_mode"}
                            }
                        else:
                            result = {
                                "response": "Das Abfragesystem ist derzeit nicht verfügbar.",
                                "sources": [],
                                "metadata": {"status": "unavailable"}
                            }
                    
                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "data": result
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })
            
            elif message["type"] == "suggestions":
                # Get query suggestions
                try:
                    if query_orchestrator:
                        suggestions = await query_orchestrator.get_query_suggestions(
                            message.get("partial_query", "")
                        )
                    else:
                        # Fallback suggestions
                        suggestions = [
                            "Welche BSI-Grundschutz Maßnahmen gibt es?",
                            "Was sind die wichtigsten ISO 27001 Controls?",
                            "Wie implementiere ich NIST CSF?",
                            "Welche Sicherheitsrichtlinien sind relevant?"
                        ]
                    
                    await websocket.send_json({
                        "type": "suggestions",
                        "suggestions": suggestions
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Suggestions failed: {str(e)}"
                    })
            
            elif message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Background task functions
async def process_document_background(
    file_path: str,
    filename: str,
    task_id: str,
    force_type,
    validate: bool
):
    """Process document in background with REAL status tracking"""
    
    def status_callback(task_id: str, status: str, progress: float, metadata: Dict = {}):
        """Callback function to update task status during processing"""
        update_task_status(task_id, status, progress, metadata)
    
    try:
        # Initialize task
        update_task_status(task_id, "loading", 0.0, {
            "step": "initializing",
            "filename": filename,
            "processing_started": datetime.utcnow().isoformat()
        })
        
        # Process document with status callbacks
        result = await document_processor.process_document(
            file_path,
            force_type=force_type,
            validate=validate,
            status_callback=status_callback,
            task_id=task_id
        )
        
        # Final status update with results
        update_task_status(task_id, "completed", 1.0, {
            "step": "processing_completed",
            "filename": filename,
            "document_type": result.document_type.value,
            "num_chunks": len(result.chunks),
            "num_controls": len(result.controls),
            "processing_completed": datetime.utcnow().isoformat(),
            "file_hash": result.metadata.get("file_hash", ""),
            "success": True
        })
        
        logger.info(f"✅ Document {filename} processed successfully: "
                   f"{len(result.controls)} controls, {len(result.chunks)} chunks")
        
    except Exception as e:
        # Update task status on failure
        update_task_status(task_id, "failed", 0.0, {
            "step": "processing_failed",
            "filename": filename,
            "error": str(e),
            "error_traceback": traceback.format_exc(),
            "processing_failed": datetime.utcnow().isoformat(),
            "success": False
        })
        logger.error(f"❌ Error processing document {filename}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Clean up temp file
        import os
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {file_path}: {e}")

async def process_batch_background(file_paths: List[str], task_id: str):
    """Process batch of documents"""
    try:
        results = await document_processor.process_batch(file_paths)
        logger.info(f"Batch {task_id} completed: {len(results)} documents processed")
    except Exception as e:
        logger.error(f"Error processing batch {task_id}: {e}")

async def reindex_vector_store(task_id: str):
    """Reindex vector store"""
    try:
        # Implementation would rebuild vector indices
        logger.info(f"Reindexing task {task_id} started")
        await asyncio.sleep(1)  # Placeholder
        logger.info(f"Reindexing task {task_id} completed")
    except Exception as e:
        logger.error(f"Error in reindexing task {task_id}: {e}")

async def run_gardening_task(task_id: str, focus: str):
    """Run gardening task"""
    try:
        result = await graph_gardener.run_gardening_cycle(focus)
        logger.info(f"Gardening task {task_id} completed: {result}")
    except Exception as e:
        logger.error(f"Error in gardening task {task_id}: {e}")

@app.get("/processing/tasks")
async def get_all_processing_tasks():
    """Get all active processing tasks"""
    return {
        "active_tasks": len(processing_tasks),
        "tasks": {
            task_id: {
                "status": task_info["status"], 
                "progress": task_info["progress"],
                "timestamp": task_info["timestamp"],
                "filename": task_info.get("filename", "Unknown")
            }
            for task_id, task_info in processing_tasks.items()
        }
    }

@app.delete("/processing/tasks/{task_id}")
async def cancel_processing_task(task_id: str):
    """Cancel a processing task"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = processing_tasks[task_id]
    
    # Mark as cancelled
    processing_tasks[task_id] = {
        **task_info,
        "status": "cancelled",
        "progress": 0.0,
        "timestamp": datetime.utcnow().isoformat(),
        "cancelled_at": datetime.utcnow().isoformat()
    }
    
    return {"message": f"Task {task_id} cancelled", "task_id": task_id}

@app.post("/processing/cleanup")
async def cleanup_completed_tasks():
    """Clean up completed processing tasks"""
    completed_statuses = ["completed", "failed", "cancelled"]
    
    completed_tasks = [
        task_id for task_id, task_info in processing_tasks.items()
        if task_info["status"] in completed_statuses
    ]
    
    for task_id in completed_tasks:
        del processing_tasks[task_id]
    
    return {
        "message": f"Cleaned up {len(completed_tasks)} completed tasks",
        "cleaned_task_ids": completed_tasks,
        "remaining_tasks": len(processing_tasks)
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )