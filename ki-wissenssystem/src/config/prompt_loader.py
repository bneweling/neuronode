"""
Zentraler PromptLoader für das KI-Wissenssystem.

Dieser Service lädt alle Prompts aus YAML-Dateien und stellt sie als
formatierbare Templates über eine einheitliche API zur Verfügung.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Singleton-Klasse für das zentrale Prompt-Management.
    
    Lädt beim Start alle Prompts aus den YAML-Dateien im prompts-Verzeichnis
    und stellt sie über get_prompt() zur Verfügung.
    """
    
    _instance: Optional['PromptLoader'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'PromptLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Vermeide mehrfache Initialisierung
        if self._initialized:
            return
            
        self.prompts: Dict[str, str] = {}
        self.prompts_dir = Path(__file__).parent / "prompts"
        self._load_all_prompts()
        self._initialized = True
        
        logger.info(f"PromptLoader initialisiert mit {len(self.prompts)} Prompts")
    
    def reload_prompts(self) -> None:
        """
        Lädt alle Prompts neu - nützlich nach Änderungen an YAML-Dateien.
        """
        self.prompts.clear()
        self._load_all_prompts()
        logger.info(f"Prompts neu geladen - {len(self.prompts)} Prompts verfügbar")
    
    def _load_all_prompts(self) -> None:
        """
        Lädt alle YAML-Dateien aus dem prompts-Verzeichnis.
        """
        if not self.prompts_dir.exists():
            logger.error(f"Prompts-Verzeichnis nicht gefunden: {self.prompts_dir}")
            return
        
        yaml_files = list(self.prompts_dir.glob("*.yaml"))
        
        if not yaml_files:
            logger.warning(f"Keine YAML-Dateien im Prompts-Verzeichnis gefunden: {self.prompts_dir}")
            return
        
        for yaml_file in yaml_files:
            try:
                self._load_yaml_file(yaml_file)
            except Exception as e:
                logger.error(f"Fehler beim Laden der YAML-Datei {yaml_file}: {e}")
    
    def _load_yaml_file(self, yaml_file: Path) -> None:
        """
        Lädt eine einzelne YAML-Datei und fügt die Prompts zum Dictionary hinzu.
        """
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file)
                
            if not isinstance(content, dict):
                logger.warning(f"YAML-Datei {yaml_file} enthält keine Dictionary-Struktur")
                return
            
            # Präfix basierend auf Dateiname hinzufügen (z.B. extractor_)
            file_prefix = yaml_file.stem
            
            for prompt_key, prompt_text in content.items():
                # Vollständiger Schlüssel: dateiname_promptname
                full_key = f"{file_prefix}_{prompt_key}"
                
                if not isinstance(prompt_text, str):
                    logger.warning(f"Prompt '{prompt_key}' in {yaml_file} ist kein String")
                    continue
                
                self.prompts[full_key] = prompt_text.strip()
                
                # Zusätzlich ohne Präfix speichern für Rückwärtskompatibilität
                self.prompts[prompt_key] = prompt_text.strip()
                
            logger.debug(f"Erfolgreich {len(content)} Prompts aus {yaml_file} geladen")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML-Parsing-Fehler in {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden von {yaml_file}: {e}")
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Ruft einen Prompt ab und formatiert ihn mit den übergebenen Parametern.
        
        Args:
            prompt_name: Name des Prompts (z.B. 'ner_extraction_v1_few_shot')
            **kwargs: Dynamische Parameter für das String-Formatting
            
        Returns:
            Formatierter Prompt-Text
            
        Raises:
            KeyError: Wenn der Prompt nicht gefunden wird
            ValueError: Wenn das Formatting fehlschlägt
        """
        if prompt_name not in self.prompts:
            available_prompts = sorted(self.prompts.keys())
            raise KeyError(
                f"Prompt '{prompt_name}' nicht gefunden. "
                f"Verfügbare Prompts: {available_prompts}"
            )
        
        prompt_template = self.prompts[prompt_name]
        
        try:
            # String-Formatting mit den übergebenen Parametern
            formatted_prompt = prompt_template.format(**kwargs)
            return formatted_prompt
            
        except KeyError as e:
            missing_key = str(e).strip("'\"")
            raise ValueError(
                f"Fehlender Parameter '{missing_key}' für Prompt '{prompt_name}'. "
                f"Benötigte Parameter: {self._extract_format_keys(prompt_template)}"
            )
        except Exception as e:
            raise ValueError(f"Formatting-Fehler für Prompt '{prompt_name}': {e}")
    
    def _extract_format_keys(self, template: str) -> list:
        """
        Extrahiert die Format-Schlüssel aus einem Template-String.
        
        Args:
            template: Template-String mit {key} Platzhaltern
            
        Returns:
            Liste der gefundenen Schlüssel (nur einfache Parameter, keine JSON-Blöcke)
        """
        import re
        # Regex für {key} Muster - nur einfache Bezeichner, keine Newlines oder Leerzeichen
        keys = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', template)
        return sorted(set(keys))
    
    def list_prompts(self) -> Dict[str, list]:
        """
        Gibt eine Übersicht über alle verfügbaren Prompts zurück.
        
        Returns:
            Dictionary mit Kategorien als Schlüssel und Prompt-Namen als Werte
        """
        categories = {}
        
        for prompt_name in self.prompts.keys():
            # Kategorie basierend auf Präfix bestimmen
            if '_' in prompt_name:
                category = prompt_name.split('_')[0]
            else:
                category = 'uncategorized'
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(prompt_name)
        
        # Sortieren für bessere Übersicht
        for category in categories:
            categories[category].sort()
        
        return categories
    
    def get_prompt_info(self, prompt_name: str) -> Dict[str, Any]:
        """
        Gibt detaillierte Informationen über einen Prompt zurück.
        
        Args:
            prompt_name: Name des Prompts
            
        Returns:
            Dictionary mit Prompt-Informationen
        """
        if prompt_name not in self.prompts:
            raise KeyError(f"Prompt '{prompt_name}' nicht gefunden")
        
        template = self.prompts[prompt_name]
        
        return {
            'name': prompt_name,
            'length': len(template),
            'required_parameters': self._extract_format_keys(template),
            'preview': template[:200] + '...' if len(template) > 200 else template
        }


# Singleton-Instanz für globalen Zugriff
prompt_loader = PromptLoader()


def get_prompt(prompt_name: str, **kwargs) -> str:
    """
    Convenience-Funktion für den direkten Zugriff auf Prompts.
    
    Args:
        prompt_name: Name des Prompts
        **kwargs: Parameter für das Formatting
        
    Returns:
        Formatierter Prompt
    """
    return prompt_loader.get_prompt(prompt_name, **kwargs) 