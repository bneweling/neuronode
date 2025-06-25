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
            # OpenAI Models - Optimierte Temperatur-Einstellungen (2025)
            "gpt-4.1": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4.1",
                temperature=0.2,  # Optimiert für Extraktion - etwas Flexibilität
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "gpt-4o": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4o",
                temperature=0.2,  # Optimiert für Validierung - konsistent aber analytisch
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "gpt-4o-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4o-mini", 
                temperature=0.2,  # Optimiert für Validierung und Extraktion
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "o4-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="o4-mini",
                temperature=0.2,  # Reasoning-optimiert für Validierung
                max_tokens=65536,
                model_kwargs={"top_p": 0.95}
            ),
            "o3-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="o3-mini",
                # o3 models may have specific parameter requirements
                max_tokens=32768
            ),
            "o1-mini": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="o1-mini",
                # o1 models don't support temperature/top_p
                max_tokens=65536
            ),
            "o1-preview": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="o1-preview",
                # o1 models don't support temperature/top_p
                max_tokens=32768
            ),
            # OpenAI Legacy (fallback)
            "gpt-4-turbo": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-4-turbo",
                temperature=0.3,  # Balanced für verschiedene Anwendungen
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            "gpt-3.5-turbo": ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-3.5-turbo",
                temperature=0.3,  # Balanced für verschiedene Anwendungen
                max_tokens=4096,
                model_kwargs={"top_p": 0.95}
            ),
            
            # Anthropic Models - Optimierte Temperatur-Einstellungen (2025)
            "claude-opus-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-opus-4-20250514",
                temperature=0.6,  # Optimiert für Synthese - kreativ aber kontrolliert
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-sonnet-4-20250514": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-sonnet-4-20250514",
                temperature=0.2,  # Optimiert für Validierung - analytisch
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-3-7-sonnet-20250219": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-7-sonnet-20250219",
                temperature=0.4,  # Balanced für Synthese
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-3-5-sonnet-20241022": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-5-sonnet-20241022",
                temperature=0.3,  # Balanced für verschiedene Anwendungen
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-3-5-haiku-20241022": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-5-haiku-20241022",
                temperature=0.2,  # Schnell und konsistent für Validierung
                max_tokens=8192,
                top_p=0.95
            ),
            "claude-3-opus-20240229": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.5,  # Kreativ für Synthese
                max_tokens=4096,
                top_p=0.95
            ),
            "claude-3-haiku-20240307": ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model="claude-3-haiku-20240307",
                temperature=0.2,  # Schnell und konsistent
                max_tokens=4096,
                top_p=0.95
            ),
            
            # Google Models - Optimierte Temperatur-Einstellungen (2025)
            "gemini-2.5-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-pro",
                temperature=0.5,  # Optimiert für Synthese - kreativ aber strukturiert
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-2.5-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-flash",
                temperature=0.1,  # Optimiert für Klassifikation - deterministisch
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-2.5-flash-lite-preview-06-17": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.5-flash-lite-preview-06-17",
                temperature=0.1,  # Optimiert für Klassifikation - effizient
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-2.0-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-2.0-flash",
                temperature=0.3,  # Balanced für Synthese
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-1.5-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-1.5-pro",
                temperature=0.4,  # Balanced für verschiedene Anwendungen
                max_output_tokens=8192,
                top_p=0.95
            ),
            "gemini-1.5-flash": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-1.5-flash",
                temperature=0.2,  # Balanced für Extraktion und Klassifikation
                max_output_tokens=8192,
                top_p=0.95
            ),
            # Legacy fallback
            "gemini-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-pro",
                temperature=0.3,  # Balanced für verschiedene Anwendungen
                max_output_tokens=2048,
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
                    print(f"Warning: Model {name} not found, using fallback")
                    # Fallback to available models
                    fallback = self._get_fallback_model(name)
                    if fallback and fallback in self.models:
                        models.append(self.models[fallback])
            return models if models else [self.models["gpt-4o"], self.models["claude-3-5-sonnet-20241022"]]
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
            # OpenAI fallbacks - Neueste zuerst
            "gpt-4.1": "gpt-4o",
            "o4-mini": "o1-mini",
            "o3-mini": "o1-mini",
            "gpt-4-turbo-preview": "gpt-4-turbo",
            
            # Anthropic fallbacks - Neueste zuerst
            "claude-opus-4-20250514": "claude-3-opus-20240229",
            "claude-sonnet-4-20250514": "claude-3-5-sonnet-20241022",
            "claude-3-7-sonnet-20250219": "claude-3-5-sonnet-20241022",
            
            # Google fallbacks - Neueste zuerst
            "gemini-2.5-flash-lite-preview-06-17": "gemini-2.5-flash",
            "gemini-2.5-flash": "gemini-1.5-flash",
            "gemini-2.5-pro": "gemini-1.5-pro",
            "gemini-2.0-flash": "gemini-1.5-flash"
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
        valid_profiles = ["premium", "balanced", "cost_effective", "gemini_only", "openai_only"]
        if profile not in valid_profiles:
            raise ValueError(f"Invalid profile. Must be one of: {valid_profiles}")
        
        # This would require updating the .env file or environment variable
        print(f"To switch to '{profile}' profile, set MODEL_PROFILE={profile} in your .env file and restart the application")
        return f"Profile switch to '{profile}' prepared. Restart required."

llm_router = LLMRouter()