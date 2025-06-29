# ===============================================================================
# LEGACY LLM CONFIG - BACKUP FÜR MIGRATION
# Diese Datei dient als Fallback während der LiteLLM-Migration
# ACHTUNG: Nach erfolgreicher Migration löschen!
# ===============================================================================

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.settings import settings
from enum import Enum
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ModelPurpose(Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"

class LegacyLLMRouter:
    """Legacy LLM Router - FALLBACK during migration"""
    
    def __init__(self):
        logger.warning("Using LEGACY LLM Router - Switch to LiteLLM ASAP!")
        self.models = {
            # OpenAI Models - Optimierte Temperatur-Einstellungen (2025)
            "gpt-4.1": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4.1",
                temperature=0.2,
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "gpt-4o": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4o",
                temperature=0.2,
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "gpt-4o-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4o-mini", 
                temperature=0.2,
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            
            # Anthropic Models
            "claude-opus-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-opus-4-20250514",
                temperature=0.6,
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-sonnet-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-sonnet-4-20250514",
                temperature=0.2,
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-3-5-sonnet-20241022": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-5-sonnet-20241022",
                temperature=0.3,
                max_tokens=8192,
                top_p=0.95
            ),
            
            # Google Models
            "gemini-2.5-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-flash",
                temperature=0.1,
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-1.5-flash-latest": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-1.5-flash-latest",
                temperature=0.1,
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-1.5-pro-latest": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-1.5-pro-latest",
                temperature=0.4,
                max_output_tokens=8192,
                top_p=0.95
            )
        }
        
        # Get current model configuration from settings
        model_config = settings.get_model_config()
        
        self.purpose_models = {
            ModelPurpose.CLASSIFICATION: model_config["classifier_model"],
            ModelPurpose.EXTRACTION: model_config["extractor_model"],
            ModelPurpose.SYNTHESIS: model_config["synthesizer_model"],
            ModelPurpose.VALIDATION: [model_config["validator_model_1"], model_config["validator_model_2"]]
        }
    
    def get_model(self, purpose: ModelPurpose):
        """Get model(s) for specific purpose with fallback handling"""
        model_name = self.purpose_models.get(purpose)
        
        if isinstance(model_name, list):
            # For validation, return list of models
            models = []
            for name in model_name:
                if name in self.models:
                    models.append(self.models[name])
                else:
                    logger.warning(f"Model {name} not found, using fallback")
                    fallback = self._get_fallback_model(name)
                    if fallback and fallback in self.models:
                        models.append(self.models[fallback])
            return models if models else [self.models["gpt-4o"], self.models["claude-3-5-sonnet-20241022"]]
        else:
            # For single model purposes
            if model_name in self.models:
                return self.models[model_name]
            else:
                logger.warning(f"Model {model_name} not found, using fallback")
                fallback = self._get_fallback_model(model_name)
                return self.models.get(fallback, self.models["gpt-4o"])
    
    def _get_fallback_model(self, model_name: str) -> str:
        """Get fallback model for unavailable models"""
        fallback_mapping = {
            "gpt-4.1": "gpt-4o",
            "claude-opus-4-20250514": "claude-3-5-sonnet-20241022",
            "claude-sonnet-4-20250514": "claude-3-5-sonnet-20241022",
            "gemini-2.5-flash": "gemini-1.5-flash-latest",
            "gemini-2.5-pro": "gemini-1.5-pro-latest",
        }
        return fallback_mapping.get(model_name, "gpt-4o")
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of all available models"""
        return {name: model.__class__.__name__ for name, model in self.models.items()}

# Legacy router instance
legacy_llm_router = LegacyLLMRouter() 