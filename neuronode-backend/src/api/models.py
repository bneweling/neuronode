from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="User query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    use_cache: bool = Field(default=True, description="Whether to use cached responses")

class GraphNode(BaseModel):
    """Graph node model"""
    id: str
    type: str
    label: str
    relevance: Optional[float] = None

class GraphEdge(BaseModel):
    """Graph edge model"""
    source: str
    target: str
    type: str = "RELATES_TO"
    weight: float = 0.5

class GraphMetadata(BaseModel):
    """Graph visualization metadata"""
    graph_relevant: bool = False
    graph_confidence: float = 0.0
    graph_nodes: List[GraphNode] = Field(default_factory=list)
    graph_edges: List[GraphEdge] = Field(default_factory=list)
    suggested_visualization: str = "none"

class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    response: str
    sources: List[Dict[str, Any]]
    confidence: float
    follow_up_questions: Optional[List[str]] = None
    metadata: Dict[str, Any]
    analysis: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    filename: str
    status: str
    document_type: Optional[str] = None
    num_chunks: Optional[int] = None
    num_controls: Optional[int] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BatchProcessRequest(BaseModel):
    """Request model for batch processing"""
    file_paths: List[str]
    validate: bool = True
    max_concurrent: int = 3

class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SystemStatus(BaseModel):
    """System status model"""
    status: str
    components: Dict[str, str]
    timestamp: datetime
    metrics: Optional[Dict[str, Any]] = None

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo(BaseModel):
    """Task information model"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None