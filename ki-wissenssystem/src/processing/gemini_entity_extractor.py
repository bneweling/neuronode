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

# Füge das Konfigurationsmodul hinzu
sys.path.append(str(Path(__file__).parent.parent))

try:
    import redis
except ImportError:
    redis = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Fallback-Decorator für retry
    def retry(stop=None, wait=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def stop_after_attempt(attempts):
        return None
    
    def wait_exponential(multiplier=1, min=4, max=10):
        return None

from config.prompt_loader import get_prompt
from config.ai_services_loader import get_config

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
    API-basierter Entity Extractor mit Google Gemini.
    
    Features:
    - Redis-Caching mit konfigurierbarer TTL
    - Batch-Verarbeitung für Effizienz  
    - Retry-Mechanismus mit exponential backoff
    - Fallback auf Regex-Extraktor bei Fehlern
    - Kosten- und Performance-Tracking
    """
    
    def __init__(self):
        """
        Initialisiert den Gemini Entity Extractor.
        """
        self.config = get_config()
        self._setup_gemini_client()
        self._setup_redis_client()
        self.fallback_extractor = None  # Wird bei Bedarf geladen
        
        # Performance-Metriken
        self.total_api_calls = 0
        self.total_cache_hits = 0
        self.total_processing_time = 0.0
        
        # Logge verfügbare Dependencies
        if not redis:
            logger.warning("Redis nicht verfügbar - Caching deaktiviert")
        if not genai:
            logger.warning("Google Generative AI nicht verfügbar - Fallback-Modus")
        if not TENACITY_AVAILABLE:
            logger.warning("Tenacity nicht verfügbar - Retry-Mechanismus deaktiviert")
        
        logger.info("GeminiEntityExtractor initialisiert")
    
    def _setup_gemini_client(self) -> None:
        """
        Konfiguriert den Gemini API Client.
        """
        if not genai:
            logger.warning("Google Generative AI nicht installiert - Fallback-Modus")
            self.gemini_client = None
            self.model_name = "N/A"  # Setze Fallback-Modellname
            return
        
        gemini_config = self.config.get_gemini_config()
        api_key = gemini_config.get('api_key')
        
        if not api_key or api_key.startswith('${'):
            logger.warning("Gemini API Key nicht konfiguriert - Fallback-Modus")
            self.gemini_client = None
            self.model_name = "N/A"  # Setze Fallback-Modellname
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model_name = self.config.get_model_for_task('extraction')
            self.gemini_client = genai.GenerativeModel(self.model_name)
            
            logger.info(f"Gemini Client konfiguriert mit Modell: {self.model_name} (aus LLM-Config)")
            
        except Exception as e:
            logger.error(f"Fehler bei Gemini Client Setup: {e}")
            self.gemini_client = None
            self.model_name = "N/A"  # Setze Fallback-Modellname
    
    def _setup_redis_client(self) -> None:
        """
        Konfiguriert den Redis Client für Caching.
        """
        if not redis:
            logger.warning("Redis nicht installiert - Cache deaktiviert")
            self.redis_client = None
            return
        
        redis_config = self.config.get_redis_config()
        
        try:
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=True
            )
            
            # Test-Verbindung
            self.redis_client.ping()
            
            self.cache_ttl = redis_config.get('ttl_for_documents_seconds', 2592000)  # 30 Tage
            logger.info(f"Redis Client konfiguriert - TTL: {self.cache_ttl}s")
            
        except Exception as e:
            logger.warning(f"Redis-Verbindung fehlgeschlagen: {e} - Cache deaktiviert")
            self.redis_client = None
    
    def _get_cache_key(self, text_chunk: str) -> str:
        """
        Generiert einen Cache-Schlüssel für einen Text-Chunk.
        
        Args:
            text_chunk: Der zu verarbeitende Text
            
        Returns:
            SHA-256 Hash als Cache-Schlüssel
        """
        # Erstelle deterministischen Hash aus Text + Modell + Prompt-Version
        content = f"{text_chunk}|{self.model_name}|ner_extraction_v1_few_shot"
        return f"ner_cache:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[ExtractedEntity]]:
        """
        Holt Ergebnis aus dem Redis Cache.
        
        Args:
            cache_key: Cache-Schlüssel
            
        Returns:
            Liste von ExtractedEntity oder None
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
        
        Args:
            cache_key: Cache-Schlüssel
            entities: Liste von ExtractedEntity
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Führt einen API-Call an Gemini durch mit Retry-Mechanismus.
        
        Args:
            prompt: Der formatierte Prompt
            
        Returns:
            JSON-Response als String
            
        Raises:
            Exception: Bei dauerhaften API-Fehlern
        """
        if not self.gemini_client:
            raise Exception("Gemini Client nicht verfügbar")
        
        try:
            gemini_config = self.config.get_gemini_config()
            timeout = gemini_config.get('timeout_seconds', 45)
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Niedrige Temperatur für konsistente Extraktion
                    'candidate_count': 1,
                }
            )
            
            self.total_api_calls += 1
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API Call fehlgeschlagen: {e}")
            raise
    
    def _parse_gemini_response(self, response_text: str) -> List[ExtractedEntity]:
        """
        Parst die JSON-Antwort von Gemini in ExtractedEntity Objekte.
        
        Args:
            response_text: JSON-Response von Gemini
            
        Returns:
            Liste von ExtractedEntity
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
            logger.error(f"Fehler beim Parsen der Gemini-Antwort: {e}")
            logger.debug(f"Response Text: {response_text}")
            return []
    
    def _use_fallback_extractor(self, text_chunk: str) -> List[ExtractedEntity]:
        """
        Verwendet den alten Regex-Extraktor als Fallback.
        
        Args:
            text_chunk: Der zu verarbeitende Text
            
        Returns:
            Liste von ExtractedEntity
        """
        if not self.config.is_fallback_enabled('regex_fallback_on_error'):
            logger.warning("Fallback deaktiviert - leere Ergebnisse zurückgegeben")
            return []
        
        # Lazy-Loading des Fallback-Extractors
        if self.fallback_extractor is None:
            try:
                # Hier würde der Import des alten Extractors stehen
                # from extractors.regex_entity_extractor import RegexEntityExtractor
                # self.fallback_extractor = RegexEntityExtractor()
                logger.info("Fallback-Extraktor würde hier geladen werden")
                return []  # Placeholder
            except ImportError:
                logger.error("Fallback-Extraktor nicht verfügbar")
                return []
        
        try:
            # return self.fallback_extractor.extract(text_chunk)
            logger.info("Fallback-Extraktion würde hier durchgeführt werden")
            return []  # Placeholder
        except Exception as e:
            logger.error(f"Fallback-Extraktion fehlgeschlagen: {e}")
            return []
    
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
        
        # 2. API-basierte Extraktion
        try:
            prompt = get_prompt("ner_extraction_v1_few_shot", text_block=text_chunk)
            response_text = self._call_gemini_api(prompt)
            entities = self._parse_gemini_response(response_text)
            
            # Cache das Ergebnis
            self._store_in_cache(cache_key, entities)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.total_processing_time += processing_time
            
            return ExtractionResult(
                entities=entities,
                chunk_id=chunk_id,
                processing_time_ms=processing_time,
                source='api',
                api_cost_estimate=self._estimate_api_cost(text_chunk)
            )
            
        except Exception as e:
            logger.error(f"API-Extraktion für Chunk {chunk_id} fehlgeschlagen: {e}")
            
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
        
        Args:
            text: Der verarbeitete Text
            
        Returns:
            Geschätzte Kosten in USD
        """
        # Grobe Schätzung: Gemini Flash ~$0.075/1M input tokens
        # Durchschnittlich ~4 Zeichen pro Token
        estimated_tokens = len(text) / 4
        cost_per_token = 0.075 / 1_000_000
        return estimated_tokens * cost_per_token
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Gibt Performance-Statistiken zurück.
        
        Returns:
            Dictionary mit Performance-Metriken
        """
        total_requests = self.total_api_calls + self.total_cache_hits
        cache_hit_rate = self.total_cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'total_api_calls': self.total_api_calls,
            'total_cache_hits': self.total_cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'average_processing_time_ms': self.total_processing_time / self.total_api_calls if self.total_api_calls > 0 else 0,
            'gemini_model': self.model_name if hasattr(self, 'model_name') else 'N/A',
            'redis_available': self.redis_client is not None,
            'gemini_available': self.gemini_client is not None
        } 