from typing import Dict, Any, Optional, List
import asyncio
import time
from datetime import datetime

from src.retrievers.intent_analyzer import IntentAnalyzer
from src.retrievers.hybrid_retriever import HybridRetriever
from src.retrievers.response_synthesizer import ResponseSynthesizer, SynthesizedResponse
import logging

logger = logging.getLogger(__name__)

class QueryOrchestrator:
    """Main orchestrator for handling user queries"""
    
    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.retriever = HybridRetriever()
        self.synthesizer = ResponseSynthesizer()
        
        # Cache for frequent queries
        self.query_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def process_query(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Process a user query end-to-end"""
        
        start_time = time.time()
        
        # Check cache
        if use_cache:
            cached_response = self._get_cached_response(query)
            if cached_response:
                logger.info(f"Returning cached response for query: {query[:50]}...")
                return cached_response
        
        try:
            # Step 1: Analyze query intent
            logger.info(f"Analyzing query: {query[:100]}...")
            analysis = await self.intent_analyzer.analyze_query(query)
            
            # Enhance with synonyms
            analysis = self.intent_analyzer.enhance_query_with_synonyms(analysis)
            
            # Step 2: Retrieve relevant information
            logger.info(f"Retrieving information for intent: {analysis.primary_intent}")
            retrieval_results = await self.retriever.retrieve(
                query, 
                analysis,
                max_results=20
            )
            
            logger.info(f"Retrieved {len(retrieval_results)} results")
            
            # Step 3: Synthesize response
            logger.info("Synthesizing response...")
            response = await self.synthesizer.synthesize_response(
                query,
                analysis,
                retrieval_results
            )
            
            # Prepare final response
            processing_time = time.time() - start_time
            
            result = {
                "query": query,
                "response": response.answer,
                "sources": response.sources,
                "confidence": response.confidence,
                "follow_up_questions": response.follow_up_questions,
                "metadata": {
                    **response.metadata,
                    "processing_time": round(processing_time, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_context": user_context
                },
                "analysis": {
                    "intent": analysis.primary_intent.value,
                    "entities": analysis.entities,
                    "keywords": analysis.search_keywords
                }
            }
            
            # Cache successful responses
            if use_cache and response.confidence > 0.7:
                self._cache_response(query, result)
            
            logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            
            # Return error response
            return {
                "query": query,
                "response": f"Entschuldigung, bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "metadata": {
                    "error": True,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def process_conversation(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a query in conversation context"""
        
        # Extract current query and history
        current_query = messages[-1]["content"]
        history = messages[:-1]
        
        # Build context from history
        context = self._build_conversation_context(history)
        
        # Add context to query if relevant
        if context:
            enhanced_query = f"{context}\n\nAktuelle Frage: {current_query}"
        else:
            enhanced_query = current_query
        
        # Process with context
        result = await self.process_query(
            enhanced_query,
            user_context={
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "has_history": len(history) > 0
            }
        )
        
        return result
    
    def _build_conversation_context(self, history: List[Dict[str, str]]) -> str:
        """Build context from conversation history"""
        if not history:
            return ""
        
        # Take last 2 exchanges for context
        recent_history = history[-4:] if len(history) >= 4 else history
        
        context_parts = ["Kontext aus vorherigem Gespräch:"]
        for msg in recent_history:
            role = "Nutzer" if msg["role"] == "user" else "Assistent"
            # Truncate long messages
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get response from cache"""
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
        """Cache a response"""
        cache_key = self._get_cache_key(query)
        
        self.query_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.query_cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(
                self.query_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            for key, _ in sorted_cache[:100]:
                del self.query_cache[key]
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Normalize query for caching
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized
    
    async def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get query suggestions based on partial input"""
        # This could be enhanced with:
        # - Common query patterns
        # - Previous successful queries
        # - Entity-based suggestions
        
        suggestions = []
        
        # Common query starters
        starters = [
            "Was fordert BSI C5 zu",
            "Wie implementiere ich",
            "Was ist der Unterschied zwischen",
            "Zeige mir alle Controls für",
            "Best Practices für",
            "Wie erfülle ich"
        ]
        
        for starter in starters:
            if starter.lower().startswith(partial_query.lower()):
                suggestions.append(starter)
        
        return suggestions[:5]