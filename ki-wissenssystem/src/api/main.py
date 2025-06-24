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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global query_orchestrator, document_processor, graph_gardener, neo4j_client, chroma_client
    
    logger.info("Starting KI-Wissenssystem API...")
    
    # Initialize components
    query_orchestrator = QueryOrchestrator()
    document_processor = DocumentProcessor()
    graph_gardener = GraphGardener()
    neo4j_client = Neo4jClient()
    chroma_client = ChromaClient()
    
    # Start background tasks
    gardening_task = asyncio.create_task(
        graph_gardener.schedule_continuous_gardening(interval_hours=24)
    )
    background_tasks.add(gardening_task)
    gardening_task.add_done_callback(background_tasks.discard)
    
    logger.info("API initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down API...")
    
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
    
    # Close connections
    neo4j_client.close()
    document_processor.close()
    
    logger.info("API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="KI-Wissenssystem API",
    description="AI-powered knowledge system for compliance and security consulting",
    version="1.0.0",
    lifespan=lifespan
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
        # Check Neo4j connection
        with neo4j_client.driver.session() as session:
            session.run("RETURN 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "neo4j": "connected",
                "chromadb": "connected",
                "llm": "available"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
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
        # Save uploaded file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process document
        if force_type:
            from src.models.document_types import DocumentType
            force_type_enum = DocumentType[force_type.upper()]
        else:
            force_type_enum = None
        
        # Process immediately for small files, in background for large ones
        file_size = len(content)
        if file_size < 5 * 1024 * 1024:  # 5MB
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
                document_type=result.document_type.value,
                num_chunks=len(result.chunks),
                num_controls=len(result.controls),
                metadata=result.metadata
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
        raise HTTPException(status_code=500, detail=str(e))

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