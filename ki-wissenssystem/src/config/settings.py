from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict, Any
import os
from enum import Enum

class ModelProfile(Enum):
    PREMIUM = "premium"
    BALANCED = "balanced"
    COST_EFFECTIVE = "cost_effective"

class Settings(BaseSettings):
    # LLM API Keys
    openai_api_key: str
    anthropic_api_key: str
    google_api_key: str
    
    # Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    
    # Model Profile Selection
    model_profile: str = "premium"  # premium, balanced, cost_effective
    
    # Legacy Model Selection (deprecated - use model_profile instead)
    classifier_model: Optional[str] = None
    extractor_model: Optional[str] = None
    synthesizer_model: Optional[str] = None
    validator_model_1: Optional[str] = None
    validator_model_2: Optional[str] = None
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retries: int = 3
    
    # Pydantic v2 configuration
    model_config = ConfigDict(env_file=".env", protected_namespaces=('settings_',))
    
    def get_model_config(self) -> Dict[str, str]:
        """Get model configuration based on selected profile"""
        profiles = {
            ModelProfile.PREMIUM.value: {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gpt-4.1",
                "synthesizer_model": "claude-opus-4-20250514",
                "validator_model_1": "gpt-4o",
                "validator_model_2": "claude-sonnet-4-20250514"
            },
            ModelProfile.BALANCED.value: {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gpt-4.1",
                "synthesizer_model": "gemini-2.5-pro",
                "validator_model_1": "gpt-4o",
                "validator_model_2": "claude-3-7-sonnet-20250219"
            },
            ModelProfile.COST_EFFECTIVE.value: {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gpt-4o",
                "synthesizer_model": "gemini-2.5-flash",
                "validator_model_1": "gpt-4o",
                "validator_model_2": "claude-3-7-sonnet-20250219"
            }
        }
        
        # Use legacy individual settings if they exist, otherwise use profile
        if all([self.classifier_model, self.extractor_model, self.synthesizer_model, 
                self.validator_model_1, self.validator_model_2]):
            return {
                "classifier_model": self.classifier_model,
                "extractor_model": self.extractor_model,
                "synthesizer_model": self.synthesizer_model,
                "validator_model_1": self.validator_model_1,
                "validator_model_2": self.validator_model_2
            }
        
        return profiles.get(self.model_profile, profiles[ModelProfile.PREMIUM.value])

settings = Settings()