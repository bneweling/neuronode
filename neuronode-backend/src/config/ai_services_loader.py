"""
AI Services Configuration Loader

Lädt und verwaltet die Konfiguration für alle KI-Services aus ai_services.yaml.
Unterstützt Umgebungsvariablen-Substitution für sichere Konfiguration.
Integriert mit der zentralen LLM-Konfiguration für Modellauswahl.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AIServicesConfig:
    """
    Singleton-Klasse für die zentrale AI-Services-Konfiguration.
    
    Lädt die Konfiguration aus ai_services.yaml und ersetzt
    Umgebungsvariablen-Platzhalter wie ${GEMINI_API_KEY}.
    """
    
    _instance: Optional['AIServicesConfig'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'AIServicesConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config: Dict[str, Any] = {}
        self.config_file = Path(__file__).parent / "ai_services.yaml"
        self._load_config()
        self._load_llm_router()
        self._initialized = True
        
        logger.info("AIServicesConfig initialisiert")
    
    def _load_config(self) -> None:
        """
        Lädt die YAML-Konfiguration und ersetzt Umgebungsvariablen.
        """
        if not self.config_file.exists():
            logger.error(f"AI Services Konfigurationsdatei nicht gefunden: {self.config_file}")
            self.config = {}
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)
            
            # Umgebungsvariablen rekursiv ersetzen
            self.config = self._substitute_env_vars(raw_config)
            
            logger.info(f"AI Services Konfiguration erfolgreich geladen: {self.config_file}")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML-Parsing-Fehler in {self.config_file}: {e}")
            self.config = {}
        except Exception as e:
            logger.error(f"Fehler beim Laden der AI Services Konfiguration: {e}")
            self.config = {}
    
    def _load_llm_router(self) -> None:
        """
        Lädt den LLM Router für zentrale Modellauswahl.
        """
        try:
            from config.llm_config import LLMRouter, ModelPurpose
            self.llm_router = LLMRouter()
            self.ModelPurpose = ModelPurpose
            logger.info("LLM Router für zentrale Modellauswahl geladen")
        except ImportError as e:
            logger.warning(f"LLM Router nicht verfügbar: {e}")
            self.llm_router = None
            self.ModelPurpose = None
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Ersetzt rekursiv ${VAR_NAME} Platzhalter durch Umgebungsvariablen.
        
        Args:
            obj: Das zu verarbeitende Objekt (dict, list, str, etc.)
            
        Returns:
            Objekt mit ersetzten Umgebungsvariablen
        """
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_single_env_var(obj)
        else:
            return obj
    
    def _substitute_single_env_var(self, value: str) -> str:
        """
        Ersetzt ${VAR_NAME} in einem einzelnen String.
        
        Args:
            value: String mit potenziellen Umgebungsvariablen
            
        Returns:
            String mit ersetzten Umgebungsvariablen
        """
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            
            if env_value is None:
                logger.warning(f"Umgebungsvariable '{var_name}' nicht gesetzt - verwende Platzhalter")
                return match.group(0)  # Behalte ${VAR_NAME} bei
            
            return env_value
        
        # Regex für ${VAR_NAME} Pattern
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
    
    def get_gemini_config(self) -> Dict[str, Any]:
        """
        Gibt die Gemini API Konfiguration zurück.
        
        Returns:
            Dictionary mit Gemini-spezifischen Einstellungen
        """
        return self.config.get('gemini', {})
    
    def get_redis_config(self) -> Dict[str, Any]:
        """
        Gibt die Redis Konfiguration zurück.
        
        Returns:
            Dictionary mit Redis-spezifischen Einstellungen
        """
        return self.config.get('redis', {})
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """
        Gibt die Fallback-Mechanismen Konfiguration zurück.
        
        Returns:
            Dictionary mit Fallback-Einstellungen
        """
        return self.config.get('fallbacks', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """
        Gibt die Validierungs-Konfiguration zurück.
        
        Returns:
            Dictionary mit Validierungs-Einstellungen
        """
        return self.config.get('validation', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Gibt die Monitoring-Konfiguration zurück.
        
        Returns:
            Dictionary mit Monitoring-Einstellungen
        """
        return self.config.get('monitoring', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """
        Gibt die Development-Konfiguration zurück.
        
        Returns:
            Dictionary mit Development-Einstellungen
        """
        return self.config.get('development', {})
    
    def is_fallback_enabled(self, fallback_type: str) -> bool:
        """
        Prüft, ob ein bestimmter Fallback-Mechanismus aktiviert ist.
        
        Args:
            fallback_type: Name des Fallback-Mechanismus (z.B. 'regex_fallback_on_error')
            
        Returns:
            True wenn der Fallback aktiviert ist
        """
        fallbacks = self.get_fallback_config()
        return fallbacks.get(f'enable_{fallback_type}', False)
    
    def get_model_for_task(self, task_type: str) -> str:
        """
        Gibt das passende Modell für einen Aufgabentyp zurück (aus zentraler LLM-Config).
        
        Args:
            task_type: 'extraction', 'synthesis', 'classification', oder 'validation'
            
        Returns:
            Modell-Name für die Aufgabe aus der LLM-Konfiguration
        """
        if not self.llm_router or not self.ModelPurpose:
            logger.warning("LLM Router nicht verfügbar - verwende Fallback-Modelle")
            fallback_models = {
                'extraction': 'gemini-1.5-flash-latest',
                'synthesis': 'gemini-1.5-pro-latest',
                'classification': 'gemini-1.5-flash-latest',
                'validation': 'gemini-1.5-pro-latest'
            }
            return fallback_models.get(task_type, 'gemini-1.5-flash-latest')
        
        try:
            if task_type == 'extraction':
                purpose = self.ModelPurpose.EXTRACTION
            elif task_type == 'synthesis':
                purpose = self.ModelPurpose.SYNTHESIS
            elif task_type == 'classification':
                purpose = self.ModelPurpose.CLASSIFICATION
            elif task_type == 'validation':
                purpose = self.ModelPurpose.VALIDATION
            else:
                logger.warning(f"Unbekannter Task-Type: {task_type} - verwende EXTRACTION")
                purpose = self.ModelPurpose.EXTRACTION
            
            model = self.llm_router.get_model(purpose)
            if hasattr(model, 'model_name'):
                return model.model_name
            elif hasattr(model, 'model'):
                return model.model
            else:
                logger.warning(f"Modell-Name konnte nicht extrahiert werden für {task_type}")
                return 'gemini-1.5-flash-latest'
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Modells für {task_type}: {e}")
            return 'gemini-1.5-flash-latest'
    
    def get_gemini_model_for_task(self, task_type: str) -> str:
        """
        Deprecated: Verwende get_model_for_task() stattdessen.
        Compatibility-Wrapper für bestehenden Code.
        """
        logger.warning("get_gemini_model_for_task() ist deprecated - verwende get_model_for_task()")
        return self.get_model_for_task(task_type)
    
    def reload_config(self) -> None:
        """
        Lädt die Konfiguration neu - nützlich für Development.
        """
        self._load_config()
        self._load_llm_router()
        logger.info("AI Services Konfiguration und LLM Router neu geladen")


# Singleton-Instanz für globalen Zugriff
ai_services_config = AIServicesConfig()


def get_config() -> AIServicesConfig:
    """
    Convenience-Funktion für den direkten Zugriff auf die Konfiguration.
    
    Returns:
        AIServicesConfig Singleton-Instanz
    """
    return ai_services_config 