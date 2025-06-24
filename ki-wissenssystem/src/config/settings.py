from pydantic_settings import BaseSettings
from typing import Optional
import os

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
    
    # LLM Model Selection
    classifier_model: str = "gemini-pro"
    extractor_model: str = "gpt-4-turbo-preview"
    synthesizer_model: str = "claude-3-opus-20240229"
    validator_model_1: str = "gpt-4-turbo-preview"
    validator_model_2: str = "claude-3-opus-20240229"
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retries: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()