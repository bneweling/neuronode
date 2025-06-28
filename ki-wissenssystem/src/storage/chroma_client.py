import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from src.config.settings import settings
import uuid
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging

from src.config.exceptions import (
    ErrorCode, DatabaseError, SystemError
)
from src.utils.error_handler import error_handler, handle_exceptions, retry_with_backoff

logger = logging.getLogger(__name__)

class ChromaClient:
    def __init__(self):
        try:
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=Settings(anonymized_telemetry=False)
            )
            # Test connection
            self.client.heartbeat()
        except Exception as e:
            db_error = DatabaseError(
                f"Failed to connect to ChromaDB: {str(e)}",
                ErrorCode.DB_CONNECTION_FAILED,
                {"host": settings.chroma_host, "port": settings.chroma_port},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error
        
        # Configure Gemini embeddings via LangChain
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key
        )
        self._init_collections()
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini embedding model via LangChain"""
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            db_error = DatabaseError(
                f"Error generating embedding with Gemini: {str(e)}",
                ErrorCode.DB_EMBEDDING_FAILED,
                {"text_length": len(text)},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error
    
    def _init_collections(self):
        """Initialize collections for different document types"""
        self.collections = {
            "compliance": self.client.get_or_create_collection(
                name="compliance_docs",
                metadata={"description": "BSI, ISO, NIST compliance documents"}
            ),
            "technical": self.client.get_or_create_collection(
                name="technical_docs",
                metadata={"description": "Technical documentation and whitepapers"}
            ),
            "general": self.client.get_or_create_collection(
                name="general_knowledge",
                metadata={"description": "General knowledge chunks"}
            )
        }
    
    def add_chunk(self, chunk: Dict[str, Any], collection_name: str = "general") -> str:
        """Add a chunk to the vector store"""
        chunk_id = chunk.get("id", str(uuid.uuid4()))
        
        # Generate embedding using Gemini
        embedding = self._get_embedding(chunk["text"])
        
        # Prepare metadata - ChromaDB only accepts strings, numbers, or booleans
        metadata = {
            "source": str(chunk.get("source", "unknown")),
            "page": str(chunk.get("page", "")) if chunk.get("page") is not None else "",
            "summary": str(chunk.get("summary", "")),
            "keywords": ", ".join(chunk.get("keywords", [])),
        }
        
        # Add other metadata, ensuring all values are strings
        chunk_metadata = chunk.get("metadata", {})
        for key, value in chunk_metadata.items():
            if value is not None:
                metadata[key] = str(value)
            else:
                metadata[key] = ""
        
        # Add to collection
        collection = self.collections.get(collection_name, self.collections["general"])
        collection.add(
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[metadata],
            ids=[chunk_id]
        )
        
        return chunk_id
    
    def search_similar(
        self, 
        query: str, 
        collection_names: List[str] = None,
        n_results: int = 10,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks across collections"""
        if collection_names is None:
            collection_names = list(self.collections.keys())
        
        all_results = []
        query_embedding = self._get_embedding(query)
        
        for collection_name in collection_names:
            if collection_name not in self.collections:
                continue
                
            collection = self.collections[collection_name]
            
            # Build where clause
            where_clause = filter_dict if filter_dict else None
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
            
            # Process results
            for i in range(len(results["ids"][0])):
                all_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "collection": collection_name
                })
        
        # Sort by distance and return top results
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:n_results]
    
    def get_chunk(self, chunk_id: str, collection_name: str = "general") -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        result = collection.get(ids=[chunk_id])
        
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "text": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None
    
    def update_chunk_metadata(self, chunk_id: str, metadata: Dict[str, Any], collection_name: str = "general"):
        """Update metadata for a chunk"""
        collection = self.collections.get(collection_name, self.collections["general"])
        
        # Get existing chunk
        existing = collection.get(ids=[chunk_id])
        if existing["ids"]:
            # Merge metadata
            updated_metadata = {**existing["metadatas"][0], **metadata}
            
            # Update
            collection.update(
                ids=[chunk_id],
                metadatas=[updated_metadata]
            )
    
    def delete_chunk(self, chunk_id: str, collection_name: str = "general"):
        """Delete a chunk"""
        collection = self.collections.get(collection_name, self.collections["general"])
        collection.delete(ids=[chunk_id])
