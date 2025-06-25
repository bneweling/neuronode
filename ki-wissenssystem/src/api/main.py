#!/usr/bin/env python3
"""
KI-Wissenssystem API
"""

import sys
import os
from pathlib import Path

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
from datetime import datetime

from src.api.models import (
    QueryRequest, QueryResponse, DocumentUploadResponse,
    BatchProcessRequest, SystemStatus, WebSocketMessage
)
from src.orchestration.query_orchestrator import QueryOrchestrator
from src.orchestration.graph_gardener import GraphGardener
from src.document_processing.document_processor import DocumentProcessor
from src.storage.neo4j_client import Neo4jClient
from src.storage.chroma_client import ChromaClient
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
query_orchestrator = None
document_processor = None
graph_gardener = None
neo4j_client = None
chroma_client = None

# Background tasks
background_tasks = set()

# Simplified startup - no complex lifecycle needed for working uploads
# Initialize components with graceful fallbacks
query_orchestrator = None
document_processor = None
graph_gardener = None
neo4j_client = None
chroma_client = None

try:
    logger.info("Starting KI-Wissenssystem API...")
    
    # Initialize core components with fallbacks
    try:
        from src.orchestration.query_orchestrator import QueryOrchestrator
        from src.document_processing.document_processor import DocumentProcessor
        
        query_orchestrator = QueryOrchestrator()
        document_processor = DocumentProcessor()
        logger.info("✅ Core components initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Core components failed to initialize: {e}")
    
    # Optional components - don't fail startup if they can't connect
    try:
        from src.orchestration.graph_gardener import GraphGardener
        from src.storage.neo4j_client import Neo4jClient
        from src.storage.chroma_client import ChromaClient
        
        graph_gardener = GraphGardener()
        neo4j_client = Neo4jClient()
        chroma_client = ChromaClient()
        logger.info("✅ Optional components initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Optional components failed to initialize: {e}")
    
    logger.info("🚀 API startup complete")
    
except Exception as e:
    logger.error(f"❌ API startup failed: {e}")

# No complex lifecycle manager needed

# Create FastAPI app
app = FastAPI(
    title="KI-Wissenssystem API",
    description="AI-powered knowledge system for compliance and security consulting",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check system health"""
    try:
        components = {}
        
        # Check Neo4j connection (if available)
        if neo4j_client:
            try:
                with neo4j_client.driver.session() as session:
                    session.run("RETURN 1")
                components["neo4j"] = "connected"
            except:
                components["neo4j"] = "disconnected"
        else:
            components["neo4j"] = "not_initialized"
        
        # Check other components
        components["document_processor"] = "available" if document_processor else "not_initialized"
        components["query_orchestrator"] = "available" if query_orchestrator else "not_initialized"
        components["chromadb"] = "available" if chroma_client else "not_initialized"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": components
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,  # Don't fail health check completely
            content={
                "status": "partial",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Query endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query"""
    try:
        result = await query_orchestrator.process_query(
            query=request.query,
            user_context=request.context,
            use_cache=request.use_cache
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """Process a query with streaming response"""
    
    async def generate():
        try:
            # Start with metadata
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
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
    """Get status of document processing task"""
    # In einer vollständigen Implementierung würde hier ein Task-Store abgefragt
    # Für jetzt simulieren wir den Status
    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 0.75,
        "steps_completed": [
            "file_upload",
            "type_detection", 
            "classification",
            "extraction"
        ],
        "current_step": "quality_validation",
        "estimated_completion": "2024-01-15T10:30:00Z"
    }

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
        file_type = document_processor._detect_file_type(file_path)
        
        # Load first part of document
        if file_type == FileType.PDF:
            from src.document_processing.loaders.pdf_loader import PDFLoader
            loader = PDFLoader()
            raw_content = loader.load(tmp_path)
        elif file_type == FileType.TXT:
            raw_content = {"full_text": content.decode('utf-8', errors='ignore')}
        else:
            raw_content = {"full_text": "Binary file - full processing required"}
        
        # Clean up
        os.unlink(tmp_path)
        
        # Preview text
        preview_text = raw_content.get("full_text", "")[:preview_length]
        
        # Quick classification
        from src.document_processing.classifier import DocumentClassifier
        classifier = DocumentClassifier()
        predicted_type = classifier.classify(preview_text)
        
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
                "classification": "high" if any(keyword in preview_text.lower() for keyword in ["grundschutz", "iso", "nist", "bsi"]) else "medium"
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing document preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
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
                suggestions = await query_orchestrator.get_query_suggestions(
                    message.get("partial_query", "")
                )
                
                await websocket.send_json({
                    "type": "suggestions",
                    "suggestions": suggestions
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
    """Process document in background"""
    try:
        result = await document_processor.process_document(
            file_path,
            force_type=force_type,
            validate=validate
        )
        
        # Store result (in production, use proper task storage)
        logger.info(f"Document {filename} processed successfully: "
                   f"{len(result.controls)} controls, {len(result.chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing document {filename}: {e}")
    finally:
        # Clean up temp file
        import os
        if os.path.exists(file_path):
            os.unlink(file_path)

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

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )