from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.settings import settings
from enum import Enum
from typing import Dict, Any

class ModelPurpose(Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"

class LLMRouter:
    def __init__(self):
        self.models = {
            # OpenAI Models - Latest
            "gpt-4.1": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4.1",
                temperature=0.1
            ),
            "gpt-4o": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4o",
                temperature=0.1
            ),
            "o4-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="o4-mini",
                temperature=0.1
            ),
            # OpenAI Models - Legacy (for fallback)
            "gpt-4-turbo-preview": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4-turbo-preview",
                temperature=0.1
            ),
            "gpt-3.5-turbo": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-3.5-turbo",
                temperature=0.1
            ),
            
            # Anthropic Models - Latest
            "claude-opus-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-opus-4-20250514",
                temperature=0.1
            ),
            "claude-sonnet-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-sonnet-4-20250514",
                temperature=0.1
            ),
            "claude-3-7-sonnet-20250219": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-7-sonnet-20250219",
                temperature=0.1
            ),
            # Anthropic Models - Legacy (for fallback)
            "claude-3-opus-20240229": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.1
            ),
            "claude-3-haiku-20240307": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-haiku-20240307",
                temperature=0.1
            ),
            
            # Google Models - Latest
            "gemini-2.5-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-pro",
                temperature=0.1
            ),
            "gemini-2.5-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-flash",
                temperature=0.1
            ),
            "gemini-1.5-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-1.5-flash",
                temperature=0.1
            ),
            # Google Models - Legacy (for fallback)
            "gemini-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-pro",
                temperature=0.1
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
                    print(f"Warning: Model {name} not found, using fallback")
                    # Fallback to legacy models
                    fallback = self._get_fallback_model(name)
                    if fallback and fallback in self.models:
                        models.append(self.models[fallback])
            return models if models else [self.models["gpt-4o"], self.models["claude-3-opus-20240229"]]
        else:
            # For single model purposes
            if model_name in self.models:
                return self.models[model_name]
            else:
                print(f"Warning: Model {model_name} not found, using fallback")
                fallback = self._get_fallback_model(model_name)
                return self.models.get(fallback, self.models["gpt-4o"])
    
    def _get_fallback_model(self, model_name: str) -> str:
        """Get fallback model for unavailable models"""
        fallback_mapping = {
            # OpenAI fallbacks
            "gpt-4.1": "gpt-4o",
            "o4-mini": "gpt-4o",
            
            # Anthropic fallbacks
            "claude-opus-4-20250514": "claude-3-opus-20240229",
            "claude-sonnet-4-20250514": "claude-3-opus-20240229",
            "claude-3-7-sonnet-20250219": "claude-3-opus-20240229",
            
            # Google fallbacks
            "gemini-2.5-pro": "gemini-pro",
            "gemini-2.5-flash": "gemini-pro",
            "gemini-1.5-flash": "gemini-pro"
        }
        return fallback_mapping.get(model_name, "gpt-4o")
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of all available models"""
        return {name: model.__class__.__name__ for name, model in self.models.items()}
    
    def get_current_profile(self) -> str:
        """Get current model profile"""
        return settings.model_profile
    
    def switch_profile(self, profile: str):
        """Switch model profile (requires restart to take effect)"""
        valid_profiles = ["premium", "balanced", "cost_effective"]
        if profile not in valid_profiles:
            raise ValueError(f"Invalid profile. Must be one of: {valid_profiles}")
        
        # This would require updating the .env file or environment variable
        print(f"To switch to '{profile}' profile, set MODEL_PROFILE={profile} in your .env file and restart the application")
        return f"Profile switch to '{profile}' prepared. Restart required."

llm_router = LLMRouter()