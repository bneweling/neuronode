"""
Robuster LLM-Response Parser mit Pydantic
Wandelt LLM-Outputs in strukturierte Daten um
"""
import json
import re
from typing import TypeVar, Type, Optional, Dict, Any
from pydantic import BaseModel, ValidationError
import logging

T = TypeVar('T', bound=BaseModel)

class LLMParser:
    """Parser für LLM-Antworten mit Pydantic-Validierung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_llm_response(
        self, 
        response_text: str, 
        response_model: Type[T],
        fallback_values: Optional[Dict[str, Any]] = None
    ) -> T:
        """
        Parst LLM-Response zu Pydantic-Modell
        
        Args:
            response_text: Rohe LLM-Antwort
            response_model: Pydantic-Modell-Klasse
            fallback_values: Fallback-Werte bei Parse-Fehlern
            
        Returns:
            Validiertes Pydantic-Modell
        """
        
        # 1. Versuche direktes JSON-Parsing
        try:
            json_data = self._extract_json_from_text(response_text)
            if json_data:
                return response_model(**json_data)
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.warning(f"JSON-Parsing fehlgeschlagen: {e}")
        
        # 2. Versuche strukturiertes Text-Parsing
        try:
            parsed_data = self._parse_structured_text(response_text)
            if parsed_data:
                return response_model(**parsed_data)
        except ValidationError as e:
            self.logger.warning(f"Strukturiertes Parsing fehlgeschlagen: {e}")
        
        # 3. Fallback-Werte verwenden
        if fallback_values:
            try:
                return response_model(**fallback_values)
            except ValidationError as e:
                self.logger.error(f"Fallback-Werte ungültig: {e}")
        
        # 4. Letzter Fallback: Minimum-gültige Instanz
        return self._create_minimal_instance(response_model)
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrahiert JSON aus Fließtext"""
        # Suche nach JSON-Blöcken in ```json oder { } Blöcken
        json_patterns = [
            r'```json\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'\{.*?\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _parse_structured_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parst strukturierten Text (KEY: Value Format)"""
        result = {}
        
        # Pattern für KEY: Value Zeilen
        patterns = {
            'relationship_type': r'RELATIONSHIP_TYPE:\s*(\w+)',
            'confidence': r'CONFIDENCE:\s*([\d.]+)',
            'context': r'CONTEXT:\s*(.+?)(?=\n\w+:|$)',
            'evidence': r'EVIDENCE:\s*(.+?)(?=\n\w+:|$)',
            'reasoning': r'REASONING:\s*(.+?)(?=\n\w+:|$)',
            'needs_clarification': r'NEEDS_CLARIFICATION:\s*(true|false)',
            'prompt': r'PROMPT:\s*["\'](.+?)["\']',
            'ambiguous_terms': r'AMBIGUOUS_TERMS:\s*\[(.*?)\]'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                
                # Typ-Konvertierung
                if key == 'confidence':
                    try:
                        result[key] = float(value)
                    except ValueError:
                        continue
                elif key == 'needs_clarification':
                    result[key] = value.lower() == 'true'
                elif key == 'ambiguous_terms':
                    # Parse Array-ähnliche Strings
                    terms = [term.strip().strip('"\'') for term in value.split(',')]
                    result[key] = [term for term in terms if term]
                else:
                    result[key] = value
        
        return result if result else None
    
    def _create_minimal_instance(self, model_class: Type[T]) -> T:
        """Erstellt minimal-gültige Instanz als letzter Fallback"""
        # Basis-Fallback-Werte für verschiedene Modelle
        fallbacks = {
            'RelationshipAnalysis': {
                'relationship_type': 'NONE',
                'confidence': 0.0,
                'confidence_level': 'LOW',
                'context': 'Unbekannt',
                'evidence': 'Nicht verfügbar',
                'reasoning': 'Parsing fehlgeschlagen'
            },
            'AmbiguityCheck': {
                'needs_clarification': False,
                'confidence': 0.0,
                'reasoning': 'Parsing fehlgeschlagen'
            }
        }
        
        model_name = model_class.__name__
        default_values = fallbacks.get(model_name, {})
        
        try:
            return model_class(**default_values)
        except ValidationError:
            # Wenn sogar Fallback fehlschlägt, alle Felder auf None/Default setzen
            model_fields = model_class.__fields__
            safe_defaults = {}
            
            for field_name, field_info in model_fields.items():
                if field_info.default is not None:
                    safe_defaults[field_name] = field_info.default
                elif field_info.type_ == str:
                    safe_defaults[field_name] = ""
                elif field_info.type_ == float:
                    safe_defaults[field_name] = 0.0
                elif field_info.type_ == bool:
                    safe_defaults[field_name] = False
                elif field_info.type_ == list:
                    safe_defaults[field_name] = []
            
            return model_class(**safe_defaults) 