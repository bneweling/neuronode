from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """Request model for query processing"""
    query: str
    context: Optional[Dict[str, Any]] = {}
    use_cache: bool = True

class QueryResponse(BaseModel):
    """Response model for query processing"""
    query: str
    response: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    follow_up_questions: List[str] = []
    metadata: Dict[str, Any] = {}
    analysis: Optional[Dict[str, Any]] = {}

class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    filename: str
    status: str
    document_type: Optional[str] = None
    task_id: Optional[str] = None
    num_chunks: Optional[int] = None
    num_controls: Optional[int] = None
    metadata: Dict[str, Any] = {}

class BatchProcessRequest(BaseModel):
    """Request model for batch processing"""
    file_paths: List[str]
    force_type: Optional[str] = None
    validate: bool = True

class GraphStats(BaseModel):
    """Response model for graph statistics"""
    total_nodes: int
    total_relationships: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]

class SearchResult(BaseModel):
    """Model for search results"""
    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = {}
    score: float = 0.0 