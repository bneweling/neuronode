#!/usr/bin/env python3
"""
LiteLLM Profile Management API Endpoints
Implementiert API für Profile-basierte Model-Routing
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ...auth.jwt_handler import UserPayload
from ...auth.dependencies import get_admin_user
from ...llm.profile_manager import get_profile_manager, ProfileManager, ProfileMetadata
from ...utils.error_handler import error_handler

logger = logging.getLogger(__name__)

# Request/Response Models
class ProfileSwitchRequest(BaseModel):
    """Request model für Profile-Switching"""
    profile: str = Field(..., description="Name des Ziel-Profils")
    force_reload: bool = Field(False, description="Erzwinge Router-Reload")

class ProfileSwitchResponse(BaseModel):
    """Response model für Profile-Switching"""
    success: bool
    from_profile: str
    to_profile: str
    active_mappings: Dict[str, str]
    switch_timestamp: str
    reload_successful: bool

class ProfileStatusResponse(BaseModel):
    """Response model für Profile-Status"""
    active_profile: str
    active_mappings: Dict[str, str]
    expected_mappings: Dict[str, str]
    mapping_valid: bool
    profile_metadata: Dict[str, Any]
    switch_history: List[Dict[str, Any]]
    available_profiles: List[str]
    last_config_update: Optional[str]

class ProfileValidationResponse(BaseModel):
    """Response model für Profile-Validierung"""
    validation_results: Dict[str, Any]
    summary: Dict[str, Any]
    available_models: List[str]
    validation_timestamp: str

# Router Definition
router = APIRouter(
    prefix="/admin/profiles",
    tags=["Profile Management"],
    dependencies=[Depends(get_admin_user)]
)

# ===================================================================
# PROFILE SWITCHING ENDPOINTS
# ===================================================================

@router.post("/switch", response_model=ProfileSwitchResponse)
async def switch_profile(
    request: ProfileSwitchRequest,
    background_tasks: BackgroundTasks,
    profile_manager: ProfileManager = Depends(get_profile_manager),
    current_user: UserPayload = Depends(get_admin_user)
):
    """
    Wechselt das aktive Model-Profil
    
    Ändert model_group_alias Mappings für alle Tasks auf das gewählte Profil.
    Sofort wirksam ohne Service-Restart.
    """
    try:
        logger.info(f"Profile switch requested by {current_user.user_id}: {request.profile}")
        
        # Profile-Switch durchführen
        result = await profile_manager.switch_profile(request.profile)
        
        # Background Task für Audit Logging
        background_tasks.add_task(
            log_profile_switch,
            user_id=current_user.user_id,
            from_profile=result["from_profile"],
            to_profile=result["to_profile"],
            timestamp=result["switch_timestamp"]
        )
        
        logger.info(f"Profile switched successfully: {result['from_profile']} → {result['to_profile']}")
        
        return ProfileSwitchResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid profile switch request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "switch_profile", "profile": request.profile})
        raise HTTPException(status_code=500, detail=f"Profile switch failed: {str(e)}")

@router.get("/status", response_model=ProfileStatusResponse)
async def get_profile_status(
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Holt den aktuellen Profile-Status mit allen Mappings und Metadaten
    
    Zeigt aktives Profil, model_group_alias Mappings, Switch-History und Validierungsstatus.
    """
    try:
        status = await profile_manager.get_current_profile()
        
        logger.debug(f"Profile status requested - active: {status['active_profile']}")
        
        return ProfileStatusResponse(**status)
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "get_profile_status"})
        raise HTTPException(status_code=500, detail=f"Failed to get profile status: {str(e)}")

@router.get("/list")
async def list_available_profiles(
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Listet alle verfügbaren Profile mit Metadaten
    
    Zeigt alle 5 Profile (premium, balanced, cost_effective, specialized, ultra_fast)
    mit Cost-Level, Performance-Level und Model-Mappings.
    """
    try:
        profiles = await profile_manager.list_profiles()
        
        # Convert ProfileMetadata zu Dict für JSON Response
        profiles_dict = []
        for profile in profiles:
            profiles_dict.append({
                "name": profile.name,
                "cost_level": profile.cost_level,
                "performance_level": profile.performance_level,
                "description": profile.description,
                "model_mappings": profile.model_mappings
            })
        
        logger.debug(f"Profile list requested - {len(profiles_dict)} profiles available")
        
        return {
            "profiles": profiles_dict,
            "total_profiles": len(profiles_dict),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "list_available_profiles"})
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")

# ===================================================================
# PROFILE VALIDATION ENDPOINTS
# ===================================================================

@router.get("/validate", response_model=ProfileValidationResponse)
async def validate_profile_assignments(
    profile: Optional[str] = None,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Validiert Model-Assignments für Profile
    
    Prüft ob alle Smart-Aliases für Profile korrekt konfiguriert sind.
    Kann für spezifisches Profil oder alle Profile durchgeführt werden.
    """
    try:
        logger.info(f"Profile validation requested for: {profile or 'all profiles'}")
        
        validation_result = await profile_manager.validate_assignments(profile)
        
        logger.info(f"Validation completed - Health: {validation_result['summary']['overall_health']}")
        
        return ProfileValidationResponse(**validation_result)
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "validate_profile_assignments", "profile": profile})
        raise HTTPException(status_code=500, detail=f"Profile validation failed: {str(e)}")

@router.post("/validate/assignments")
async def validate_specific_assignments(
    assignments: Dict[str, str],
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Validiert spezifische Task-zu-Model-Assignments
    
    Erlaubt Test von Custom-Assignments bevor sie angewendet werden.
    """
    try:
        logger.info(f"Custom assignment validation requested: {len(assignments)} mappings")
        
        # Lade verfügbare Modelle
        config = profile_manager.load_config()
        model_list = config.get('model_list', [])
        available_models = {model['model_name'] for model in model_list}
        
        validation_results = {}
        for task, smart_alias in assignments.items():
            validation_results[task] = {
                "smart_alias": smart_alias,
                "valid": smart_alias in available_models,
                "available": smart_alias in available_models
            }
        
        total_assignments = len(assignments)
        valid_assignments = sum(1 for r in validation_results.values() if r["valid"])
        
        summary = {
            "total_assignments": total_assignments,
            "valid_assignments": valid_assignments,
            "invalid_assignments": total_assignments - valid_assignments,
            "validation_score": valid_assignments / total_assignments if total_assignments > 0 else 0,
            "overall_status": "valid" if valid_assignments == total_assignments else "invalid"
        }
        
        logger.info(f"Custom validation completed - Score: {summary['validation_score']:.2f}")
        
        return {
            "validation_results": validation_results,
            "summary": summary,
            "available_models": list(available_models),
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "validate_specific_assignments"})
        raise HTTPException(status_code=500, detail=f"Assignment validation failed: {str(e)}")

# ===================================================================
# PROFILE STATISTICS ENDPOINTS
# ===================================================================

@router.get("/stats/{profile_name}")
async def get_profile_statistics(
    profile_name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Holt Performance-Statistiken für ein Profil
    
    Zeigt Request-Count, Latenz, Kosten und Error-Rate für das gewählte Profil.
    """
    try:
        logger.debug(f"Profile statistics requested for: {profile_name}")
        
        stats = await profile_manager.get_profile_stats(profile_name)
        
        return {
            "profile": profile_name,
            "statistics": stats,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "get_profile_statistics", "profile": profile_name})
        raise HTTPException(status_code=500, detail=f"Failed to get profile statistics: {str(e)}")

@router.get("/stats")
async def get_all_profile_statistics(
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Holt Performance-Statistiken für alle Profile
    
    Aggregierte Statistiken für Vergleich zwischen Profilen.
    """
    try:
        logger.debug("All profile statistics requested")
        
        profiles = await profile_manager.list_profiles()
        all_stats = {}
        
        for profile in profiles:
            stats = await profile_manager.get_profile_stats(profile.name)
            all_stats[profile.name] = stats
        
        return {
            "profile_statistics": all_stats,
            "total_profiles": len(all_stats),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "get_all_profile_statistics"})
        raise HTTPException(status_code=500, detail=f"Failed to get profile statistics: {str(e)}")

# ===================================================================
# CONFIGURATION MANAGEMENT ENDPOINTS
# ===================================================================

@router.get("/config")
async def get_profile_configuration(
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Holt die aktuelle Profile-Konfiguration
    
    Zeigt alle model_group_alias Mappings und Profile-Metadaten.
    """
    try:
        config = profile_manager.load_config()
        
        profile_config = {
            "router_settings": config.get("router_settings", {}),
            "profile_settings": config.get("profile_settings", {}),
            "model_count": len(config.get("model_list", [])),
            "last_modified": datetime.fromtimestamp(
                profile_manager.config_path.stat().st_mtime
            ).isoformat() if profile_manager.config_path.exists() else None
        }
        
        return {
            "configuration": profile_config,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "get_profile_configuration"})
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@router.post("/reload")
async def reload_profile_router(
    profile_manager: ProfileManager = Depends(get_profile_manager),
    current_user: UserPayload = Depends(get_admin_user)
):
    """
    Triggert LiteLLM Router Hot-Reload
    
    Lädt die Konfiguration neu ohne Service-Restart.
    """
    try:
        logger.info(f"Router reload triggered by {current_user.user_id}")
        
        reload_success = await profile_manager.reload_router()
        
        return {
            "reload_successful": reload_success,
            "triggered_by": current_user.user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Hot-reload depends on LiteLLM deployment configuration"
        }
        
    except Exception as e:
        error_handler.log_error(e, {"endpoint": "reload_profile_router"})
        raise HTTPException(status_code=500, detail=f"Router reload failed: {str(e)}")

# ===================================================================
# UTILITY FUNCTIONS
# ===================================================================

async def log_profile_switch(user_id: str, from_profile: str, to_profile: str, timestamp: str):
    """Background Task für Profile-Switch Audit Logging"""
    try:
        logger.info(f"AUDIT: Profile switch - User: {user_id}, From: {from_profile}, To: {to_profile}, Time: {timestamp}")
        
        # TODO: In Production hier Audit-Log-System verwenden
        # Beispiel: audit_logger.log_action("profile_switch", user_id, {...})
        
    except Exception as e:
        logger.error(f"Failed to log profile switch audit: {e}")

# Error Handler Integration
# Note: Exception handlers are registered at the app level, not router level
# The get_current_user and error_handler.log_error handle exceptions appropriately 