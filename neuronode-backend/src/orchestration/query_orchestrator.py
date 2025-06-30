from typing import Dict, Any, Optional, List
import asyncio
import time
from datetime import datetime

# Updated imports for migrated services
from src.retrievers.intent_analyzer import IntentAnalyzer
from src.retrievers.hybrid_retriever import HybridRetriever
from src.retrievers.response_synthesizer import ResponseSynthesizer
from src.models.llm_models import QueryAnalysis, SynthesizedResponse
import logging

from src.config.exceptions import (
    ErrorCode, QueryProcessingError, LLMServiceError, DatabaseError
)
from src.utils.error_handler import error_handler, handle_exceptions, retry_with_backoff

logger = logging.getLogger(__name__)

class QueryOrchestrator:
    """
    Production Query Orchestrator with LiteLLM v1.72.6 Integration
    
    Coordinates the complete RAG pipeline using enterprise-grade LiteLLM-based services:
    - IntentAnalyzer (CRITICAL priority, sub-200ms performance)
    - HybridRetriever (graph + vector search coordination)  
    - ResponseSynthesizer (Quality-focused response generation)
    
    Enterprise Features:
    - Strategic request prioritization with dynamic model selection
    - End-to-end performance monitoring and metrics
    - Enterprise error handling with comprehensive fallbacks
    - Conversation context management and caching
    - Intelligent caching with TTL and memory optimization
    """
    
    def __init__(self, 
                 intent_analyzer: Optional[IntentAnalyzer] = None,
                 hybrid_retriever: Optional[HybridRetriever] = None,
                 response_synthesizer: Optional[ResponseSynthesizer] = None):
        """
        Initialize with dependency injection for enterprise-grade testing and flexibility
        
        Args:
            intent_analyzer: Enhanced intent analyzer with LiteLLM integration
            hybrid_retriever: Hybrid retrieval system (graph + vector)
            response_synthesizer: Enhanced response synthesizer with LiteLLM integration
        """
        # Dependency injection with fallback initialization
        self.intent_analyzer = intent_analyzer or IntentAnalyzer()
        self.retriever = hybrid_retriever or HybridRetriever()
        self.synthesizer = response_synthesizer or ResponseSynthesizer()
        
        # Enterprise caching with performance optimization
        self.query_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Performance tracking
        self.performance_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
            "error_rate": 0.0
        }
        
        logger.info("QueryOrchestrator initialized with LiteLLM v1.72.6 services")
    
    async def orchestrate_query(
        self,
        user_query: str,
        user_context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Complete end-to-end query orchestration with strategic service coordination
        
        Pipeline:
        1. Intent Analysis (CRITICAL priority, pattern-based + LLM hybrid)
        2. Retrieval Coordination (graph + vector search optimization)
        3. Response Synthesis (LOW priority, quality-over-speed)
        4. Performance tracking and caching
        
        Args:
            user_query: User's natural language query
            user_context: Additional context metadata
            use_cache: Enable intelligent caching
            conversation_context: Previous conversation messages for context
            
        Returns:
            Complete response with sources, metadata, and performance metrics
        """
        
        start_time = time.time()
        self.performance_stats["total_queries"] += 1
        
        # Enhanced query with conversation context if available
        if conversation_context:
            enhanced_query = self._build_conversation_enhanced_query(user_query, conversation_context)
        else:
            enhanced_query = user_query
        
        # Check intelligent cache first
        if use_cache:
            cached_response = self._get_cached_response(enhanced_query)
            if cached_response:
                self.performance_stats["cache_hits"] += 1
                logger.info(f"Cache hit for query: {user_query[:50]}...")
                return self._add_performance_metadata(cached_response, time.time() - start_time, cached=True)
        
        try:
            # STEP 1: Intent Analysis (CRITICAL Priority - Sub-200ms target)
            logger.info(f"🔍 Analyzing query intent (CRITICAL priority): {user_query[:100]}...")
            analysis_start = time.time()
            
            query_analysis = await self.intent_analyzer.analyze_query(enhanced_query)
            
            analysis_time = time.time() - analysis_start
            logger.info(f"✅ Intent analysis completed in {analysis_time*1000:.1f}ms (target: <200ms)")
            
            # STEP 2: Hybrid Retrieval (Coordinated graph + vector search)
            logger.info(f"📚 Retrieving information for intent: {query_analysis.primary_intent}")
            retrieval_start = time.time()
            
            retrieval_results = await self.retriever.retrieve(
                enhanced_query, 
                query_analysis,
                max_results=20
            )
            
            retrieval_time = time.time() - retrieval_start
            logger.info(f"✅ Retrieved {len(retrieval_results)} results in {retrieval_time*1000:.1f}ms")
            
            # STEP 3: Response Synthesis (LOW Priority - Quality focused)
            logger.info("🎯 Synthesizing response (LOW priority for quality)...")
            synthesis_start = time.time()
            
            synthesized_response = await self.synthesizer.synthesize_response(
                enhanced_query,
                query_analysis,
                retrieval_results,
                user_context=user_context
            )
            
            synthesis_time = time.time() - synthesis_start
            logger.info(f"✅ Response synthesized in {synthesis_time*1000:.1f}ms")
            
            # STEP 4: Build final enterprise response
            total_processing_time = time.time() - start_time
            
            final_response = self._build_final_response(
                user_query,
                query_analysis,
                synthesized_response,
                total_processing_time,
                user_context,
                performance_breakdown={
                    "intent_analysis_ms": round(analysis_time * 1000, 1),
                    "retrieval_ms": round(retrieval_time * 1000, 1),
                    "synthesis_ms": round(synthesis_time * 1000, 1),
                    "total_ms": round(total_processing_time * 1000, 1)
                }
            )
            
            # Cache high-confidence responses
            if use_cache and synthesized_response.confidence > 0.7:
                self._cache_response(enhanced_query, final_response)
            
            # Update performance statistics
            self._update_performance_stats(total_processing_time, success=True)
            
            logger.info(f"🚀 Query orchestration completed successfully in {total_processing_time:.2f}s")
            return final_response
            
        except QueryProcessingError as e:
            return await self._handle_processing_error(e, user_query, start_time)
        except Exception as e:
            return await self._handle_unexpected_error(e, user_query, start_time)
    
    # Legacy compatibility wrapper
    async def process_query(self, *args, **kwargs) -> Dict[str, Any]:
        """Legacy compatibility wrapper for existing API calls"""
        return await self.orchestrate_query(*args, **kwargs)
    
    async def process_conversation(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a query with full conversation context"""
        
        if not messages:
            raise QueryProcessingError("No messages provided", ErrorCode.QUERY_ANALYSIS_FAILED)
        
        # Extract current query and history
        current_query = messages[-1]["content"]
        conversation_history = messages[:-1]
        
        # Use the enhanced orchestration with conversation context
        result = await self.orchestrate_query(
            user_query=current_query,
            user_context={
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "has_history": len(conversation_history) > 0
            },
            conversation_context=conversation_history
        )
        
        return result
    
    def _build_conversation_enhanced_query(self, current_query: str, history: List[Dict[str, str]]) -> str:
        """Build enhanced query with conversation context"""
        if not history:
            return current_query
        
        # Take last 2 exchanges for context (4 messages max)
        recent_history = history[-4:] if len(history) >= 4 else history
        
        context_parts = ["Kontext aus vorherigem Gespräch:"]
        for msg in recent_history:
            role = "Nutzer" if msg["role"] == "user" else "Assistent"
            # Truncate long messages for efficiency
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            context_parts.append(f"{role}: {content}")
        
        context = "\n".join(context_parts)
        return f"{context}\n\nAktuelle Frage: {current_query}"
    
    def _build_final_response(
        self,
        original_query: str,
        analysis: QueryAnalysis,
        response: SynthesizedResponse,
        processing_time: float,
        user_context: Optional[Dict[str, Any]],
        performance_breakdown: Dict[str, float]
    ) -> Dict[str, Any]:
        """Build the final enterprise-grade response with comprehensive metadata"""
        
        return {
            "query": original_query,
            "response": response.answer,
            "sources": response.sources,
            "confidence": response.confidence,
            "follow_up_questions": response.follow_up_questions,
            "metadata": {
                **response.metadata,
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "user_context": user_context,
                "performance_breakdown": performance_breakdown,
                "orchestrator_version": "QueryOrchestrator_v1.72.6",
                "litellm_integration": True
            },
            "analysis": {
                "intent": analysis.primary_intent.value,
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.entity_type,
                        "confidence": entity.confidence
                    }
                    for entity in analysis.entities
                ],
                "keywords": analysis.search_keywords,
                "complexity": analysis.complexity_score,
                "confidence": analysis.confidence
            }
        }
    
    async def _handle_processing_error(self, error: QueryProcessingError, query: str, start_time: float) -> Dict[str, Any]:
        """Handle structured processing errors with fallback strategies"""
        processing_time = time.time() - start_time
        error_handler.log_error(error, {"query": query[:100], "processing_time": processing_time})
        
        self._update_performance_stats(processing_time, success=False)
        
        return {
            "query": query,
            "response": f"Ihre Anfrage konnte nicht vollständig verarbeitet werden (Fehlercode: {error.error_code.value}). Bitte versuchen Sie es erneut oder formulieren Sie Ihre Frage anders.",
            "sources": [],
            "confidence": 0.0,
            "follow_up_questions": [
                "Können Sie Ihre Frage anders formulieren?",
                "Suchen Sie nach einem spezifischen Standard oder Control?",
                "Benötigen Sie Implementierungsdetails oder allgemeine Informationen?"
            ],
            "metadata": {
                "error": True,
                "error_code": error.error_code.value,
                "error_message": error.message,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": round(processing_time, 2),
                "orchestrator_version": "QueryOrchestrator_v1.72.6"
            }
        }
    
    async def _handle_unexpected_error(self, error: Exception, query: str, start_time: float) -> Dict[str, Any]:
        """Handle unexpected errors with comprehensive logging and user-friendly response"""
        processing_time = time.time() - start_time
        
        # Wrap unexpected errors in structured exception
        structured_error = QueryProcessingError(
            f"Unexpected error in query orchestration: {str(error)}",
            ErrorCode.QUERY_ANALYSIS_FAILED,
            {"query": query[:100], "processing_time": processing_time, "error_type": type(error).__name__},
            cause=error
        )
        error_handler.log_error(structured_error)
        
        self._update_performance_stats(processing_time, success=False)
        
        return {
            "query": query,
            "response": "Es ist ein unerwarteter Systemfehler aufgetreten. Das Entwicklungsteam wurde benachrichtigt. Bitte versuchen Sie es in wenigen Minuten erneut.",
            "sources": [],
            "confidence": 0.0,
            "follow_up_questions": [
                "Versuchen Sie es mit einer einfacheren Frage",
                "Kontaktieren Sie den Support falls das Problem weiterhin besteht"
            ],
            "metadata": {
                "error": True,
                "error_code": structured_error.error_code.value,
                "error_type": "unexpected_error",
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": round(processing_time, 2),
                "orchestrator_version": "QueryOrchestrator_v1.72.6"
            }
        }
    
    def _add_performance_metadata(self, response: Dict[str, Any], processing_time: float, cached: bool = False) -> Dict[str, Any]:
        """Add performance metadata to cached responses"""
        if "metadata" not in response:
            response["metadata"] = {}
        
        response["metadata"].update({
            "processing_time": round(processing_time, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "cached": cached,
            "orchestrator_version": "QueryOrchestrator_v1.72.6"
        })
        
        return response
    
    def _update_performance_stats(self, processing_time: float, success: bool):
        """Update internal performance statistics"""
        # Update average processing time
        total_queries = self.performance_stats["total_queries"]
        current_avg = self.performance_stats["avg_processing_time"]
        self.performance_stats["avg_processing_time"] = (
            (current_avg * (total_queries - 1) + processing_time) / total_queries
        )
        
        # Update error rate
        if not success:
            errors = total_queries * self.performance_stats["error_rate"] + 1
            self.performance_stats["error_rate"] = errors / total_queries
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            **self.performance_stats,
            "cache_hit_rate": self.performance_stats["cache_hits"] / max(self.performance_stats["total_queries"], 1),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get response from intelligent cache"""
        cache_key = self._get_cache_key(query)
        
        if cache_key in self.query_cache:
            cached_item = self.query_cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["response"]
            else:
                # Remove expired cache
                del self.query_cache[cache_key]
        
        return None
    
    def _cache_response(self, query: str, response: Dict[str, Any]):
        """Cache a high-quality response"""
        cache_key = self._get_cache_key(query)
        
        self.query_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Limit cache size for memory efficiency
        if len(self.query_cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(
                self.query_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            for key, _ in sorted_cache[:100]:
                del self.query_cache[key]
    
    def _get_cache_key(self, query: str) -> str:
        """Generate normalized cache key for query"""
        # Normalize query for caching
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized
    
    async def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get intelligent query suggestions based on partial input"""
        suggestions = []
        
        # Common query starters for compliance and security domain
        starters = [
            "Was fordert BSI C5 zu",
            "Wie implementiere ich",
            "Was ist der Unterschied zwischen",
            "Zeige mir alle Controls für",
            "Best Practices für",
            "Wie erfülle ich",
            "Welche Anforderungen gibt es für",
            "Wie kann ich nachweisen dass"
        ]
        
        for starter in starters:
            if starter.lower().startswith(partial_query.lower()):
                suggestions.append(starter)
        
        return suggestions[:5]

# ===================================================================
# PRODUCTION STATUS: ENTERPRISE-READY
# ===================================================================

# Enhanced → Final class migration completed 
# QueryOrchestrator is now the production-ready final class