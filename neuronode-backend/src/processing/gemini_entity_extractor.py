"""
Gemini Entity Extractor Service

Ersetzt die alte Regex-basierte NER-Extraktion durch API-basierte
Entitätserkennung mit Google Gemini. Implementiert Caching,
Batching und robuste Fehlerbehandlung.

Dies ist das Pilotprojekt für Phase 2 der KI-System-Transformation.
"""

import json
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys
import asyncio

# Füge das Konfigurationsmodul hinzu
sys.path.append(str(Path(__file__).parent.parent))

# Migration: New LiteLLM imports
from ..llm.litellm_client import (
    get_litellm_client, 
    LiteLLMClient,
    RequestPriorityLevel,
    LiteLLMExceptionMapper
)
from ..llm.model_manager import get_model_manager, TaskType, ModelTier
from ..models.llm_models import LLMRequest, LLMMessage
from ..config.prompt_loader import get_prompt

# Legacy imports removed:
# import google.generativeai as genai
# from src.config.ai_services_loader import get_config

# Optional imports with fallbacks
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """
    Datenklasse für eine extrahierte Entität.
    """
    text: str
    category: str
    confidence: float
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


@dataclass
class ExtractionResult:
    """
    Datenklasse für das Ergebnis einer NER-Extraktion.
    """
    entities: List[ExtractedEntity]
    chunk_id: str
    processing_time_ms: int
    source: str  # 'cache', 'api', 'fallback'
    api_cost_estimate: Optional[float] = None


class GeminiEntityExtractor:
    """
    Enhanced Entity Extractor with LiteLLM integration
    
    MIGRATION FEATURES:
    - Uses extraction-primary model (Gemini Pro for structured output)
    - BATCH priority for quality validation tasks
    - Redis caching with deterministic cache keys
    - Enhanced error handling with LiteLLM exception mapping
    - Backward compatible API for existing quality validation
    - Performance optimized for batch entity extraction
    """
    
    def __init__(self):
        """
        Initialisiert den Enhanced Entity Extractor.
        """
        self.litellm_client = get_litellm_client()
        self._setup_redis_client()
        self.fallback_extractor = None  # Legacy fallback if needed
        
        # Performance-Metriken
        self.total_api_calls = 0
        self.total_cache_hits = 0
        self.total_processing_time = 0.0
        
        # Configuration
        self.cache_ttl = 2592000  # 30 days for document entity extraction
        
        logger.info("Enhanced GeminiEntityExtractor initialized with LiteLLM client")
    
    def _setup_redis_client(self) -> None:
        """
        Konfiguriert den Redis Client für Caching.
        """
        if not redis:
            logger.warning("Redis nicht installiert - Cache deaktiviert")
            self.redis_client = None
            return
        
        try:
            self.redis_client = redis.Redis(
                host="localhost",  # Default configuration
                port=6379,
                db=0,
                decode_responses=True
            )
            
            # Test-Verbindung
            self.redis_client.ping()
            logger.info(f"Redis Client konfiguriert - TTL: {self.cache_ttl}s")
            
        except Exception as e:
            logger.warning(f"Redis-Verbindung fehlgeschlagen: {e} - Cache deaktiviert")
            self.redis_client = None
    
    def _get_cache_key(self, text_chunk: str) -> str:
        """
        Generiert einen Cache-Schlüssel für einen Text-Chunk.
        """
        # Erstelle deterministischen Hash aus Text + Modell + Prompt-Version
        content = f"{text_chunk}|extraction-primary|ner_extraction_v1_few_shot"
        return f"ner_cache_v2:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[ExtractedEntity]]:
        """
        Holt Ergebnis aus dem Redis Cache.
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                self.total_cache_hits += 1
                entities_data = json.loads(cached_data)
                return [ExtractedEntity(**entity) for entity in entities_data]
                
        except Exception as e:
            logger.warning(f"Cache-Abruf fehlgeschlagen: {e}")
        
        return None
    
    def _store_in_cache(self, cache_key: str, entities: List[ExtractedEntity]) -> None:
        """
        Speichert Ergebnis im Redis Cache.
        """
        if not self.redis_client:
            return
        
        try:
            # Konvertiere Entities zu serialisierbaren Dicts
            entities_data = [
                {
                    'text': entity.text,
                    'category': entity.category,
                    'confidence': entity.confidence,
                    'start_pos': entity.start_pos,
                    'end_pos': entity.end_pos
                }
                for entity in entities
            ]
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(entities_data, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.warning(f"Cache-Speicherung fehlgeschlagen: {e}")
    
    def _create_extraction_prompt(self, text_chunk: str) -> str:
        """Create structured entity extraction prompt"""
        return f"""Du bist ein Experte für die Extraktion von Entitäten aus Compliance- und Sicherheitsdokumenten.

Extrahiere alle relevanten Entitäten aus dem folgenden Text und klassifiziere sie in diese Kategorien:
- STANDARD: Standards und Frameworks (z.B. "ISO 27001", "NIST CSF", "BSI IT-Grundschutz")
- CONTROL_ID: Spezifische Kontroll-IDs (z.B. "A.5.1.1", "OPS-01", "SC-7")
- TECHNOLOGY: Technologien und Produkte (z.B. "Microsoft Azure", "Kubernetes", "LDAP")
- PROCESS: Geschäftsprozesse und Aktivitäten (z.B. "Risikobewertung", "Incident Management")
- ROLE: Rollen und Verantwortlichkeiten (z.B. "CISO", "Systemadministrator", "Data Controller")
- ORGANIZATION: Organisationen und Unternehmen (z.B. "BSI", "Microsoft", "NIST")

Antworte mit einem JSON-Objekt in folgendem Format:
{{
    "entities": [
        {{
            "text": "Gefundener Entitäten-Text",
            "category": "KATEGORIE",
            "confidence": 0.95
        }}
    ]
}}

Text für Entitäten-Extraktion:

{text_chunk}"""
    
    async def _call_litellm_api_async(self, prompt: str) -> str:
        """
        Führt einen API-Call an LiteLLM durch mit Retry-Mechanismus.
        """
        try:
            # === DYNAMIC MODEL RESOLUTION ===
            # Get model manager and resolve optimal model for extraction task
            model_manager = await get_model_manager()
            model_config = await model_manager.get_model_for_task(
                task_type=TaskType.EXTRACTION,
                model_tier=ModelTier.BALANCED,  # Extraction needs good quality balance
                fallback=True
            )
            
            # Create LLM request with dynamically resolved model
            request = LLMRequest(
                messages=[
                    LLMMessage(role="user", content=prompt)
                ],
                model=model_config["model"],  # DYNAMIC: Resolved from LiteLLM UI
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=4096,
                stream=False,
                # Request structured JSON response
                extra_kwargs={
                    "response_format": {"type": "json_object"}
                }
            )
            
            logger.info(f"Using dynamic model for extraction: {model_config['model']} (tier: {model_config['tier']}, strategy: {model_config['selection_strategy']})")
            
            # Execute with BATCH priority (quality validation background task)
            response = await self.litellm_client.complete(
                request=request,
                priority=RequestPriorityLevel.BATCH,  # Background processing priority
                purpose="entity_extraction_validation"  # For audit logging
            )
            
            self.total_api_calls += 1
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"LiteLLM API Call fehlgeschlagen: {e}")
            # Map LiteLLM exceptions for better error handling
            mapped_exception = LiteLLMExceptionMapper.map_exception(e)
            raise mapped_exception
    
    def _parse_llm_response(self, response_text: str) -> List[ExtractedEntity]:
        """
        Parst die JSON-Antwort von LiteLLM in ExtractedEntity Objekte.
        """
        try:
            # Entferne mögliche Markdown-Formatierung
            clean_response = response_text.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            response_data = json.loads(clean_response.strip())
            entities_data = response_data.get('entities', [])
            
            entities = []
            for entity_data in entities_data:
                entity = ExtractedEntity(
                    text=entity_data.get('text', ''),
                    category=entity_data.get('category', ''),
                    confidence=float(entity_data.get('confidence', 0.0))
                )
                entities.append(entity)
            
            return entities
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Fehler beim Parsen der LiteLLM-Antwort: {e}")
            logger.debug(f"Response Text: {response_text}")
            return []
    
    def _use_fallback_extractor(self, text_chunk: str) -> List[ExtractedEntity]:
        """
        Verwendet einen einfachen Pattern-basierten Extraktor als Fallback.
        """
        logger.warning("Using pattern-based fallback extractor")
        
        # Simple pattern-based extraction for basic entities
        entities = []
        text_lower = text_chunk.lower()
        
        # Standard patterns
        if any(term in text_lower for term in ["iso 27001", "iso/iec 27001", "isms"]):
            entities.append(ExtractedEntity("ISO 27001", "STANDARD", 0.8))
        
        if any(term in text_lower for term in ["bsi", "grundschutz", "it-grundschutz"]):
            entities.append(ExtractedEntity("BSI IT-Grundschutz", "STANDARD", 0.8))
        
        if any(term in text_lower for term in ["nist", "cybersecurity framework"]):
            entities.append(ExtractedEntity("NIST CSF", "STANDARD", 0.8))
        
        return entities
    
    def extract_entities(self, text_chunk: str, chunk_id: str = None) -> ExtractionResult:
        """
        Extrahiert Entitäten aus einem Text-Chunk.
        
        Args:
            text_chunk: Der zu verarbeitende Text
            chunk_id: Optionale ID für den Chunk
            
        Returns:
            ExtractionResult mit Entitäten und Metadaten
        """
        start_time = time.time()
        
        if not chunk_id:
            chunk_id = hashlib.md5(text_chunk.encode()).hexdigest()[:8]
        
        # 1. Cache-Lookup
        cache_key = self._get_cache_key(text_chunk)
        cached_entities = self._get_from_cache(cache_key)
        
        if cached_entities:
            processing_time = int((time.time() - start_time) * 1000)
            return ExtractionResult(
                entities=cached_entities,
                chunk_id=chunk_id,
                processing_time_ms=processing_time,
                source='cache'
            )
        
        # 2. LiteLLM-basierte Extraktion
        try:
            # Create structured extraction prompt
            extraction_prompt = self._create_extraction_prompt(text_chunk)
            
            # Run async extraction in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an event loop, use fallback
                entities = self._use_fallback_extractor(text_chunk)
                source = 'fallback'
            else:
                response_text = loop.run_until_complete(self._call_litellm_api_async(extraction_prompt))
                entities = self._parse_llm_response(response_text)
                source = 'api'
                
                # Cache das Ergebnis
                self._store_in_cache(cache_key, entities)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.total_processing_time += processing_time
            
            return ExtractionResult(
                entities=entities,
                chunk_id=chunk_id,
                processing_time_ms=processing_time,
                source=source,
                api_cost_estimate=self._estimate_api_cost(text_chunk)
            )
            
        except Exception as e:
            logger.error(f"LiteLLM-Extraktion für Chunk {chunk_id} fehlgeschlagen: {e}")
            
            # 3. Fallback-Mechanismus
            entities = self._use_fallback_extractor(text_chunk)
            processing_time = int((time.time() - start_time) * 1000)
            
            return ExtractionResult(
                entities=entities,
                chunk_id=chunk_id,
                processing_time_ms=processing_time,
                source='fallback'
            )
    
    def extract_entities_batch(self, text_chunks: List[str]) -> List[ExtractionResult]:
        """
        Extrahiert Entitäten aus mehreren Text-Chunks (Batch-Verarbeitung).
        
        Args:
            text_chunks: Liste von Text-Chunks
            
        Returns:
            Liste von ExtractionResult
        """
        results = []
        
        for i, chunk in enumerate(text_chunks):
            chunk_id = f"batch_{int(time.time())}_{i}"
            result = self.extract_entities(chunk, chunk_id)
            results.append(result)
        
        return results
    
    def _estimate_api_cost(self, text: str) -> float:
        """
        Schätzt die API-Kosten für einen Text.
        """
        # Grobe Schätzung: Gemini Pro ~$3.5/1M input tokens via LiteLLM
        # Durchschnittlich ~4 Zeichen pro Token
        estimated_tokens = len(text) / 4
        cost_per_token = 3.5 / 1_000_000
        return estimated_tokens * cost_per_token
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Gibt Performance-Statistiken zurück.
        """
        total_requests = self.total_api_calls + self.total_cache_hits
        cache_hit_rate = self.total_cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'total_api_calls': self.total_api_calls,
            'total_cache_hits': self.total_cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'average_processing_time_ms': self.total_processing_time / self.total_api_calls if self.total_api_calls > 0 else 0,
            'model': 'extraction-primary (LiteLLM)',
            'redis_available': self.redis_client is not None,
            'litellm_available': True
        }


# ===================================================================
# BACKWARD COMPATIBILITY WRAPPER 
# ===================================================================

class GeminiEntityExtractorLegacy:
    """Legacy wrapper for backward compatibility during migration"""
    
    def __init__(self):
        self.enhanced_extractor = GeminiEntityExtractor()
        logger.warning("Using legacy GeminiEntityExtractor wrapper - migrate to GeminiEntityExtractor")
    
    def extract_entities(self, text_chunk: str, chunk_id: str = None) -> ExtractionResult:
        """Legacy extraction method"""
        return self.enhanced_extractor.extract_entities(text_chunk, chunk_id)
    
    def extract_entities_batch(self, text_chunks: List[str]) -> List[ExtractionResult]:
        """Legacy batch extraction method"""
        return self.enhanced_extractor.extract_entities_batch(text_chunks)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Legacy performance stats method"""
        return self.enhanced_extractor.get_performance_stats()

# Legacy alias for existing code
LegacyGeminiEntityExtractor = GeminiEntityExtractorLegacy 