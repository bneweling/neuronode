# ===============================================================================
# LITELLM-POWERED LLM CONFIG - MIGRATED VERSION
# Migration von LangChain zu LiteLLM Proxy für alle LLM-Aufrufe
# ===============================================================================

from src.llm.client import litellm_client, create_langchain_adapter
from src.config.settings import settings
from enum import Enum
from typing import Dict, Any, Union, List
import logging

logger = logging.getLogger(__name__)

class ModelPurpose(Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"

class LiteLLMRouter:
    """
    LiteLLM-powered LLM Router
    
    Ersetzt alle direkten LangChain Provider Calls durch standardisierte 
    OpenAI-kompatible Aufrufe an den LiteLLM Proxy.
    
    ADVANTAGES:
    - Vereinfachte Architektur (ein Client statt 3+ Provider)
    - Automatische Fallbacks und Retry-Logik
    - Standardisierte Error-Behandlung
    - Built-in Cost Tracking und Rate Limiting
    """
    
    def __init__(self):
        self.client = litellm_client
        logger.info("LiteLLM Router initialisiert - Alle LLM-Calls via Proxy")
        
        # Model mapping von Settings -> LiteLLM Aliases
        model_config = settings.get_model_config()
        
        self.purpose_models = {
            ModelPurpose.CLASSIFICATION: model_config["classifier_model"],
            ModelPurpose.EXTRACTION: model_config["extractor_model"],
            ModelPurpose.SYNTHESIS: model_config["synthesizer_model"],
            ModelPurpose.VALIDATION: [model_config["validator_model_1"], model_config["validator_model_2"]]
        }
        
        # Erstelle LangChain-kompatible Adapter für alle unterstützten Modelle
        self.langchain_adapters = {}
        all_models = [
            # Current purpose models
            model_config["classifier_model"],
            model_config["extractor_model"], 
            model_config["synthesizer_model"],
            model_config["validator_model_1"],
            model_config["validator_model_2"],
            # Common legacy model names for compatibility
            "gpt-4.1", "gpt-4o", "gpt-4o-mini", "o4-mini", "o3-mini", "o1-mini",
            "claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022",
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest",
            # Purpose-based aliases (PREFERRED)
            "classification", "extraction", "synthesis", "validation"
        ]
        
        for model_name in set(all_models):  # Remove duplicates
            if model_name:  # Skip None values
                self.langchain_adapters[model_name] = create_langchain_adapter(model_name)
    
    def get_model(self, purpose: ModelPurpose):
        """
        Get model(s) for specific purpose with LangChain compatibility
        
        Returns LangChain-compatible adapter that internally uses LiteLLM
        """
        model_name = self.purpose_models.get(purpose)
        
        if isinstance(model_name, list):
            # For validation, return list of LangChain-compatible adapters
            adapters = []
            for name in model_name:
                if name in self.langchain_adapters:
                    adapters.append(self.langchain_adapters[name])
                else:
                    # Create adapter on-the-fly
                    adapter = create_langchain_adapter(name)
                    self.langchain_adapters[name] = adapter
                    adapters.append(adapter)
            
            return adapters if adapters else [
                self.langchain_adapters.get("validation", create_langchain_adapter("validation")),
                self.langchain_adapters.get("validation-secondary", create_langchain_adapter("validation-secondary"))
            ]
        else:
            # For single model purposes
            if model_name in self.langchain_adapters:
                return self.langchain_adapters[model_name]
            else:
                # Create adapter on-the-fly
                adapter = create_langchain_adapter(model_name)
                self.langchain_adapters[model_name] = adapter
                return adapter
    
    def get_direct_client(self, model_name: str = None):
        """
        Get direct LiteLLM client for non-LangChain usage
        
        Args:
            model_name: Optional specific model name
            
        Returns:
            LiteLLM client instance
        """
        return self.client
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from LiteLLM proxy"""
        try:
            return self.client.get_available_models()
        except Exception as e:
            logger.warning(f"Could not fetch models from LiteLLM proxy: {e}")
            # Return configured models as fallback
            return list(self.langchain_adapters.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Check LiteLLM proxy health"""
        return self.client.health_check()
    
    def get_current_profile(self) -> str:
        """Get current model profile - Simplified for LiteLLM"""
        return "litellm-unified"
    
    def switch_profile(self, profile: str):
        """Switch model profile - No-op for LiteLLM (handled by proxy config)"""
        logger.info(f"Profile switching handled by LiteLLM proxy config: {profile}")
        pass

# ===============================================================================
# MIGRATION UTILITIES
# ===============================================================================

def migrate_from_legacy_router(legacy_router):
    """
    Utility to migrate from legacy LangChain-based router to LiteLLM router
    
    This preserves the same API surface while switching to LiteLLM internally.
    """
    logger.info("Migrating from Legacy LLM Router to LiteLLM Router...")
    
    # Create new LiteLLM router
    new_router = LiteLLMRouter()
    
    # Verify that all model purposes can be served
    for purpose in ModelPurpose:
        try:
            model = new_router.get_model(purpose)
            logger.info(f"✅ Purpose {purpose.value} mapped successfully")
        except Exception as e:
            logger.error(f"❌ Purpose {purpose.value} mapping failed: {e}")
            raise
    
    logger.info("✅ Migration to LiteLLM Router completed successfully")
    return new_router

# Global router instance
llm_router = LiteLLMRouter()

# ===============================================================================
# BACKWARD COMPATIBILITY
# ===============================================================================

# Legacy alias for existing code that imports llm_router
LLMRouter = LiteLLMRouter  # Alias for backward compatibility 