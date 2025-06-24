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
            "gemini-pro": ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model="gemini-pro",
                temperature=0.1
            )
        }
        
        self.purpose_models = {
            ModelPurpose.CLASSIFICATION: settings.classifier_model,
            ModelPurpose.EXTRACTION: settings.extractor_model,
            ModelPurpose.SYNTHESIS: settings.synthesizer_model,
            ModelPurpose.VALIDATION: [settings.validator_model_1, settings.validator_model_2]
        }
    
    def get_model(self, purpose: ModelPurpose):
        model_name = self.purpose_models.get(purpose)
        if isinstance(model_name, list):
            return [self.models[name] for name in model_name]
        return self.models[model_name]

llm_router = LLMRouter()