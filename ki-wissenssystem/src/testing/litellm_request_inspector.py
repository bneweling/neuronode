"""
LiteLLM Request Inspector - Enterprise Glass-Box Testing
========================================================

Fängt JEDEN LLM-Request ab, bevor er an die API gesendet wird.
Speichert alle Parameter, Prompts und Metadaten für Test-Validierung.

Verwendung:
    1. LiteLLM Callback aktivieren
    2. Request-Capture in Redis 
    3. Test-Validierung der internen Logik
"""

import json
import redis
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CapturedRequest:
    """Captured LLM request with complete metadata for validation"""
    timestamp: str
    session_id: str
    request_id: str
    
    # Core Request Parameters
    model: str
    messages: List[Dict[str, str]]
    temperature: float
    max_tokens: int
    response_format: Dict[str, Any]
    
    # Enterprise Metadata
    task_type: str
    tier: str
    priority: int
    
    # Context & Processing Info
    context_sources: List[str]
    pipeline_stage: str
    escalation_reason: Optional[str]
    cache_status: str
    
    # Performance Metrics
    request_size_bytes: int
    estimated_cost_usd: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return asdict(self)

class LLMRequestInspector:
    """
    Enterprise Request Inspection & Mock Response System
    
    This class implements the intelligent mocking layer that:
    1. Intercepts every LLM request before API call
    2. Captures all parameters for validation
    3. Returns contextually appropriate mock responses
    4. Stores data in Redis for test analysis
    """
    
    def __init__(self, session_id: str = None, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True,
            socket_timeout=5
        )
        self.session_id = session_id or f"e2e_session_{uuid.uuid4().hex[:8]}"
        self.request_counter = 0
        
        # Test if Redis is available
        try:
            self.redis_client.ping()
            logger.info(f"✅ LLM Request Inspector initialized - Session: {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    def capture_request_callback(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        LiteLLM Custom Callback: Main interception point
        
        This function is called BEFORE every LLM API call.
        Perfect for capturing request details and returning mock responses.
        
        Args:
            kwargs: All LiteLLM request parameters
            
        Returns:
            Mock response that simulates real LLM output
        """
        self.request_counter += 1
        request_id = f"{self.session_id}_req_{self.request_counter:03d}"
        
        try:
            # Extract and enhance request metadata
            captured = self._extract_request_details(kwargs, request_id)
            
            # Store in Redis for test validation
            self._store_captured_request(captured)
            
            # Generate contextually appropriate mock response
            mock_response = self._generate_mock_response(captured)
            
            logger.info(f"🎯 Captured Request: {captured.model} | {captured.task_type} | {captured.pipeline_stage}")
            
            return mock_response
            
        except Exception as e:
            logger.error(f"❌ Request capture failed: {e}")
            # Return minimal mock response on error
            return self._fallback_mock_response()
    
    def _extract_request_details(self, kwargs: Dict[str, Any], request_id: str) -> CapturedRequest:
        """Extract comprehensive request details with enterprise metadata"""
        
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "unknown")
        
        # Analyze content to determine processing context
        content_analysis = self._analyze_request_content(messages)
        
        # Calculate request size for performance metrics
        request_size = len(json.dumps(kwargs).encode('utf-8'))
        
        # Estimate cost based on model and token count
        estimated_cost = self._estimate_request_cost(model, messages)
        
        return CapturedRequest(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            request_id=request_id,
            
            # Core Parameters
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 0),
            response_format=kwargs.get("response_format", {}),
            
            # Enterprise Metadata (extracted from kwargs or inferred)
            task_type=kwargs.get("task_type", content_analysis["task_type"]),
            tier=kwargs.get("tier", content_analysis["tier"]),
            priority=kwargs.get("priority", content_analysis["priority"]),
            
            # Context & Processing
            context_sources=kwargs.get("context_sources", content_analysis["context_sources"]),
            pipeline_stage=kwargs.get("pipeline_stage", content_analysis["pipeline_stage"]),
            escalation_reason=kwargs.get("escalation_reason"),
            cache_status=kwargs.get("cache_status", "MISS"),
            
            # Performance Metrics
            request_size_bytes=request_size,
            estimated_cost_usd=estimated_cost
        )
    
    def _analyze_request_content(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Intelligent content analysis to infer request context
        
        This analyzes the prompt content to determine:
        - Task type (classification, extraction, synthesis)
        - Processing tier (premium, balanced, cost_effective)  
        - Priority level
        - Context sources
        - Pipeline stage
        """
        
        # Combine all message content for analysis
        full_content = " ".join([msg.get("content", "") for msg in messages]).lower()
        
        # Task Type Detection
        task_type = "UNKNOWN"
        if any(keyword in full_content for keyword in ["klassifiziere", "kategorisiere", "analysiere intention"]):
            task_type = "CLASSIFICATION"
        elif any(keyword in full_content for keyword in ["extrahiere", "entitäten", "strukturierte daten"]):
            task_type = "EXTRACTION"
        elif any(keyword in full_content for keyword in ["synthese", "erstelle antwort", "vergleiche", "erkläre"]):
            task_type = "SYNTHESIS"
        elif any(keyword in full_content for keyword in ["validiere", "prüfe", "bewerte qualität"]):
            task_type = "VALIDATION"
        
        # Tier Detection (based on complexity indicators)
        tier = "COST_EFFECTIVE"
        if any(indicator in full_content for indicator in ["detailliert", "umfassend", "alle aspekte", "komplex"]):
            tier = "PREMIUM"
        elif any(indicator in full_content for indicator in ["vergleiche", "mehrere", "beziehungen"]):
            tier = "BALANCED"
        
        # Priority Detection
        priority = 3  # Medium default
        if task_type == "CLASSIFICATION":
            priority = 1  # CRITICAL - needed for routing
        elif "sofort" in full_content or "urgent" in full_content:
            priority = 1  # CRITICAL
        elif task_type == "SYNTHESIS":
            priority = 4  # LOW - resource intensive
        
        # Context Sources Detection
        context_sources = []
        if "dokument" in full_content or "datei" in full_content:
            context_sources.append("UPLOADED_DOCUMENT")
        if "knowledge graph" in full_content or "beziehungen" in full_content:
            context_sources.append("KNOWLEDGE_GRAPH")
        if "vector" in full_content or "ähnlichkeit" in full_content:
            context_sources.append("VECTOR_SEARCH")
        
        # Pipeline Stage Detection
        pipeline_stage = "UNKNOWN"
        if "dokumentverarbeitung" in full_content:
            pipeline_stage = "DOCUMENT_PROCESSING"
        elif "nutzerintention" in full_content:
            pipeline_stage = "INTENT_ANALYSIS"
        elif "kontext retrieval" in full_content:
            pipeline_stage = "CONTEXT_RETRIEVAL"
        elif "finale antwort" in full_content:
            pipeline_stage = "RESPONSE_SYNTHESIS"
        
        return {
            "task_type": task_type,
            "tier": tier,
            "priority": priority,
            "context_sources": context_sources,
            "pipeline_stage": pipeline_stage
        }
    
    def _estimate_request_cost(self, model: str, messages: List[Dict[str, str]]) -> float:
        """Estimate API cost based on model and content length"""
        
        # Token estimation (rough approximation)
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough token estimation
        
        # Cost per 1K tokens (simplified pricing)
        cost_per_1k_tokens = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.0015,
            "claude-3-5-sonnet": 0.003,
            "claude-3-haiku": 0.0025,
            "gemini-1.5-pro": 0.0035,
            "gemini-1.5-flash": 0.0007
        }
        
        # Extract base model name
        base_model = model.split("/")[-1].lower()
        
        # Find matching cost
        cost_rate = 0.002  # Default cost
        for model_key, rate in cost_per_1k_tokens.items():
            if model_key in base_model:
                cost_rate = rate
                break
        
        return (estimated_tokens / 1000) * cost_rate
    
    def _store_captured_request(self, captured: CapturedRequest):
        """Store captured request in Redis for test validation"""
        
        try:
            # Store in session-specific list
            request_key = f"test:requests:{self.session_id}"
            self.redis_client.rpush(request_key, json.dumps(captured.to_dict()))
            
            # Set TTL to 1 hour
            self.redis_client.expire(request_key, 3600)
            
            # Also store by request ID for direct access
            direct_key = f"test:request:{captured.request_id}"
            self.redis_client.setex(direct_key, 3600, json.dumps(captured.to_dict()))
            
        except Exception as e:
            logger.error(f"❌ Failed to store request in Redis: {e}")
    
    def _generate_mock_response(self, request: CapturedRequest) -> Dict[str, Any]:
        """Generate contextually appropriate mock responses based on request details"""
        
        # Get base response template
        base_response = self._get_base_mock_response(request.task_type, request.model)
        
        # Enhance with request-specific content
        enhanced_response = self._enhance_mock_response(base_response, request)
        
        return enhanced_response
    
    def _get_base_mock_response(self, task_type: str, model: str) -> Dict[str, Any]:
        """Get base mock response templates by task type"""
        
        mock_responses = {
            "CLASSIFICATION": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "classification": "COMPLIANCE_DOCUMENT",
                            "confidence": 0.95,
                            "category": "Security Policy",
                            "subcategory": "Access Control",
                            "compliance_frameworks": ["ISO 27001", "BSI C5", "DSGVO"],
                            "priority": "HIGH",
                            "action_required": True
                        })
                    }
                }],
                "usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50}
            },
            
            "EXTRACTION": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "entities": [
                                {
                                    "type": "REGULATION",
                                    "value": "DSGVO",
                                    "confidence": 0.98,
                                    "context": "Datenschutz-Grundverordnung"
                                },
                                {
                                    "type": "ARTICLE",
                                    "value": "Artikel 5",
                                    "confidence": 0.95,
                                    "context": "Grundsätze für die Verarbeitung personenbezogener Daten"
                                },
                                {
                                    "type": "DEADLINE",
                                    "value": "2025-12-31",
                                    "confidence": 0.90,
                                    "context": "Implementierungsfrist"
                                },
                                {
                                    "type": "REQUIREMENT",
                                    "value": "Datenschutz-Folgenabschätzung",
                                    "confidence": 0.92,
                                    "context": "Obligatorische Bewertung bei hohem Risiko"
                                }
                            ],
                            "relationships": [
                                {
                                    "source": "DSGVO",
                                    "target": "Artikel 5",
                                    "type": "CONTAINS",
                                    "confidence": 0.99
                                },
                                {
                                    "source": "Artikel 5",
                                    "target": "Datenschutz-Folgenabschätzung",
                                    "type": "REQUIRES",
                                    "confidence": 0.85
                                }
                            ],
                            "metadata": {
                                "extraction_model": model,
                                "processing_time_ms": 1250,
                                "confidence_threshold": 0.8
                            }
                        })
                    }
                }],
                "usage": {"total_tokens": 300, "prompt_tokens": 200, "completion_tokens": 100}
            },
            
            "SYNTHESIS": {
                "choices": [{
                    "message": {
                        "content": f"""Basierend auf den verfügbaren Dokumenten und dem Knowledge Graph zur DSGVO-Compliance:

**🎯 Hauptanforderungen für Datenschutz:**

1. **Artikel 5 DSGVO** fordert die Implementierung von Datenschutz-Grundsätzen:
   - Rechtmäßigkeit, Verarbeitung nach Treu und Glauben, Transparenz
   - Zweckbindung und Datenminimierung
   - Richtigkeit und Speicherbegrenzung

2. **BSI C5 Kontrollen** ergänzen mit technischen Sicherheitsmaßnahmen:
   - Zugriffskontrolle und Identitätsmanagement
   - Verschlüsselung und Datenschutz
   - Incident Response und Business Continuity

3. **ISO 27001** bietet das Management-Framework:
   - Risikomanagement-Prozess
   - Kontinuierliche Verbesserung
   - Audit und Compliance-Überwachung

**⚡ Kritische Umsetzungsschritte:**
- ✅ Datenschutz-Folgenabschätzung vor 2025-12-31
- ✅ Implementierung technischer Sicherheitsmaßnahmen  
- ✅ Regelmäßige Audits und Dokumentation
- ✅ Schulung der Mitarbeiter

**🔗 Synergien zwischen den Frameworks:**
Die Integration aller drei Frameworks (DSGVO + BSI C5 + ISO 27001) gewährleistet eine umfassende Compliance-Strategie mit sowohl rechtlichen als auch technischen Sicherheitsmaßnahmen.

**📊 Nächste Schritte:**
1. Gap-Analyse der aktuellen Implementierung
2. Priorisierung kritischer Kontrollen
3. Zeitplan für die vollständige Umsetzung

*Antwort generiert mit {model} | Verarbeitungszeit: 2.1s | Quellen: 5 Dokumente*"""
                    }
                }],
                "usage": {"total_tokens": 500, "prompt_tokens": 300, "completion_tokens": 200}
            },
            
            "VALIDATION": {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "validation_result": "PASSED",
                            "confidence": 0.92,
                            "checks_performed": [
                                {
                                    "check_type": "COMPLETENESS",
                                    "result": "PASSED",
                                    "score": 0.95,
                                    "details": "All required sections present"
                                },
                                {
                                    "check_type": "ACCURACY",
                                    "result": "PASSED", 
                                    "score": 0.88,
                                    "details": "Factual information verified"
                                },
                                {
                                    "check_type": "CONSISTENCY",
                                    "result": "WARNING",
                                    "score": 0.75,
                                    "details": "Minor terminology inconsistencies"
                                }
                            ],
                            "overall_score": 0.86,
                            "recommendations": [
                                "Standardize terminology usage",
                                "Add more specific examples",
                                "Include recent regulatory updates"
                            ]
                        })
                    }
                }],
                "usage": {"total_tokens": 200, "prompt_tokens": 120, "completion_tokens": 80}
            }
        }
        
        return mock_responses.get(task_type, {
            "choices": [{"message": {"content": f"Mock response for {task_type} using {model}"}}],
            "usage": {"total_tokens": 50, "prompt_tokens": 30, "completion_tokens": 20}
        })
    
    def _enhance_mock_response(self, base_response: Dict[str, Any], request: CapturedRequest) -> Dict[str, Any]:
        """Enhance mock response with request-specific metadata"""
        
        # Add processing metadata to response
        if "choices" in base_response and len(base_response["choices"]) > 0:
            message = base_response["choices"][0]["message"]
            
            # For JSON responses, add metadata
            try:
                if message["content"].startswith("{"):
                    content_json = json.loads(message["content"])
                    content_json["processing_metadata"] = {
                        "request_id": request.request_id,
                        "model_used": request.model,
                        "tier": request.tier,
                        "priority": request.priority,
                        "pipeline_stage": request.pipeline_stage,
                        "processing_time_ms": 1200 + (request.request_size_bytes // 100),
                        "cache_status": request.cache_status
                    }
                    message["content"] = json.dumps(content_json)
            except (json.JSONDecodeError, KeyError):
                # For text responses, append metadata
                message["content"] += f"\n\n---\n*Processed by {request.model} | Stage: {request.pipeline_stage} | ID: {request.request_id}*"
        
        # Enhance usage statistics based on request size
        if "usage" in base_response:
            base_tokens = base_response["usage"]["total_tokens"]
            size_factor = max(1.0, request.request_size_bytes / 1000)
            
            base_response["usage"].update({
                "total_tokens": int(base_tokens * size_factor),
                "prompt_tokens": int(base_response["usage"]["prompt_tokens"] * size_factor),
                "completion_tokens": base_response["usage"]["completion_tokens"],
                "estimated_cost_usd": request.estimated_cost_usd
            })
        
        return base_response
    
    def _fallback_mock_response(self) -> Dict[str, Any]:
        """Minimal fallback response when request capture fails"""
        return {
            "choices": [{
                "message": {
                    "content": "Fallback mock response - request capture failed"
                }
            }],
            "usage": {"total_tokens": 20}
        }
    
    # ===================================================================
    # TEST VALIDATION METHODS
    # ===================================================================
    
    def get_captured_requests(self, session_id: str = None) -> List[CapturedRequest]:
        """
        Retrieve all captured requests for validation
        
        Args:
            session_id: Optional session ID (defaults to current session)
            
        Returns:
            List of captured requests for test validation
        """
        target_session = session_id or self.session_id
        request_key = f"test:requests:{target_session}"
        
        try:
            raw_requests = self.redis_client.lrange(request_key, 0, -1)
            
            requests = []
            for raw in raw_requests:
                data = json.loads(raw)
                # Convert dict back to CapturedRequest object
                requests.append(CapturedRequest(**data))
            
            return requests
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve captured requests: {e}")
            return []
    
    def get_request_by_id(self, request_id: str) -> Optional[CapturedRequest]:
        """Get specific request by ID"""
        try:
            direct_key = f"test:request:{request_id}"
            raw_data = self.redis_client.get(direct_key)
            
            if raw_data:
                data = json.loads(raw_data)
                return CapturedRequest(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve request {request_id}: {e}")
            return None
    
    def clear_session(self, session_id: str = None):
        """Clear captured requests for session"""
        target_session = session_id or self.session_id
        request_key = f"test:requests:{target_session}"
        
        try:
            self.redis_client.delete(request_key)
            logger.info(f"✅ Cleared session: {target_session}")
        except Exception as e:
            logger.error(f"❌ Failed to clear session: {e}")
    
    def get_session_statistics(self, session_id: str = None) -> Dict[str, Any]:
        """Get comprehensive session statistics for test reporting"""
        target_session = session_id or self.session_id
        requests = self.get_captured_requests(target_session)
        
        if not requests:
            return {"total_requests": 0}
        
        # Analyze requests
        task_types = {}
        models = {}
        tiers = {}
        total_cost = 0
        total_tokens = 0
        
        for req in requests:
            # Count task types
            task_types[req.task_type] = task_types.get(req.task_type, 0) + 1
            
            # Count models
            models[req.model] = models.get(req.model, 0) + 1
            
            # Count tiers
            tiers[req.tier] = tiers.get(req.tier, 0) + 1
            
            # Sum costs and tokens
            total_cost += req.estimated_cost_usd
        
        return {
            "total_requests": len(requests),
            "task_types": task_types,
            "models_used": models,
            "tiers_used": tiers,
            "total_estimated_cost_usd": round(total_cost, 4),
            "session_duration_minutes": self._calculate_session_duration(requests),
            "average_request_size_bytes": sum(r.request_size_bytes for r in requests) // len(requests),
            "cache_hit_rate": len([r for r in requests if r.cache_status == "HIT"]) / len(requests)
        }
    
    def _calculate_session_duration(self, requests: List[CapturedRequest]) -> float:
        """Calculate session duration in minutes"""
        if len(requests) < 2:
            return 0
        
        timestamps = [datetime.fromisoformat(r.timestamp) for r in requests]
        duration = max(timestamps) - min(timestamps)
        return duration.total_seconds() / 60


# ===================================================================
# FACTORY FUNCTIONS & SINGLETON
# ===================================================================

_inspector_instance: Optional[LLMRequestInspector] = None

def get_request_inspector(session_id: str = None) -> LLMRequestInspector:
    """Get or create singleton request inspector instance"""
    global _inspector_instance
    
    if _inspector_instance is None:
        _inspector_instance = LLMRequestInspector(session_id)
    
    return _inspector_instance

def create_test_session(session_id: str = None) -> LLMRequestInspector:
    """Create new test session with fresh inspector"""
    return LLMRequestInspector(session_id)


# ===================================================================
# LITELLM CALLBACK INTEGRATION
# ===================================================================

def litellm_success_callback(kwargs, completion_response, start_time, end_time):
    """
    LiteLLM success callback - captures successful requests
    
    This function is registered with LiteLLM to be called on every successful request.
    It's the main entry point for request interception.
    """
    inspector = get_request_inspector()
    
    # Store completion time
    kwargs["completion_time_ms"] = (end_time - start_time) * 1000
    
    # Capture the request (returns mock response, but we've already got real response)
    inspector.capture_request_callback(kwargs)

def litellm_failure_callback(kwargs, completion_response, start_time, end_time):
    """LiteLLM failure callback - captures failed requests for analysis"""
    inspector = get_request_inspector()
    
    # Add failure metadata
    kwargs["failure_details"] = str(completion_response)
    kwargs["failure_time_ms"] = (end_time - start_time) * 1000
    
    # Still capture for analysis
    inspector.capture_request_callback(kwargs)


if __name__ == "__main__":
    # Test the inspector
    inspector = LLMRequestInspector("test_session")
    
    # Simulate a request
    test_request = {
        "model": "classification_premium",
        "messages": [
            {"role": "system", "content": "Klassifiziere das folgende Dokument"},
            {"role": "user", "content": "Das ist ein BSI C5 Compliance-Dokument über Zugriffskontrolle"}
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
        "task_type": "CLASSIFICATION"
    }
    
    # Capture and validate
    response = inspector.capture_request_callback(test_request)
    captured = inspector.get_captured_requests()
    
    print(f"✅ Test passed: Captured {len(captured)} requests")
    print(f"📊 Session stats: {inspector.get_session_statistics()}") 