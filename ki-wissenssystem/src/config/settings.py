from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Dict, Any
import os
from enum import Enum

class ModelProfile(Enum):
    PREMIUM = "premium"
    BALANCED = "balanced"
    COST_EFFECTIVE = "cost_effective"
    GEMINI_ONLY = "gemini_only"
    OPENAI_ONLY = "openai_only"

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
    model_profile: str = "premium"  # premium, balanced, cost_effective, gemini_only, openai_only
    
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
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration based on current profile"""
        profile_configs = {
            "premium": {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gpt-4.1", 
                "synthesizer_model": "claude-opus-4-20250514",
                "validator_model_1": "gpt-4o",
                "validator_model_2": "claude-sonnet-4-20250514"
            },
            "balanced": {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gpt-4.1",
                "synthesizer_model": "gemini-2.5-pro",
                "validator_model_1": "o4-mini",
                "validator_model_2": "claude-3-7-sonnet-20250219"
            },
            "cost_effective": {
                "classifier_model": "gemini-2.5-flash-lite-preview-06-17",
                "extractor_model": "gpt-4o-mini",
                "synthesizer_model": "gemini-2.0-flash",
                "validator_model_1": "gpt-4o-mini",
                "validator_model_2": "claude-3-5-haiku-20241022"
            },
            "gemini_only": {
                "classifier_model": "gemini-2.5-flash",
                "extractor_model": "gemini-2.5-pro",
                "synthesizer_model": "gemini-2.5-pro",
                "validator_model_1": "gemini-2.0-flash",
                "validator_model_2": "gemini-2.5-flash"
            },
            "openai_only": {
                "classifier_model": "gpt-4o-mini",
                "extractor_model": "gpt-4.1",
                "synthesizer_model": "gpt-4o",
                "validator_model_1": "o4-mini",
                "validator_model_2": "o3-mini"
            }
        }
        
        current_profile = self.model_profile.lower()
        
        # Return configuration for current profile, fallback to premium
        return profile_configs.get(current_profile, profile_configs["premium"])

settings = Settings()