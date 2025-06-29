"""
LiteLLM Client - Central LLM Integration Hub

Ersetzt alle direkten LLM-Provider-Aufrufe (OpenAI, Anthropic, Gemini) durch 
standardisierte OpenAI-kompatible Calls an den LiteLLM Proxy.

MIGRATION STRATEGY:
- Behält alle bisherigen Model-Namen bei (Kompatibilität)
- Nutzt Purpose-based Aliases für optimale Performance
- Fallback auf direkten LiteLLM client für unknown models
"""

import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
import logging
from dataclasses import dataclass
import asyncio
import json

from src.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None

class LiteLLMClient:
    """Central LLM client using LiteLLM proxy"""
    
    def __init__(self):
        """Initialize LiteLLM client pointing to proxy"""
        self.client = OpenAI(
            api_key="sk-irrelevant",  # Key wird vom Proxy verwaltet
            base_url=settings.litellm_proxy_url
        )
        
        # Model mapping: Legacy names -> LiteLLM aliases
        self.model_mapping = {
            # Purpose-based aliases (PREFERRED)
            "classification": "classification-primary",
            "extraction": "extraction-primary", 
            "synthesis": "synthesis-premium",
            "validation": "validation-primary",
            
            # Legacy compatibility (DEPRECATED but supported)
            "gemini-2.5-flash": "classification-primary",
            "gpt-4.1": "extraction-primary",
            "claude-opus-4-20250514": "synthesis-premium",
            "gpt-4o": "validation-primary",
            "claude-sonnet-4-20250514": "validation-secondary",
            
            # All other model names pass through directly
        }
        
        logger.info(f"LiteLLM Client initialized - Proxy URL: {settings.litellm_proxy_url}")
    
    def _map_model_name(self, model_name: str) -> str:
        """Map legacy model names to LiteLLM aliases"""
        return self.model_mapping.get(model_name, model_name)
    
    def _prepare_messages(self, messages: Union[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """Convert various input formats to OpenAI messages format"""
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            return messages
        else:
            raise ValueError(f"Unsupported message format: {type(messages)}")
    
    def invoke(self, 
               model: str, 
               messages: Union[str, List[Dict[str, str]]], 
               **kwargs) -> LLMResponse:
        """
        Synchronous LLM call (LangChain .invoke() replacement)
        
        Args:
            model: Model name (will be mapped to LiteLLM alias)
            messages: User input or messages list
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with standardized format
        """
        try:
            mapped_model = self._map_model_name(model)
            prepared_messages = self._prepare_messages(messages)
            
            # Filter kwargs to only include supported parameters
            supported_params = {
                'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 
                'presence_penalty', 'stop', 'stream', 'response_format'
            }
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
            
            response = self.client.chat.completions.create(
                model=mapped_model,
                messages=prepared_messages,
                **filtered_kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=mapped_model,
                usage=response.usage.dict() if response.usage else None,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "original_model_name": model
                }
            )
            
        except Exception as e:
            logger.error(f"LiteLLM invoke error - Model: {model}, Error: {e}")
            raise
    
    async def ainvoke(self, 
                      model: str, 
                      messages: Union[str, List[Dict[str, str]]], 
                      **kwargs) -> LLMResponse:
        """
        Asynchronous LLM call (LangChain .ainvoke() replacement)
        
        Args:
            model: Model name (will be mapped to LiteLLM alias)
            messages: User input or messages list
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with standardized format
        """
        # Run synchronous call in thread pool for async compatibility
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.invoke(model, messages, **kwargs)
        )
    
    def stream(self, 
               model: str, 
               messages: Union[str, List[Dict[str, str]]], 
               **kwargs) -> AsyncGenerator[str, None]:
        """
        Streaming LLM call for real-time responses
        
        Args:
            model: Model name
            messages: User input or messages list
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        try:
            mapped_model = self._map_model_name(model)
            prepared_messages = self._prepare_messages(messages)
            
            # Force streaming
            kwargs['stream'] = True
            
            # Filter supported parameters
            supported_params = {
                'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 
                'presence_penalty', 'stop', 'stream'
            }
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
            
            response = self.client.chat.completions.create(
                model=mapped_model,
                messages=prepared_messages,
                **filtered_kwargs
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"LiteLLM streaming error - Model: {model}, Error: {e}")
            raise
    
    def embed_query(self, text: str, model: str = "embedding-001") -> List[float]:
        """
        Generate embeddings for text
        
        Args:
            text: Text to embed
            model: Embedding model name
            
        Returns:
            Embedding vector
        """
        try:
            # Use OpenAI embeddings endpoint via LiteLLM
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"LiteLLM embedding error - Model: {model}, Error: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from LiteLLM proxy"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.warning(f"Could not fetch models from LiteLLM proxy: {e}")
            return list(self.model_mapping.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Check LiteLLM proxy health"""
        try:
            # Try a simple model list call to test connectivity
            models = self.client.models.list()
            return {
                "status": "healthy",
                "proxy_url": settings.litellm_proxy_url,
                "available_models": len(models.data) if models.data else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "proxy_url": settings.litellm_proxy_url,
                "error": str(e)
            }

# Global client instance (Singleton pattern)
litellm_client = LiteLLMClient()

# ===============================================================================
# LANGCHAIN COMPATIBILITY LAYER
# ===============================================================================

class LiteLLMLangChainAdapter:
    """
    Adapter to make LiteLLM client compatible with existing LangChain code
    
    This allows gradual migration without breaking existing functionality.
    """
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = litellm_client
    
    def invoke(self, input_data):
        """LangChain .invoke() compatibility"""
        if hasattr(input_data, 'content'):
            # Handle HumanMessage/AIMessage objects
            messages = [{"role": "user", "content": input_data.content}]
        elif isinstance(input_data, str):
            messages = input_data
        elif isinstance(input_data, list):
            # Handle formatted messages from ChatPromptTemplate
            if len(input_data) > 0 and hasattr(input_data[0], 'content'):
                messages = [{"role": msg.type, "content": msg.content} for msg in input_data]
            else:
                messages = input_data
        else:
            messages = str(input_data)
        
        response = self.client.invoke(self.model_name, messages)
        
        # Return object with .content attribute for LangChain compatibility
        class LangChainResponse:
            def __init__(self, content):
                self.content = content
        
        return LangChainResponse(response.content)
    
    async def ainvoke(self, input_data):
        """LangChain .ainvoke() compatibility"""
        if hasattr(input_data, 'content'):
            messages = [{"role": "user", "content": input_data.content}]
        elif isinstance(input_data, str):
            messages = input_data
        elif isinstance(input_data, list):
            if len(input_data) > 0 and hasattr(input_data[0], 'content'):
                messages = [{"role": msg.type, "content": msg.content} for msg in input_data]
            else:
                messages = input_data
        else:
            messages = str(input_data)
        
        response = await self.client.ainvoke(self.model_name, messages)
        
        class LangChainResponse:
            def __init__(self, content):
                self.content = content
        
        return LangChainResponse(response.content)

def create_langchain_adapter(model_name: str) -> LiteLLMLangChainAdapter:
    """Factory function for creating LangChain-compatible adapters"""
    return LiteLLMLangChainAdapter(model_name) 