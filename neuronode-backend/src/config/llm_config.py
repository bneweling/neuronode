# ===============================================================================
# SIMPLIFIED LLM CONFIG FOR LITELLM MIGRATION
# Simplified version during migration to avoid LangChain dependencies
# ===============================================================================

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
    """Simplified LLM Router for migration phase"""
    
    def __init__(self):
        # Simplified model configuration without LangChain dependencies
        self.model_configs = {
            # OpenAI Models
            "gpt-4.1": {"provider": "openai", "model": "gpt-4.1", "temperature": 0.2},
            "gpt-4o": {"provider": "openai", "model": "gpt-4o", "temperature": 0.2},
            "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2},
            "o4-mini": {"provider": "openai", "model": "o4-mini", "temperature": 0.2},
            "o3-mini": {"provider": "openai", "model": "o3-mini", "temperature": 0.2},
            "o1-mini": {"provider": "openai", "model": "o1-mini"},
            "o1-preview": {"provider": "openai", "model": "o1-preview"},
            "gpt-4-turbo": {"provider": "openai", "model": "gpt-4-turbo", "temperature": 0.3},
            "gpt-3.5-turbo": {"provider": "openai", "model": "gpt-3.5-turbo", "temperature": 0.3},
            
            # Anthropic Models
            "claude-opus-4-20250514": {"provider": "anthropic", "model": "claude-opus-4-20250514", "temperature": 0.6},
            "claude-sonnet-4-20250514": {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "temperature": 0.2},
            "claude-3-7-sonnet-20250219": {"provider": "anthropic", "model": "claude-3-7-sonnet-20250219", "temperature": 0.4},
            "claude-3-5-sonnet-20241022": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "temperature": 0.3},
            "claude-3-5-haiku-20241022": {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "temperature": 0.2},
            "claude-3-opus-20240229": {"provider": "anthropic", "model": "claude-3-opus-20240229", "temperature": 0.5},
            "claude-3-haiku-20240307": {"provider": "anthropic", "model": "claude-3-haiku-20240307", "temperature": 0.2},
            
            # Google Models
            "gemini-2.5-pro": {"provider": "google", "model": "gemini-2.5-pro", "temperature": 0.5},
            "gemini-2.5-flash": {"provider": "google", "model": "gemini-2.5-flash", "temperature": 0.1},
            "gemini-2.5-flash-lite-preview": {"provider": "google", "model": "gemini-2.5-flash-lite-preview-06-17", "temperature": 0.0},
            "gemini-2.5-flash-lite-preview-06-17": {"provider": "google", "model": "gemini-2.5-flash-lite-preview-06-17", "temperature": 0.1},
            "gemini-2.0-flash": {"provider": "google", "model": "gemini-1.5-flash", "temperature": 0.3},
            "gemini-1.5-pro": {"provider": "google", "model": "gemini-1.5-pro", "temperature": 0.4},
            "gemini-1.5-flash": {"provider": "google", "model": "gemini-1.5-flash", "temperature": 0.2},
            "gemini-1.5-flash-latest": {"provider": "google", "model": "gemini-1.5-flash-latest", "temperature": 0.1},
            "gemini-1.5-pro-latest": {"provider": "google", "model": "gemini-1.5-pro-latest", "temperature": 0.4},
            "gemini-pro": {"provider": "google", "model": "gemini-2.5-flash", "temperature": 0.3}
        }
        
        # Get current model configuration from settings
        try:
            model_config = settings.get_model_config()
            self.purpose_models = {
                ModelPurpose.CLASSIFICATION: model_config.get("classifier_model", "gemini-2.5-flash"),
                ModelPurpose.EXTRACTION: model_config.get("extractor_model", "gemini-1.5-flash"),
                ModelPurpose.SYNTHESIS: model_config.get("synthesizer_model", "claude-3-5-sonnet-20241022"),
                ModelPurpose.VALIDATION: [
                    model_config.get("validator_model_1", "gpt-4o"),
                    model_config.get("validator_model_2", "claude-3-5-sonnet-20241022")
                ]
            }
        except Exception as e:
            logger.warning(f"Failed to load model config from settings: {e}")
            # Fallback configuration
            self.purpose_models = {
                ModelPurpose.CLASSIFICATION: "gemini-2.5-flash",
                ModelPurpose.EXTRACTION: "gemini-1.5-flash",
                ModelPurpose.SYNTHESIS: "claude-3-5-sonnet-20241022",
                ModelPurpose.VALIDATION: ["gpt-4o", "claude-3-5-sonnet-20241022"]
            }
    
    def get_model(self, purpose: ModelPurpose):
        """Get model configuration for specific purpose"""
        model_name = self.purpose_models.get(purpose)
        
        if isinstance(model_name, list):
            # For validation, return list of model configs
            configs = []
            for name in model_name:
                if name in self.model_configs:
                    configs.append(self.model_configs[name])
                else:
                    logger.warning(f"Model {name} not found, using fallback")
                    fallback = self._get_fallback_model(name)
                    if fallback and fallback in self.model_configs:
                        configs.append(self.model_configs[fallback])
            return configs if configs else [self.model_configs["gpt-4o"], self.model_configs["claude-3-5-sonnet-20241022"]]
        else:
            # For single model purposes
            if model_name in self.model_configs:
                return self.model_configs[model_name]
            else:
                logger.warning(f"Model {model_name} not found, using fallback")
                fallback = self._get_fallback_model(model_name)
                return self.model_configs.get(fallback, self.model_configs["gpt-4o"])
    
    def _get_fallback_model(self, model_name: str) -> str:
        """Get fallback model for unavailable models"""
        fallback_mapping = {
            # OpenAI fallbacks
            "gpt-4.1": "gpt-4o",
            "o4-mini": "o1-mini",
            "o3-mini": "o1-mini",
            "gpt-4-turbo-preview": "gpt-4-turbo",
            
            # Anthropic fallbacks
            "claude-opus-4-20250514": "claude-3-opus-20240229",
            "claude-sonnet-4-20250514": "claude-3-5-sonnet-20241022",
            "claude-3-7-sonnet-20250219": "claude-3-5-sonnet-20241022",
            
            # Google fallbacks
            "gemini-2.5-flash-lite-preview-06-17": "gemini-2.5-flash",
            "gemini-2.5-flash": "gemini-1.5-flash",
            "gemini-2.5-pro": "gemini-1.5-pro",
            "gemini-2.0-flash": "gemini-1.5-flash",
            "gemini-pro": "gemini-1.5-flash"
        }
        return fallback_mapping.get(model_name, "gpt-4o")
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of all available models"""
        return {name: config["provider"] for name, config in self.model_configs.items()}
    
    def get_current_profile(self) -> str:
        """Get current model profile"""
        return getattr(settings, 'model_profile', 'balanced')
    
    def switch_profile(self, profile: str):
        """Switch model profile (requires restart to take effect)"""
        valid_profiles = ["premium", "balanced", "cost_effective", "gemini_only", "openai_only"]
        if profile not in valid_profiles:
            raise ValueError(f"Invalid profile. Must be one of: {valid_profiles}")
        
        logger.info(f"To switch to '{profile}' profile, set MODEL_PROFILE={profile} in your .env file and restart the application")
        return f"Profile switch to '{profile}' prepared. Restart required."

# Initialize the router
llm_router = LiteLLMRouter()