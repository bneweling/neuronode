"""
Enhanced Model Manager für dynamische Modell-Konfiguration
Ermöglicht UI-gesteuerte Modell-Zuordnung ohne Neustart

Unterstützt:
- 5 Task-Types (CLASSIFICATION, EXTRACTION, SYNTHESIS, VALIDATION_PRIMARY, VALIDATION_SECONDARY)
- 5 Model-Profile (PREMIUM, BALANCED, COST_EFFECTIVE, SPECIALIZED, ULTRA_FAST)
- Smart Alias Strategy: Direct Task-to-Model Mapping via LiteLLM UI
- Real-time Model-Switching ohne Service-Neustart
- Enterprise Budget & Performance Tracking
"""

import httpx
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from ..config.settings import Settings, ModelProfile

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Verfügbare Task-Types im System"""
    CLASSIFICATION = "CLASSIFICATION"
    EXTRACTION = "EXTRACTION" 
    SYNTHESIS = "SYNTHESIS"
    VALIDATION_PRIMARY = "VALIDATION_PRIMARY"
    VALIDATION_SECONDARY = "VALIDATION_SECONDARY"

class ModelTier(Enum):
    """Enterprise Model-Tiers für Budget-Management - Smart Alias Strategy"""
    PREMIUM = "PREMIUM"           # Höchste Kosten, beste Performance
    BALANCED = "BALANCED"         # Ausgewogenes Preis-Leistungs-Verhältnis  
    COST_EFFECTIVE = "COST_EFFECTIVE"  # Niedrigste Kosten
    SPECIALIZED = "SPECIALIZED"   # Spezialisierte Modelle für spezielle Tasks
    ULTRA_FAST = "ULTRA_FAST"     # Ultraschnelle Modelle für Echtzeit-Anwendungen

class EnhancedModelManager:
    """
    Enterprise-Grade Model Manager mit LiteLLM Integration
    
    Features:
    - Dynamische Modell-Auflösung über LiteLLM UI
    - Team-basierte Modell-Zuordnung
    - Performance & Cost Tracking
    - Real-time Configuration Updates
    - Fallback-Strategien für Ausfälle
    """
    
    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.litellm_proxy_url = self.settings.litellm_proxy_url
        self.api_client = httpx.AsyncClient(timeout=30.0)
        
        # Caching für Performance
        self._config_cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 60  # 60 Sekunden Cache
        
        # Performance Tracking - Enterprise Edition
        self._model_performance = {}
        self._model_costs = {}
        self._request_metrics = {}
        self._error_tracking = {}
        self._response_time_history = []
        self._cost_tracking_enabled = True
        
        logger.info(f"EnhancedModelManager initialized with proxy URL: {self.litellm_proxy_url}")

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.api_client.aclose()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Prüft ob Cache-Eintrag noch gültig ist"""
        if cache_key not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[cache_key]

    async def _fetch_live_config(self) -> Dict[str, Any]:
        """
        Holt die aktuelle Modell-Konfiguration vom LiteLLM Proxy
        
        Returns:
            Dict mit allen konfigurierten Modellen und deren Parametern
        """
        cache_key = "live_config"
        
        # Cache Check
        if self._is_cache_valid(cache_key):
            logger.debug("Using cached LiteLLM configuration")
            return self._config_cache[cache_key]
        
        try:
            # LiteLLM Proxy Model Info Endpoint
            response = await self.api_client.get(
                f"{self.litellm_proxy_url}/model/info",
                headers={"Authorization": f"Bearer sk-ki-system-master-2025"}
            )
            response.raise_for_status()
            
            config_data = response.json()
            models_data = config_data.get("data", [])
            
            # Cache Update
            self._config_cache[cache_key] = models_data
            self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self._cache_ttl)
            
            logger.info(f"Successfully fetched {len(models_data)} models from LiteLLM proxy")
            return models_data
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch live config from LiteLLM: {e}")
            # Fallback auf statische Konfiguration
            return self._get_fallback_config()
        except Exception as e:
            logger.error(f"Unexpected error fetching live config: {e}")
            return self._get_fallback_config()

    def _get_fallback_config(self) -> List[Dict[str, Any]]:
        """
        Fallback-Konfiguration wenn LiteLLM Proxy nicht erreichbar ist
        Nutzt die statischen Profile aus settings.py
        """
        logger.warning("Using fallback configuration - LiteLLM proxy not accessible")
        
        profile_config = self.settings.get_model_config()
        
        # Konvertiere statische Konfiguration in LiteLLM Format
        fallback_models = []
        for task_type, model_name in profile_config.items():
            fallback_models.append({
                "model_name": f"{task_type.replace('_model', '')}-primary",
                "litellm_params": {"model": model_name},
                "model_info": {
                    "id": f"fallback-{task_type}",
                    "tier": "fallback",
                    "task_type": task_type.replace('_model', '')
                }
            })
        
        return fallback_models

    async def get_model_for_task(
        self, 
        task_type: TaskType, 
        team_id: str = None,
        model_tier: ModelTier = ModelTier.BALANCED,
        fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Löst den optimalen Modell-Alias für eine gegebene Aufgabe auf
        
        SMART ALIAS STRATEGY:
        - Format: {task_type}_{profile} (e.g., synthesis_premium, extraction_balanced)
        - Direct mapping in LiteLLM UI: Admin can change assignments directly
        - No intermediate alias layers - maximum UI usability
        
        Args:
            task_type: Art der Aufgabe (classification, extraction, etc.)
            team_id: Optional - Team-ID für team-spezifische Modelle
            model_tier: Gewünschtes Model-Tier (premium, balanced, cost_effective, specialized, ultra_fast)
            fallback: Ob Fallback-Modelle verwendet werden sollen
            
        Returns:
            Dict mit Modell-Konfiguration für LiteLLM
        """
        
        try:
            # 1. Lade aktuelle LiteLLM Konfiguration
            live_config = await self._fetch_live_config()
            
            # 2. SMART ALIAS STRATEGY: Bestimme Modell-Alias mit Task + Profile Format
            preferred_alias = f"{task_type.value}_{model_tier.value}"
            
            # 3. Suche nach passendem Modell in Live-Config mit Smart Alias Prioritäten
            model_candidates = []
            
            for model in live_config:
                model_name = model.get("model_name", "")
                
                # PRIORITÄT 1: Exakte Übereinstimmung mit gewünschtem Alias
                if model_name == preferred_alias:
                    model_candidates.append({
                        **model,
                        "priority": 1,  # Höchste Priorität
                        "tier": model_tier.value,
                        "match_type": "exact_smart_alias"
                    })
                
                # PRIORITÄT 2: Gleicher Task-Type, anderes Profil
                elif model_name.startswith(f"{task_type.value}_"):
                    # Extract profile from model name (e.g., "synthesis_premium" -> "premium")
                    parts = model_name.split("_", 1)
                    if len(parts) == 2:
                        model_profile = parts[1]
                        tier_score = self._calculate_profile_compatibility(model_profile, model_tier.value)
                        
                        model_candidates.append({
                            **model,
                            "priority": 2,
                            "tier": model_profile,
                            "tier_score": tier_score,
                            "match_type": "same_task_different_profile"
                        })
                
                # PRIORITÄT 3: Legacy-Format Support (task-primary/secondary)
                elif model_name in [f"{task_type.value}-primary", f"{task_type.value}-secondary"]:
                    model_candidates.append({
                        **model,
                        "priority": 3,
                        "tier": "legacy",
                        "tier_score": 5,  # Medium compatibility
                        "match_type": "legacy_format"
                    })
            
            # 4. Sortiere Kandidaten: Priorität > Tier-Kompatibilität
            model_candidates.sort(key=lambda x: (
                x["priority"],
                x.get("tier_score", 10)  # Lower is better
            ))
            
            # 5. Wähle bestes Modell
            if model_candidates:
                selected_model = model_candidates[0]
                
                # Performance Tracking
                await self._track_model_selection(task_type, selected_model)
                
                logger.info(f"Smart Alias resolved: {task_type.value} + {model_tier.value} → {selected_model['model_name']} (match: {selected_model['match_type']})")
                
                return {
                    "model": selected_model["litellm_params"]["model"],
                    "model_alias": selected_model["model_name"],
                    "tier": selected_model["tier"],
                    "task_type": task_type.value,
                    "team_id": team_id,
                    "selected_at": datetime.now().isoformat(),
                    "selection_strategy": "smart_alias_live_config",
                    "match_type": selected_model["match_type"]
                }
            
            # 6. Fallback auf statische Konfiguration
            if fallback:
                logger.warning(f"No Smart Alias model found for {task_type.value}_{model_tier.value}, using fallback")
                return await self._get_fallback_model(task_type, model_tier)
            
            else:
                raise ValueError(f"No model configured for task type: {task_type.value} with tier: {model_tier.value}")
                
        except Exception as e:
            logger.error(f"Error resolving Smart Alias model for {task_type.value}_{model_tier.value}: {e}")
            
            if fallback:
                return await self._get_fallback_model(task_type, model_tier)
            else:
                raise

    def _calculate_profile_compatibility(self, available_profile: str, requested_profile: str) -> int:
        """
        Berechnet Kompatibilitäts-Score zwischen verfügbarem und gewünschtem Profil
        Lower score = better compatibility
        
        Smart Alias Profile Hierarchie:
        - premium: Beste Performance, höchste Kosten
        - balanced: Ausgewogen, mittlere Kosten  
        - cost_effective: Niedrigste Kosten
        - specialized: Spezielle Anwendungsfälle
        - ultra_fast: Ultraschnell für Real-time
        """
        
        # Profile compatibility matrix
        compatibility_matrix = {
            "premium": {"premium": 0, "balanced": 1, "specialized": 2, "ultra_fast": 3, "cost_effective": 4},
            "balanced": {"balanced": 0, "premium": 1, "specialized": 2, "cost_effective": 2, "ultra_fast": 3},
            "cost_effective": {"cost_effective": 0, "balanced": 1, "ultra_fast": 2, "specialized": 3, "premium": 4},
            "specialized": {"specialized": 0, "premium": 1, "balanced": 2, "ultra_fast": 3, "cost_effective": 4},
            "ultra_fast": {"ultra_fast": 0, "cost_effective": 1, "balanced": 2, "specialized": 3, "premium": 4}
        }
        
        return compatibility_matrix.get(requested_profile, {}).get(available_profile, 10)

    async def _get_fallback_model(self, task_type: TaskType, model_tier: ModelTier) -> Dict[str, Any]:
        """Fallback-Modell aus statischer Konfiguration"""
        
        profile_config = self.settings.get_model_config()
        
        # Map TaskType zu settings key
        task_mapping = {
            TaskType.CLASSIFICATION: "classifier_model",
            TaskType.EXTRACTION: "extractor_model", 
            TaskType.SYNTHESIS: "synthesizer_model",
            TaskType.VALIDATION_PRIMARY: "validator_model_1",
            TaskType.VALIDATION_SECONDARY: "validator_model_2"
        }
        
        settings_key = task_mapping.get(task_type)
        if not settings_key:
            raise ValueError(f"No fallback mapping for task type: {task_type.value}")
        
        fallback_model = profile_config.get(settings_key)
        if not fallback_model:
            raise ValueError(f"No fallback model configured for {settings_key}")
        
        return {
            "model": fallback_model,
            "model_alias": f"{task_type.value}-fallback",
            "tier": model_tier.value,
            "task_type": task_type.value,
            "selected_at": datetime.now().isoformat(),
            "selection_strategy": "fallback"
        }

    async def _track_model_selection(self, task_type: TaskType, model_config: Dict[str, Any]):
        """Tracking für Performance & Cost Analysis"""
        
        model_name = model_config.get("model_name", "unknown")
        
        # Performance Tracking
        if model_name not in self._model_performance:
            self._model_performance[model_name] = {
                "selections": 0,
                "task_types": set(),
                "first_used": datetime.now(),
                "last_used": datetime.now()
            }
        
        self._model_performance[model_name]["selections"] += 1
        self._model_performance[model_name]["task_types"].add(task_type.value)
        self._model_performance[model_name]["last_used"] = datetime.now()
        
        logger.debug(f"Tracked model selection: {model_name} for {task_type.value}")

    async def get_model_performance_stats(self) -> Dict[str, Any]:
        """Gibt Performance-Statistiken für alle Modelle zurück"""
        
        stats = {}
        for model_name, data in self._model_performance.items():
            stats[model_name] = {
                **data,
                "task_types": list(data["task_types"]),  # Convert set to list for JSON
                "first_used": data["first_used"].isoformat(),
                "last_used": data["last_used"].isoformat()
            }
        
        return stats

    async def refresh_config_cache(self):
        """Forciert Neuladung der Konfiguration von LiteLLM"""
        
        logger.info("Refreshing model configuration cache")
        
        # Clear cache
        self._config_cache.clear()
        self._cache_expiry.clear()
        
        # Reload configuration
        await self._fetch_live_config()
        
        logger.info("Model configuration cache refreshed successfully")

# Singleton Instance für globale Nutzung
_enhanced_model_manager = None

async def get_model_manager() -> EnhancedModelManager:
    """Factory Function für EnhancedModelManager Singleton"""
    global _enhanced_model_manager
    
    if _enhanced_model_manager is None:
        _enhanced_model_manager = EnhancedModelManager()
    
    return _enhanced_model_manager 