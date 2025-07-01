import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from src.config.settings import settings
import uuid
import logging
import asyncio

from src.config.exceptions import (
    ErrorCode, DatabaseError, SystemError
)
from src.utils.error_handler import error_handler, handle_exceptions, retry_with_backoff

logger = logging.getLogger(__name__)


class ChromaClient:
    """Enterprise ChromaDB client with LiteLLM embedding integration"""
    
    def __init__(self):
        """Initialize ChromaDB client with enterprise error handling"""
        try:
            # ChromaDB Configuration
            self.settings = Settings(
                persist_directory="/chroma/chroma",
                is_persistent=True,
                anonymized_telemetry=False
            )
            
            # Initialize ChromaDB client  
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=self.settings
            )
            
            # Initialize LiteLLM client for embeddings (enterprise-consistent approach)
            self.litellm_client = None  # Will be initialized lazily
            self._init_collections()
            
        except Exception as e:
            db_error = DatabaseError(
                f"Failed to initialize ChromaDB client: {str(e)}",
                ErrorCode.CHROMADB_CONNECTION_FAILED,
                {"host": settings.chroma_host, "port": settings.chroma_port},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error

    def _get_litellm_client(self):
        """Lazy initialization of LiteLLM client for embeddings"""
        if self.litellm_client is None:
            from src.llm.litellm_client import get_litellm_client
            self.litellm_client = get_litellm_client()
        return self.litellm_client

    async def _get_embedding_async(self, text: str) -> List[float]:
        """Generate embedding using LiteLLM (enterprise-consistent approach)"""
        try:
            client = self._get_litellm_client()
            
            # Use LiteLLM embedding endpoint with profile-system integration
            from src.models.llm_models import EmbeddingRequest
            
            embedding_request = EmbeddingRequest(
                input=[text],  # LiteLLM expects a list
                model="embeddings"  # This will be resolved via profile system
            )
            
            response = await client.embed(embedding_request)
            
            # Extract the embedding vector
            if response.data and len(response.data) > 0:
                return response.data[0].embedding
            else:
                raise ValueError("No embedding data received from LiteLLM")
                
        except Exception as e:
            db_error = DatabaseError(
                f"Error generating embedding via LiteLLM: {str(e)}",
                ErrorCode.CHROMADB_QUERY_FAILED,
                {"text_length": len(text), "model": "embeddings"},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error
    
    def _get_embedding(self, text: str) -> List[float]:
        """Synchronous wrapper for embedding generation"""
        try:
            # Run async embedding in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._get_embedding_async(text))
            finally:
                loop.close()
        except Exception as e:
            # Fallback for sync contexts - use current event loop if available
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, need to create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.new_event_loop().run_until_complete(
                                self._get_embedding_async(text)
                            )
                        )
                        return future.result()
                else:
                    return loop.run_until_complete(self._get_embedding_async(text))
            except Exception as async_error:
                db_error = DatabaseError(
                    f"Error in embedding generation: {str(async_error)}",
                    ErrorCode.CHROMADB_QUERY_FAILED,
                    {"text_length": len(text), "original_error": str(e)},
                    cause=async_error
                )
                error_handler.log_error(db_error)
                raise db_error

    def _init_collections(self):
        """Initialize collections for different document types with enterprise error handling"""
        self.collections = {}
        
        collection_configs = [
            ("compliance", "compliance_docs", "BSI, ISO, NIST compliance documents"),
            ("technical", "technical_docs", "Technical documentation and whitepapers"),
            ("general", "general_knowledge", "General knowledge chunks")
        ]
        
        for key, name, description in collection_configs:
            try:
                # Try to get existing collection first
                try:
                    collection = self.client.get_collection(name=name)
                    logger.info(f"Using existing collection: {name}")
                    self.collections[key] = collection
                    continue
                except Exception:
                    # Collection doesn't exist, create new one
                    pass
                
                # Create new collection
                logger.info(f"Creating collection: {name}")
                collection = self.client.create_collection(
                    name=name,
                    metadata={"description": description}
                )
                self.collections[key] = collection
                logger.info(f"Successfully created collection: {name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize collection {name}: {e}")
                # Try to use a fallback approach
                try:
                    collection = self.client.get_or_create_collection(
                        name=name,
                        metadata={"description": description}
                    )
                    self.collections[key] = collection
                    logger.info(f"Successfully got or created collection: {name}")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for collection {name}: {fallback_error}")
                    continue  # Skip this collection but don't fail completely
        
        # Create a simple fallback collection if needed
        if not self.collections:
            try:
                collection = self.client.get_or_create_collection(
                    name="default_collection",
                    metadata={"description": "Default fallback collection"}
                )
                self.collections["general"] = collection
                logger.info("Created fallback default collection")
            except Exception as e:
                logger.error(f"Failed to create fallback collection: {e}")
                # Last resort - don't fail the entire system
                logger.warning("Continuing without ChromaDB collections - some features may be limited")
                self.collections = {"general": None}  # Placeholder

    def _reset_chromadb(self):
        """Reset ChromaDB by clearing all existing collections"""
        try:
            collections = self.client.list_collections()
            for collection in collections:
                try:
                    self.client.delete_collection(name=collection.name)
                    logger.info(f"Deleted existing collection: {collection.name}")
                except Exception as e:
                    logger.warning(f"Could not delete collection {collection.name}: {e}")
        except Exception as e:
            logger.warning(f"Could not list collections for reset: {e}")

    def add_chunk(self, chunk: Dict[str, Any], collection_name: str = "general") -> str:
        """Add a knowledge chunk to ChromaDB collection"""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.collections.get("general")
                if not collection:
                    raise ValueError(f"No collection available for {collection_name}")
            
            # Generate embedding for the chunk content
            content = chunk.get("content", "")
            if not content:
                raise ValueError("Chunk content cannot be empty")
            
            embedding = self._get_embedding(content)
            
            # Generate unique ID
            chunk_id = str(uuid.uuid4())
            
            # Prepare metadata
            metadata = {
                "source": chunk.get("source", "unknown"),
                "document_type": chunk.get("document_type", "unknown"),
                "chunk_index": chunk.get("chunk_index", 0),
                "quality_score": chunk.get("quality_score", 0.0)
            }
            
            # Add to ChromaDB
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Added chunk {chunk_id} to collection {collection_name}")
            return chunk_id
            
        except Exception as e:
            db_error = DatabaseError(
                f"Failed to add chunk to ChromaDB: {str(e)}",
                ErrorCode.CHROMADB_QUERY_FAILED,
                {"collection": collection_name, "chunk_size": len(str(chunk))},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error

    def similarity_search(self, query: str, collection_name: str = "general", n_results: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search in ChromaDB collection"""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.collections.get("general")
                if not collection:
                    return []
            
            # Generate embedding for query
            query_embedding = self._get_embedding(query)
            
            # Perform search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results and "documents" in results:
                for i, doc in enumerate(results["documents"][0]):
                    result = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if "metadatas" in results else {},
                        "distance": results["distances"][0][i] if "distances" in results else 0.0
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query in {collection_name}")
            return formatted_results
            
        except Exception as e:
            db_error = DatabaseError(
                f"Failed to perform similarity search: {str(e)}",
                ErrorCode.CHROMADB_QUERY_FAILED,
                {"collection": collection_name, "query_length": len(query)},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error

    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about all collections"""
        try:
            stats = {}
            for name, collection in self.collections.items():
                count = collection.count()
                stats[name] = count
            
            return stats
            
        except Exception as e:
            db_error = DatabaseError(
                f"Failed to get collection statistics: {str(e)}",
                ErrorCode.CHROMADB_QUERY_FAILED,
                {},
                cause=e
            )
            error_handler.log_error(db_error)
            raise db_error

    def health_check(self) -> bool:
        """Check if ChromaDB is healthy"""
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False
