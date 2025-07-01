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
    # LLM API Keys (optional for testing)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
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
    
    # LiteLLM Proxy Configuration
    litellm_proxy_url: str = "http://localhost:4000"  # Default for development
    
    # Additional runtime environment variables  
    environment: Optional[str] = "development"
    api_host: Optional[str] = "0.0.0.0"
    api_port: Optional[int] = 8001
    jwt_secret_key: Optional[str] = "neuronode-jwt-secret-change-in-production"
    jwt_algorithm: Optional[str] = "HS256"
    jwt_access_token_expire_minutes: Optional[int] = 30
    redis_host: Optional[str] = "redis"
    redis_port: Optional[int] = 6379
    litellm_master_key: Optional[str] = "sk-ki-system-master-2025"
    log_level: Optional[str] = "INFO"
    enable_metrics: Optional[bool] = True
    enable_audit_logs: Optional[bool] = True
    debug: Optional[bool] = False
    reload: Optional[bool] = True

    # Pydantic v2 configuration
    model_config = ConfigDict(
        env_file=".env", 
        protected_namespaces=('settings_',),
        extra='ignore'  # Ignore extra fields instead of raising validation errors
    )
    
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
                "classifier_model": "gemini-1.5-flash-latest",
                "extractor_model": "gemini-1.5-flash-latest",
                "synthesizer_model": "gemini-1.5-pro-latest",
                "validator_model_1": "o4-mini",
                "validator_model_2": "claude-3-7-sonnet-20250219"
            },
            "cost_effective": {
                "classifier_model": "gemini-2.5-flash-lite-preview",
                "extractor_model": "gpt-4o-mini",
                "synthesizer_model": "gemini-2.0-flash",
                "validator_model_1": "gpt-4o-mini",
                "validator_model_2": "claude-3-5-haiku-20241022"
            },
            "gemini_only": {
                "classifier_model": "gemini-1.5-flash-latest",
                "extractor_model": "gemini-1.5-flash-latest",
                "synthesizer_model": "gemini-1.5-pro-latest",
                "validator_model_1": "gemini-1.5-pro",
                "validator_model_2": "gemini-1.5-flash"
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