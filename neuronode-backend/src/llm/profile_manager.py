#!/usr/bin/env python3
"""
LiteLLM Profile Manager
Implementiert Profile-basierte Model-Routing über model_group_alias
"""

import os
import yaml
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProfileMetadata:
    """Profile-Metadaten für UI und API"""
    name: str
    cost_level: str
    performance_level: str
    description: str
    model_mappings: Dict[str, str]

class ProfileManager:
    """
    LiteLLM Profile Manager
    
    Verwaltet Profile-basierte Model-Routing über model_group_alias
    Basiert auf LiteLLM Dokumentation v1.61.20-stable
    """
    
    def __init__(self, config_path: str = "litellm_config.yaml"):
        self.config_path = Path(config_path)
        self.backup_path = Path(f"{config_path}.backup")
        
        # Profile-Definitionen (aus LiteLLM Config)
        self.profiles = {
            "premium": {
                "classification": "classification_premium",
                "extraction": "extraction_premium",
                "synthesis": "synthesis_premium",
                "validation_primary": "validation_primary_premium",
                "validation_secondary": "validation_secondary_premium"
            },
            "balanced": {
                "classification": "classification_balanced",
                "extraction": "extraction_balanced",
                "synthesis": "synthesis_balanced",
                "validation_primary": "validation_primary_balanced",
                "validation_secondary": "validation_secondary_balanced"
            },
            "cost_effective": {
                "classification": "classification_cost_effective",
                "extraction": "extraction_cost_effective",
                "synthesis": "synthesis_cost_effective",
                "validation_primary": "validation_primary_cost_effective",
                "validation_secondary": "validation_secondary_cost_effective"
            },
            "specialized": {
                "classification": "classification_specialized",
                "extraction": "extraction_specialized",
                "synthesis": "synthesis_specialized",
                "validation_primary": "validation_primary_specialized",
                "validation_secondary": "validation_secondary_specialized"
            },
            "ultra_fast": {
                "classification": "classification_ultra_fast",
                "extraction": "extraction_ultra_fast",
                "synthesis": "synthesis_ultra_fast",
                "validation_primary": "validation_primary_ultra_fast",
                "validation_secondary": "validation_secondary_ultra_fast"
            }
        }
        
        logger.info(f"ProfileManager initialized with config: {self.config_path}")
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt die aktuelle LiteLLM Konfiguration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Config loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Speichert die LiteLLM Konfiguration"""
        try:
            # Backup erstellen
            if self.config_path.exists():
                import shutil
                shutil.copy(self.config_path, self.backup_path)
                logger.debug(f"Backup created: {self.backup_path}")
            
            # Neue Konfiguration speichern
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            raise
    
    async def switch_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Wechselt Profil durch Aktualisierung der model_group_alias
        
        Args:
            profile_name: Name des Ziel-Profils (premium, balanced, etc.)
            
        Returns:
            Dict mit Status und aktualisierten Mappings
        """
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(self.profiles.keys())}")
        
        try:
            # 1. Lade aktuelle Konfiguration
            config = self.load_config()
            
            # 2. Backup aktuelle Konfiguration
            current_profile = config.get('profile_settings', {}).get('current_profile', 'unknown')
            
            # 3. Update model_group_alias für neues Profil
            config.setdefault('router_settings', {})
            config['router_settings']['model_group_alias'] = self.profiles[profile_name].copy()
            
            # 4. Update profile_settings
            config.setdefault('profile_settings', {})
            config['profile_settings']['current_profile'] = profile_name
            
            # 5. Add zu Switch-History
            switch_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "from_profile": current_profile,
                "to_profile": profile_name,
                "mappings_updated": len(self.profiles[profile_name])
            }
            
            if 'profile_switch_history' not in config['profile_settings']:
                config['profile_settings']['profile_switch_history'] = []
            
            config['profile_settings']['profile_switch_history'].append(switch_entry)
            
            # Behalte nur letzte 10 Einträge
            config['profile_settings']['profile_switch_history'] = \
                config['profile_settings']['profile_switch_history'][-10:]
            
            # 6. Speichere Konfiguration
            self.save_config(config)
            
            # 7. Hot-Reload LiteLLM Router (falls möglich)
            await self.reload_router()
            
            logger.info(f"Profile switched: {current_profile} → {profile_name}")
            
            return {
                "success": True,
                "from_profile": current_profile,
                "to_profile": profile_name,
                "active_mappings": self.profiles[profile_name],
                "switch_timestamp": switch_entry["timestamp"],
                "reload_successful": True
            }
            
        except Exception as e:
            logger.error(f"Failed to switch profile to {profile_name}: {e}")
            raise
    
    async def get_current_profile(self) -> Dict[str, Any]:
        """
        Gibt aktuelles Profil mit vollständigem Status zurück
        
        Returns:
            Dict mit aktuellem Profil, Mappings und Metadaten
        """
        try:
            config = self.load_config()
            
            # Aktuelles Profil ermitteln
            current_profile = config.get('profile_settings', {}).get('current_profile', 'premium')
            
            # Aktuelle model_group_alias Mappings
            active_mappings = config.get('router_settings', {}).get('model_group_alias', {})
            
            # Profile-Metadaten aus Konfiguration
            profile_metadata = config.get('profile_settings', {}).get('available_profiles', {}).get(current_profile, {})
            
            # Switch-History
            switch_history = config.get('profile_settings', {}).get('profile_switch_history', [])
            
            # Validiere Mappings
            expected_mappings = self.profiles.get(current_profile, {})
            mapping_valid = self._validate_mappings(active_mappings, expected_mappings)
            
            return {
                "active_profile": current_profile,
                "active_mappings": active_mappings,
                "expected_mappings": expected_mappings,
                "mapping_valid": mapping_valid,
                "profile_metadata": profile_metadata,
                "switch_history": switch_history[-5:],  # Letzte 5 Switches
                "available_profiles": list(self.profiles.keys()),
                "last_config_update": datetime.fromtimestamp(self.config_path.stat().st_mtime).isoformat() if self.config_path.exists() else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get current profile: {e}")
            raise
    
    async def list_profiles(self) -> List[ProfileMetadata]:
        """
        Listet alle verfügbaren Profile mit Metadaten
        
        Returns:
            Liste aller Profile mit Metadaten
        """
        try:
            config = self.load_config()
            profile_configs = config.get('profile_settings', {}).get('available_profiles', {})
            
            profiles = []
            for profile_name in self.profiles.keys():
                metadata = profile_configs.get(profile_name, {})
                
                profile_meta = ProfileMetadata(
                    name=profile_name,
                    cost_level=metadata.get('cost_level', 'unknown'),
                    performance_level=metadata.get('performance_level', 'unknown'),
                    description=metadata.get('description', f'{profile_name.title()} profile'),
                    model_mappings=self.profiles[profile_name]
                )
                profiles.append(profile_meta)
            
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            raise
    
    async def validate_assignments(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validiert alle Model-Assignments für ein Profil oder alle Profile
        
        Args:
            profile_name: Spezifisches Profil oder None für alle
            
        Returns:
            Validierungs-Ergebnisse
        """
        try:
            config = self.load_config()
            model_list = config.get('model_list', [])
            available_models = {model['model_name'] for model in model_list}
            
            validation_results = {}
            
            # Profile zu validieren
            profiles_to_check = [profile_name] if profile_name else list(self.profiles.keys())
            
            for profile in profiles_to_check:
                if profile not in self.profiles:
                    continue
                
                profile_results = {
                    "profile": profile,
                    "valid_assignments": {},
                    "invalid_assignments": {},
                    "missing_models": [],
                    "total_tasks": len(self.profiles[profile]),
                    "valid_count": 0,
                    "invalid_count": 0
                }
                
                for task, smart_alias in self.profiles[profile].items():
                    if smart_alias in available_models:
                        profile_results["valid_assignments"][task] = smart_alias
                        profile_results["valid_count"] += 1
                    else:
                        profile_results["invalid_assignments"][task] = smart_alias
                        profile_results["missing_models"].append(smart_alias)
                        profile_results["invalid_count"] += 1
                
                # Berechne Validierungs-Score
                if profile_results["total_tasks"] > 0:
                    profile_results["validation_score"] = profile_results["valid_count"] / profile_results["total_tasks"]
                else:
                    profile_results["validation_score"] = 0.0
                
                validation_results[profile] = profile_results
            
            # Gesamt-Summary
            summary = {
                "total_profiles_checked": len(validation_results),
                "fully_valid_profiles": sum(1 for r in validation_results.values() if r["validation_score"] == 1.0),
                "partially_valid_profiles": sum(1 for r in validation_results.values() if 0 < r["validation_score"] < 1.0),
                "invalid_profiles": sum(1 for r in validation_results.values() if r["validation_score"] == 0.0),
                "overall_health": "healthy" if all(r["validation_score"] == 1.0 for r in validation_results.values()) else "issues_detected"
            }
            
            return {
                "validation_results": validation_results,
                "summary": summary,
                "available_models": list(available_models),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate assignments: {e}")
            raise
    
    def _validate_mappings(self, active: Dict[str, str], expected: Dict[str, str]) -> bool:
        """Validiert ob aktive Mappings den erwarteten entsprechen"""
        if not active and not expected:
            return True
        
        return active == expected
    
    async def reload_router(self) -> bool:
        """
        Versucht LiteLLM Router Hot-Reload
        
        Returns:
            True wenn erfolgreich, False wenn nicht möglich
        """
        try:
            # TODO: Implementiere LiteLLM Hot-Reload
            # Dies hängt von der LiteLLM Version und Deployment ab
            # Für jetzt: Logging dass Reload erforderlich ist
            logger.info("LiteLLM Router reload required - config updated")
            
            # In Production würde hier ein API Call oder Signal erfolgen
            # Beispiel: 
            # import requests
            # response = requests.post("http://localhost:4000/admin/reload")
            # return response.status_code == 200
            
            return True
            
        except Exception as e:
            logger.warning(f"Router reload failed: {e}")
            return False
    
    async def get_profile_stats(self, profile_name: str) -> Dict[str, Any]:
        """
        Holt Performance-Statistiken für ein Profil
        
        Args:
            profile_name: Name des Profils
            
        Returns:
            Performance-Statistiken
        """
        try:
            # Placeholder für zukünftige Metrics-Integration
            # TODO: Integration mit LiteLLM Prometheus Metrics
            
            return {
                "profile": profile_name,
                "request_count": 0,
                "average_latency": 0.0,
                "cost_estimate": 0.0,
                "error_rate": 0.0,
                "last_request": None,
                "note": "Statistics integration pending - requires LiteLLM Prometheus setup"
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile stats for {profile_name}: {e}")
            raise

# Singleton Instance für API Endpoints
profile_manager = ProfileManager()

async def get_profile_manager() -> ProfileManager:
    """Factory function für Dependency Injection"""
    return profile_manager 